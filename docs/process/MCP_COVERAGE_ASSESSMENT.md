# Is the current Blender MCP enough for this skill's ambition?

**Date**: 2026-04-27  
**Subject**: `ahujasid/blender-mcp` v1.5.5 vs. `wireframe-to-3d` skill requirements

---

## Verdict — short answer

**Yes, it is enough — barely. The MCP gives us exactly the primitive we need (`execute_blender_code`), and that single tool is sufficient because Blender's Python API can do everything else. But there are real friction points worth knowing about before we commit.**

---

## What the MCP provides (verified against the source)

| Tool | What it does | We need it? |
|------|-------------|-------------|
| `execute_blender_code(code)` | Runs arbitrary Python in Blender, returns captured stdout | ✅ **Critical.** Drives ~90% of our pipeline |
| `get_scene_info()` | Returns scene composition (objects, materials, collections) | ✅ Used for validation |
| `get_object_info(name)` | Returns one object's properties (verts, faces, bounds, modifiers) | ✅ Used for symmetry/topology checks |
| `get_viewport_screenshot(max_size)` | PNG of current 3D viewport | ⚠️ Optional preview only |
| Polyhaven / Sketchfab / Hyper3D / Hunyuan3D tools | Asset library + AI generation | ❌ Unused — orthogonal to our task |

**Conclusion**: 4 tools matter to us, 1 is critical.

## What's actually working in our favour

1. **`execute_blender_code` is fully general.** Anything in `bpy.*` is reachable. Curve creation, mesh ops, modifiers, materials, glTF export — all callable from one tool. We don't need a specialized "create curve" or "export glb" MCP tool because we have the language those tools would be built in.

2. **`bpy.data` persists between calls.** Even though each `execute_code` gets a fresh Python namespace, `bpy.data.objects['name']` keeps working across calls. We can build a model incrementally over many small calls instead of one giant call.

3. **180-second timeout per call** is generous. Curve creation, mesh conversion, Decimate, glTF export each take well under 5 seconds on the geometry sizes we target (≤ 30 000 tris).

4. **stdout capture** gives us a clean signaling channel back. We `print(json.dumps(info))` to send structured data back to Claude after each operation.

## What the MCP doesn't give us — and why it doesn't matter

| Wish | Reality | Why it's OK |
|------|---------|-------------|
| Streaming responses for long ops | Single request → single response | Our ops are short; we chunk them anyway |
| Async / parallel execution | Synchronous socket | We orchestrate sequentially, which matches the MCP model |
| File transfer (read PNG, write GLB) | Not directly | Both ends have local FS access; we use absolute paths |
| Live progress updates | Not possible mid-call | We chunk the work; each chunk reports completion via stdout |
| Direct Python object passing | `exec()` with stdout capture only | We marshal to JSON over stdout — works fine for our payload sizes |
| Native curve/mesh primitives | None — we write Python | This is the whole point: Python is the interface |

## Genuine friction points (and how we handle them)

### 1. Fresh namespace each `execute_code` call
**Friction**: Variables defined in call N do not exist in call N+1.  
**Mitigation**: SKILL.md tells Claude to identify objects by `bpy.data.objects['name']` (stable) and re-import modules at the top of every chunk. Names are our state.

### 2. No structured return — only stdout strings
**Friction**: We can't return a Python dict directly; we get a string.  
**Mitigation**: Our code patterns end with `print(json.dumps({...}))`. Claude parses the JSON from the tool result string. Lightweight and reliable.

### 3. 180 s socket timeout is hard
**Friction**: One enormous code dump that runs for 4 minutes will time out and lose all state in that call.  
**Mitigation**: Chunk operations. The MCP tool's own docstring even says "Make sure to do it step-by-step by breaking it into smaller chunks." We follow that.

### 4. No introspection of Blender's internal state mid-call
**Friction**: While code is executing, we can't peek at progress.  
**Mitigation**: Don't run long single calls. Build incrementally; each chunk reports back.

### 5. Errors come back as a single error string
**Friction**: A traceback from deep inside Blender shows up as `"Code execution error: <last line>"`.  
**Mitigation**: Generate small, debuggable chunks so the failing chunk is small enough to read. SKILL.md has an error-recovery table.

