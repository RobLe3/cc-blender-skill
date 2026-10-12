"""Start both real add-on bridges in a disposable interactive Blender instance.

Requires CC_MCP_INSTANCE_OUT, CC_LEGACY_ADDON, CC_OFFICIAL_ADDON, and optional
CC_MCP_PURE_PYTHON_SITE (requests dependencies). Does not save user preferences.
"""
import bpy
import importlib.util
import json
import os
from pathlib import Path
import socket
import sys

out = Path(os.environ['CC_MCP_INSTANCE_OUT'])
out.mkdir(parents=True, exist_ok=True)
if os.environ.get('CC_MCP_PURE_PYTHON_SITE'):
    sys.path.append(os.environ['CC_MCP_PURE_PYTHON_SITE'])

def load(name, path, package=False):
    path = Path(path)
    spec = importlib.util.spec_from_file_location(name, str(path),
        submodule_search_locations=[str(path.parent)] if package else None)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

def port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]

legacy = load('qa_legacy_addon', os.environ['CC_LEGACY_ADDON'])
legacy.register()
legacy_port = port()
legacy_server = legacy.BlenderMCPServer(host='127.0.0.1', port=legacy_port)
legacy_server.start()
official = load('qa_official_addon', Path(os.environ['CC_OFFICIAL_ADDON']) / '__init__.py', True)
official_port = port()
official.mcp_to_blender_server.start('127.0.0.1', official_port)
bpy.app.timers.register(official.mcp_to_blender_server.poll)
(out / 'instance.json').write_text(json.dumps({'pid': os.getpid(), 'legacy_port': legacy_port,
                                              'official_port': official_port, 'blender': bpy.app.version_string}))
print('QA_MCP_INSTANCE_READY', flush=True)
