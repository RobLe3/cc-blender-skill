# Blender MCP backends

Read this before the first Blender operation, including direct leaf-skill invocations.
For host-native tools, installation, and permissions read [agent-hosts.md](agent-hosts.md).
The recipes use the original `mcp__blender__…` spelling as examples. Resolve their
logical operations through the selected backend; do not call a legacy tool on an
official server just because a recipe names it.

## Select once per task

1. Honor an explicit backend choice. If unavailable or missing a required capability,
   explain the limitation before changing the scene; do not override that choice.
2. Otherwise, if a requested download/generation operation is advertised only by
   ahujasid, select ahujasid for the whole task. Check provider availability before
   starting; advertised tools do not guarantee provider access.
3. For shared capabilities, prefer official MCP when available; otherwise use ahujasid.

Inspect the client's available tool names, then perform a read-only scene query.
Confirm that this is the user's intended scene, particularly if the servers point
to different Blender instances. If the preferred backend is unreachable, stop and
explain how to start it; do not silently switch scenes. When only one backend is
configured, use it. Never switch backends or replay a mutation after a timeout:
inspect the selected scene first because the operation may already have completed.

Keep the selected server, backend, scene, Blender version, and relevant capabilities
in the task's working notes. Leaf skills inherit that selection. Selecting a new
backend is a new task/preflight, not a hidden recovery step.

## Tool and argument mapping

| Operation | ahujasid (`blender`) | Official (`blender` or `blender_official`) |
|---|---|---|
| Execute Python | `execute_blender_code(code=...)` | `execute_blender_code(code=...)` |
| Inspect scene | `get_scene_info()` | `get_objects_summary()` |
| Inspect object | `get_object_info(object_name=...)` | `get_object_detail_summary(name=...)` |
| GUI screenshot | `get_viewport_screenshot(max_size=800)` | `get_screenshot_of_area_as_image(area_ui_type="VIEW_3D")` |
| Final render | Execute `bpy.ops.render.render(write_still=True)` with explicit scene filepath | `render_viewport_to_path(output_path=...)`, or the same Python render |
| API documentation | Consult Blender documentation | `search_api_docs(query=...)` |
| Provider assets | Advertised Poly Haven, Sketchfab, Hyper3D/Hunyuan tools, subject to provider setup | Not built in; download/import manually if legacy is unavailable |

Some clients expose tool names as `mcp__<server>__<tool>`; resolve the advertised
name and schema rather than requiring this spelling in every host. A single-backend installation
uses `blender`. A dual installation keeps the existing ahujasid server as `blender`
and adds official MCP as `blender_official`. Do not rename an existing server or
change the user's configuration without authorization. These two server names are
covered by the optional Claude `allowed-tools` entries. Other hosts use their own
tool inventory and permissions; changing a server alias does not change its MCP API.
For Claude-specific alternative aliases, update that optional metadata explicitly.

The official object summary includes dimensions but not mesh vertex/face counts.
Its scene summary is a nested collection tree, not the legacy flat scene response.
For geometry validation, execute Python against stable `bpy.data` names on either
backend; use evaluated meshes when modifiers affect the expected result.

## Results and errors

Both execution tools start a fresh Python namespace; `bpy.data` persists.
Re-import modules in each chunk. Existing print-based recipes work on both backends.
On official MCP, also set `result = {"ok": True, ...}` for structured data.

- ahujasid execution returns text, including captured prints. Treat `Error executing
  code:` and other error text as failures, even when the MCP call itself succeeded.
- Official tools return an envelope with `status`, `result`, and optional `stdout`.
  Check the outer status and any inner `result.status`; `isError=false` alone does
  not establish success. Python exceptions can be returned as an error envelope.
- Verify the resulting scene/file independently before reporting success. Preserve
  the original error, and do not suppress it with broad try/except fallbacks.
- Use small chunks. The legacy socket timeout is 180 seconds; official client/socket
  timeouts differ. A render still running is not permission to submit it again.

## Visual validation

Prefer a final render over a screenshot when judging materials and lighting.
For official `render_viewport_to_path`, the requested basename is placed in Blender's
MCP scratch directory. Read **the returned `result.filepath`**, not the requested
absolute path. Never inspect a stale file left at the requested location. If the
user requires an exact destination, render through Python with that filepath or
copy the returned file after verifying completion. A remote Blender path must be
transferred before a local file reader can inspect it.

Screenshots require an interactive Blender window. In background mode use a render;
do not interpret unavailable GUI capture as a successful visual check. If no camera
exists, follow `blender-cameras` rather than deleting or rebuilding existing objects.

## Installation and coexistence

- **ahujasid:** preserve the current Blender ≥4.0 setup and its existing compatibility
  caveats. Install its MCP client process and add-on; start the socket (default 9876).
- **Official:** requires Blender ≥5.1. Add `https://lab.blender.org/` as an extension
  repository, install/enable MCP, and start its socket server in add-on preferences.
  Install the separate official MCP server using the bundle or the upstream setup
  instructions. Enabling the add-on alone does not register tools in the agent host.
- Both upstream packages use the executable name `blender-mcp`. Keep them in separate
  environments or use the official bundle; specify the appropriate absolute
  executable in the client's MCP configuration. Do not overwrite the legacy package.
- For dual setup, leave legacy at port 9876 (`BLENDER_HOST` / `BLENDER_PORT`) and set
  the official add-on to 9877 with matching client-process environment
  `BLENDER_MCP_HOST=127.0.0.1`, `BLENDER_MCP_PORT=9877`. The protocols are different;
  two add-ons cannot share a listening port. Use distinct client server names above.

Authoritative setup: [Blender Lab](https://www.blender.org/lab/mcp-server/),
[official source/setup](https://projects.blender.org/lab/blender_mcp), and
[ahujasid](https://github.com/ahujasid/blender-mcp).
The official MCP can execute arbitrary Python; run it only in a trusted environment.

## Blender 5.x notes

PR #1 supplied useful live observations: EEVEE uses `BLENDER_EEVEE` in 5.x;
the compositor uses `scene.compositing_node_group`; Glare options are input sockets;
actions use layered F-curves; video output needs `media_type='VIDEO'` before FFMPEG.
Keep the existing compatibility helpers rather than replacing older-version paths.
See `blender-version-compat.md` and use API search for the installed version.
If a bmesh edit appears stale, update the mesh and depsgraph first. Copying/swapping
mesh data is a last resort; never remove a mesh still used by other objects.