### 6. `bpy.ops.export_scene.gltf` requires the glTF addon enabled
**Friction**: Out-of-the-box Blender has it; cut-down installs may not.  
**Mitigation**: SKILL.md's prerequisite check should verify, or fail with a clear message.

### 7. The MCP socket runs in the Blender process — Blender is single-threaded
**Friction**: While our code runs, Blender's UI is frozen.  
**Mitigation**: Acceptable for an automation skill. Users running the skill aren't using Blender's UI at the same time.

## What would make it *better* (but isn't required)

These are nice-to-haves we can live without:

- **`get_python_state(var_name)`** — fetch a Python variable from the addon. Would simplify multi-call workflows. Workaround: print + parse.
- **`run_async_job(code, callback)`** — start a long job, get notified on completion. Workaround: chunking.
- **`apply_modifier_safely(obj, kind, params)`** — would shorten our code patterns. Workaround: emit the bpy calls inline.
- **File upload/download** — would let us send PNGs and receive GLBs through the MCP itself instead of relying on shared local FS. Workaround: absolute paths work because the user runs Claude Code and Blender on the same machine. Caveat: this assumption breaks in a remote setup.

None of these are blockers. They would each save 10–30 lines of generated code.

## What would actually block us — and isn't blocked

For comparison, here's what *would* be insufficient — and how the MCP avoids each:

| Hypothetical limitation | Would block us? | Actual MCP behaviour |
|-------------------------|----------------|---------------------|
| Restricted Python (no `import`, no file I/O) | ✅ Total blocker | **Not restricted** — `exec()` runs full Python |
| Read-only mode (no scene mutation) | ✅ Total blocker | **Read-write** — we can mutate everything |
| No `bpy.ops` access | 🟡 Partial blocker | **Full access** including operators |
| No glTF export operator | ✅ Total blocker | **`bpy.ops.export_scene.gltf` works** |
| No file system access from Blender | ✅ Major blocker | **Full FS access** — we write GLBs to `/tmp` or wherever |
| Timeouts < 30 s | 🟡 Forces architecture changes | **180 s** is comfortable |

We are not blocked by any of these.

## Comparison: alternative approaches

| Approach | Verdict |
|----------|---------|
| Use `ahujasid/blender-mcp` (current) | ✅ **Sufficient.** Single primitive (`execute_blender_code`) covers everything we need |
| Build a custom Blender addon with our own MCP tools | Possible but overkill — would only save us a few lines of generated Python per operation |
| Use a different image-to-3D pipeline (Hyper3D, TripoSR, Meshy) | ❌ Different problem space — those generate from photos/text, not technical drawings; lossy and non-parametric |
| Headless Blender + subprocess | ❌ Loses interactivity, harder error recovery, no live preview, slower roundtrip |

The current MCP is the right substrate.

## Bottom line

The Blender MCP gives us the **minimum viable interface**: a way to evaluate Python in Blender's process and read structured info about the scene. Combined with Blender's own Python API — which is comprehensive — this is enough to build the wireframe-to-3D skill at the level of ambition we've defined (parametric Bezier curves, PBR materials, glTF export, validation, decimation, error recovery).

**We do not need to extend, fork, or replace the MCP.** We do need to design our skill instructions around the MCP's actual behaviour:
- Sync, blocking calls
- Fresh namespace per call (state lives in `bpy.data` and stable names)
- stdout for return data
- Generous but real timeout

All of that is now reflected in `SKILL.md` and the corrected architecture in `VERIFICATION_REPORT.md`.

**Recommendation**: Proceed with implementation. The MCP is enough.

## Sources

- Local: `/Users/roble/.tools/blender-mcp/src/blender_mcp/server.py:116-347` (verified socket protocol & tool list)
- Local: `/Users/roble/.tools/blender-mcp/addon.py:421-436` (verified `execute_code` semantics — `exec()` + stdout capture)
- [ahujasid/blender-mcp on GitHub](https://github.com/ahujasid/blender-mcp)
- [Blender MCP documentation](https://blender-mcp.com/)
- [Blender Python API — bpy.ops.export_scene.gltf](https://docs.blender.org/api/current/bpy.ops.export_scene.html)
- [glTF 2.0 binary format spec](https://github.com/KhronosGroup/glTF/tree/master/specification/2.0)
