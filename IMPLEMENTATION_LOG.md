# Implementation Log

Honest, dated record of what's been tried, what works, what doesn't. The single source of truth for "is this skill actually validated yet?"

---

## 2026-04-27 — v0.3.0 shipped (scaffolding) + first connection attempt

### What shipped
- 10-skill plugin under `plugin/skills/` (text-to-blender orchestrator + 8 domain skills + wireframe-to-3d specialty)
- 16-domain knowledge base under `knowledge/`
- Manifest, READMEs, versioning policy
- Tagged `v0.3.0` and pushed to `origin`

### Validation attempt 1 — connection failed

**Goal**: run the 5 representative prompts from `VERSIONING.md` end-to-end against real Blender.

**Result**: never reached step 1. The Blender addon socket is not listening.

**Diagnostic**:
```
ps aux | grep blender
# /Applications/Blender.app/Contents/MacOS/Blender   — running ✓
# .tools/blender-mcp/.venv/bin/blender-mcp           — running ✓

lsof -iTCP:9876 -sTCP:LISTEN
# (empty — nobody listening on 9876)

mcp__blender__get_scene_info
# "Error getting scene info: Could not connect to Blender."
```

**Root cause**: the BlenderMCP addon (`/Users/roble/.tools/blender-mcp/addon.py`) defines a `BLENDERMCP_OT_StartServer` operator at line 2414, exposed as a `"Connect to MCP server"` button in Blender's N-panel (line 2397). The socket only opens when the user clicks that button. There is no auto-start; the addon enable does *not* start the listener.

**User action required**: in Blender, press `N` to open the side panel → find the `BlenderMCP` tab → click `"Connect to MCP server"`. Confirmed listening: re-run `lsof -iTCP:9876 -sTCP:LISTEN` and expect a python process to appear.

**Implication for skill**: the orchestrator's prerequisite check ("Blender MCP is reachable") is correctly designed — it will produce a clear error message if the user hasn't clicked the button. But **no skill code has actually executed against Blender yet**. Estimated bug rate on first execution remains 20–30%.

### Tasks still open for v0.4.0
- [ ] Wait for addon activation
- [ ] Run prompt 1: "Model a cube with bevel + subsurf, apply matte red plastic, render with three-point lighting"
- [ ] Run prompt 2: "Make a glass material on the active object and render"
- [ ] Run prompt 3: "Set up a turntable animation, render 96 frames"
- [ ] Run prompt 4: "Convert this wireframe drawing to a 3D glTF model"
- [ ] Run prompt 5: "Export the current scene as FBX for Unity"
- [ ] Document each failure with: prompt, generated code chunk, error, root cause, fix
- [ ] Patch top failures
- [ ] Re-run; aim for ≥ 4/5 succeeding cleanly
- [ ] Tag v0.4.0 (or v0.5.0 if all 5 pass clean)

---

## Template for future entries

```markdown
## YYYY-MM-DD — vX.Y.Z — <one-line summary>

### What was attempted
<prompts run, code chunks generated>

### What worked
<list>

### What failed
<list with: prompt, code chunk, error, root cause, fix>

### Patches applied
<list of file changes with brief rationale>

### Next steps
<list>
```
