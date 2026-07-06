# Official Blender MCP Add-on — Adapter Notes

This plugin was originally written against `ahujasid/blender-mcp` (community
socket addon on port 9876). This install has been adapted for the **official
Blender MCP add-on** (Blender extensions platform, `lab_blender_org/mcp`,
Blender ≥ 4.5/5.x). Read this when a tool name or return value doesn't behave
as a skill describes.

## Tool mapping (what the skills now reference)

| Old (ahujasid) | Official add-on | Notes |
|---|---|---|
| `execute_blender_code(code)` | `execute_blender_code(code)` | Same name. Official version: assign a JSON-serialisable dict to a variable named `result` to return structured data. `print()` stdout is also captured (returned in a `stdout` field), but `result` is more reliable than parsing prints. |
| `get_scene_info` | `get_objects_summary` | Returns collection hierarchy + objects (name, type, parent, visibility, selection). No parameters. |
| `get_object_info(name)` | `get_object_detail_summary(name)` | Transforms, parent/children, modifiers, constraints, materials, collections. For bounding boxes / vertex counts, use `execute_blender_code` instead. |
| `get_viewport_screenshot` | `get_screenshot_of_area_as_image(area_ui_type="VIEW_3D")` | Requires the area type argument. Returns PNG image content directly. |
| — (no equivalent) | `render_viewport_to_path(output_path)` | Full render with current settings, saved to disk. **Prefer this for visual validation of final quality** (lighting/materials render correctly; viewport screenshots show viewport shading only). Read the saved file afterwards to inspect it. |
| — | `render_thumbnail_to_path` | Quick small render. |
| — | `search_api_docs(query)` / `search_manual_docs(query)` / `get_python_api_docs(path)` | Bundled Blender API + manual search. Use when unsure about an operator signature instead of guessing. |
| — | `get_blendfile_summary_datablocks` etc. | Datablock statistics, linked libraries, missing files. |
| `download_polyhaven_asset` | **not available** | Download from polyhaven.com manually (curl/browser), then import via `bpy.ops.wm.obj_import` / glTF import. |
| `download_sketchfab_model` | **not available** | Same — manual download + import. |
| `generate_hyper3d_model_via_text` | **not available** | Use a web text-to-3D service, import the GLB. |

Tool name prefixes depend on the client: Claude Code exposes them as
`mcp__<server>__<tool>` (e.g. `mcp__blender__get_objects_summary` if the server
is registered as `blender`); Cursor exposes them via its MCP tool call with
server + tool name. The skills use the `mcp__blender__…` spelling — map to your
client's convention.

## Returning data from `execute_blender_code`

Preferred pattern (official add-on):

```python
import bpy
# ... do work ...
result = {"objects": [o.name for o in bpy.data.objects], "ok": True}
```

The dict in `result` comes back as structured JSON. Exceptions come back as
tracebacks in an error status — no need to wrap everything in try/except.

## Visual validation loop (adapted)

1. `render_viewport_to_path("/tmp/check.png")` — real render, honest materials.
2. Read `/tmp/check.png` and inspect.
3. For quick orientation checks (is the object roughly there?), the cheaper
   `get_screenshot_of_area_as_image(area_ui_type="VIEW_3D")` is fine.

## Blender 5.x API gotchas (verified live on 5.1)

- `scene.render.engine` is `'BLENDER_EEVEE'` again (not `BLENDER_EEVEE_NEXT`).
- Compositor: `scene.node_tree` is gone → create a node group
  (`bpy.data.node_groups.new(name, 'CompositorNodeTree')`), assign to
  `scene.compositing_node_group`, add `NodeGroupOutput` + an OUTPUT interface
  socket. Glare node options are now **input sockets**
  (`glare.inputs['Type'].default_value = 'Bloom'`).
- Actions are layered: iterate F-curves via
  `action.layers[].strips[].channelbags[].fcurves`, not `action.fcurves`.
- Video export: set `image_settings.media_type = 'VIDEO'` **before**
  `file_format = 'FFMPEG'`.
- In-place bmesh edits sometimes leave the depsgraph stale (render shows old
  geometry). Reliable fix: swap the datablock —
  `new = me.copy(); obj.data = new; bpy.data.meshes.remove(me)`.
- More details: `references/blender-version-compat.md`.
