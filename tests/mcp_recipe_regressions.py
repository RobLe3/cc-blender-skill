"""Real MCP integration checks against the disposable tests/mcp_test_instance.py.

Run in a Python environment containing the MCP SDK. Supply independent legacy and
official server executables; no user MCP configuration is changed.
"""
import argparse
import asyncio
import base64
import json
import os
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def exercise(args, backend, label, source):
    instance = json.loads((args.instance / 'instance.json').read_text())
    out = args.out / label
    out.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, HOME=str(args.out / 'client-home'),
               XDG_DATA_HOME=str(args.out / 'client-data'), BLENDER_MCP_DISABLE_TELEMETRY='true')
    env['BLENDER_HOST' if backend == 'legacy' else 'BLENDER_MCP_HOST'] = '127.0.0.1'
    env['BLENDER_PORT' if backend == 'legacy' else 'BLENDER_MCP_PORT'] = str(instance[backend + '_port'])
    python = args.legacy_python if backend == 'legacy' else args.official_python
    command = ['-m', 'blender_mcp.server'] if backend == 'legacy' else ['-m', 'blmcp']
    rows = []
    async with stdio_client(StdioServerParameters(command=str(python), args=command, env=env)) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = {t.name: t.inputSchema for t in (await session.list_tools()).tools}
            required = ['execute_blender_code', 'get_scene_info', 'get_object_info', 'get_viewport_screenshot'] if backend == 'legacy' else [
                'execute_blender_code','get_objects_summary','get_object_detail_summary','get_screenshot_of_area_as_image','render_viewport_to_path','search_api_docs']
            if set(required)-tools.keys():
                raise AssertionError('Missing tools: '+repr(set(required)-tools.keys()))
            async def call(name, params):
                result = await asyncio.wait_for(session.call_tool(name, params), timeout=180)
                value = result.model_dump(mode='json', exclude_none=True)
                if value.get('isError'):
                    raise AssertionError(value)
                structured = value.get('structuredContent')
                if structured and (structured.get('status')=='error' or
                                   isinstance(structured.get('result'),dict) and structured['result'].get('status')=='error'):
                    raise AssertionError(structured)
                if not structured:
                    text = '\n'.join(c.get('text','') for c in value.get('content',[]))
                    if 'Error executing code:' in text or 'Error getting' in text:
                        raise AssertionError(text)
                rows.append({'tool':name,'arguments':params if name!='execute_blender_code' else {'code':'[recipe test code; see scripts]'},'response':value})
                return value
            await call('get_scene_info' if backend=='legacy' else 'get_objects_summary', {})
            await call('execute_blender_code', {'code':"import bpy\nresult={'objects':len(bpy.data.objects)}\nprint('QA_STDOUT_OK')"})
            # Genuine GUI screenshots, not headless mocks.
            image_result = await call('get_viewport_screenshot' if backend=='legacy' else 'get_screenshot_of_area_as_image',
                                     {} if backend=='legacy' else {'area_ui_type':'VIEW_3D'})
            images = [c for c in image_result['content'] if c['type']=='image']
            if not images:
                raise AssertionError('No screenshot image returned')
            (out/'screenshot.png').write_bytes(base64.b64decode(images[0]['data']))
            code = 'import runpy,json\nm=runpy.run_path('+repr(str(args.repo/'tests/core_recipe_regressions.py'))+')\nr=m["run_suite"]('+repr(str(source))+','+repr(str(out))+')\nprint("QA_CORE_TESTS:"+json.dumps({"tests":len(r["tests"])}))\nresult={"tests":len(r["tests"])}'
            await call('execute_blender_code', {'code':code})
            await call('get_object_info' if backend=='legacy' else 'get_object_detail_summary',
                       {'object_name':'GEO-head'} if backend=='legacy' else {'name':'GEO-head'})
            if backend == 'official':
                search = await call('search_api_docs', {'query':'use_multires','max_results':2})
                if not search['structuredContent']['hits']:
                    raise AssertionError('Documentation search did not return hits')
                requested = out/'requested-render.png'
                response = await call('render_viewport_to_path', {'output_path':str(requested)})
                returned = Path(response['structuredContent']['result']['filepath'])
                if not returned.is_file() or requested.exists():
                    raise AssertionError('Unexpected render scratch-path contract')
                (out/'returned-render.png').write_bytes(returned.read_bytes())
            # Deliberate Python failure: MCP transport success is not execution success.
            result = await session.call_tool('execute_blender_code', {'code':"raise ValueError('QA_expected_failure')"})
            value = result.model_dump(mode='json',exclude_none=True)
            serialized=json.dumps(value)
            if 'QA_expected_failure' not in serialized or not ('error' in serialized.lower()):
                raise AssertionError('Missing execution error evidence')
            rows.append({'tool':'execute_blender_code','expected_failure':True,'response':value})
    (out/'mcp-tests.json').write_text(json.dumps({'backend':backend,'label':label,'tools':tools,'calls':rows,'passed':True},indent=2))


async def main(args):
    args.out.mkdir(parents=True,exist_ok=True)
    await exercise(args,'legacy','legacy-baseline',args.baseline)
    await exercise(args,'legacy','legacy-candidate',args.repo)
    await exercise(args,'official','official-candidate',args.repo)
    await exercise(args,'legacy','legacy-baseline-repeat',args.baseline)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['instance','out','repo','baseline','legacy-python','official-python']:
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    asyncio.run(main(args))
