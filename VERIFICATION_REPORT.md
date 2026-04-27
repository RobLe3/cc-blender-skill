# Verification Report — Are We On The Right Track?

**Date**: 2026-04-27  
**Reviewer**: Opus 4.7 (deeper analytical pass)  
**Subject**: Wireframe-to-3D Blender Skill — Architecture, scope, and assumptions

---

## TL;DR — Verdict

**Mostly on track, but with three important corrections needed before implementation.**

| Area | Status | Action |
|------|--------|--------|
| Skill domain & scope | ✅ Correct | Continue as planned |
| Algorithmic foundation | ✅ Solid | No changes needed |
| Blender best practices | ✅ Comprehensive | No changes needed |
| **SKILL.md format & structure** | ❌ **Wrong format** | **Rebuild per official spec** |
| **Async/sync MCP assumptions** | ❌ **Incorrect** | **MCP is sync, not async** |
| **Code execution model** | ⚠️ **Misunderstood** | **No state between calls; print() for output** |
| Documentation duplication risk | ✅ No overlap with existing skills | Continue |
| Tool architecture | ✅ Right approach (codegen + execute_blender_code) | Continue |

---

## 1. ✅ What We Got Right

### 1.1 Skill scope is correctly narrow

There's already an excellent **`ra100/blender-claude-plugin`** with 8 generalist Blender skills (geometry-nodes, shader-nodes, modeling-modifiers, etc.). Our wireframe-to-3D skill is **orthogonal and complementary** — they teach Claude *how* to use Blender; we teach Claude one *specific task*. No duplication.

**Recommendation**: Reference ra100's plugin in our README as a complementary install. Users get foundational Blender knowledge from there + specialized wireframe conversion from us.

### 1.2 Code-generation strategy is correct

Both the official Anthropic skill-creator pattern and ra100's plugin use the **same approach**: generate Python code strings → execute via MCP. We're not duplicating MCP capabilities; we're orchestrating them. This is the canonical pattern.

### 1.3 Algorithm choices are well-grounded

- **Canny + RDP + Bezier fitting**: Verified against multiple expert sources, academic papers, and OpenCV documentation. This is the standard pipeline for technical drawing → vector conversion.
- **Best-practice references**: Blender Studio standards, Khronos glTF 2.0 spec, ISO 128 — all current and authoritative.

### 1.4 No reimplementation of MCP capabilities

The skill correctly leverages `execute_blender_code()`, `get_scene_info()`, `get_object_info()` rather than trying to duplicate them.

---

## 2. ❌ Critical Corrections Needed

### 2.1 SKILL.md format does not match official spec

**Problem**: We wrote `WIREFRAME_SKILL.md` as a 700-line specification document, but a real Claude skill needs:

```yaml
---
name: wireframe-to-3d
description: Convert 2D orthographic wireframe PNG drawings to 3D Blender models exported as glTF/GLB. Use this skill whenever the user provides wireframe images of objects (technical drawings, orthographic views, side+front+back panels) and wants to generate a 3D model, mesh, or .glb file. Triggers on phrases like "convert this wireframe to 3D", "make a 3D model from these drawings", "build glasses from this wireframe", or any image-to-3D-mesh request involving line drawings.
allowed-tools: Read Bash mcp__blender__execute_blender_code mcp__blender__get_scene_info mcp__blender__get_object_info mcp__blender__get_viewport_screenshot
---

# Wireframe-to-3D

[concise instructions ≤ 500 lines]

## Step 1: Analyze the wireframe
Run `${CLAUDE_SKILL_DIR}/scripts/wireframe_analyzer.py <image>` ...

## Step 2: Generate Blender code
[reference references/code-patterns.md for templates]

## Step 3: Execute in Blender
[reference references/error-recovery.md for failure modes]
```

**File structure must be**:
```
wireframe-to-3d/                    ← skill root (kebab-case directory)
├── SKILL.md                        ← required entrypoint, ≤500 lines
├── scripts/
│   └── wireframe_analyzer.py       ← bundled, executed not loaded
├── references/                     ← loaded on demand
│   ├── algorithms.md               ← (renamed SKILL_FOUNDATION.md)
│   ├── blender-patterns.md         ← (renamed BLENDER_INTEGRATION_GUIDE.md)
│   └── best-practices.md           ← (renamed BLENDER_BEST_PRACTICES.md)
└── assets/                         ← optional: example wireframes for testing
```

**Why this matters**:
- Claude Code watches `~/.claude/skills/` and `.claude/skills/` directories
- Without proper `SKILL.md` frontmatter, the skill won't be discoverable or invocable
- The 500-line cap matters because SKILL.md content stays in context for the whole session
- Progressive disclosure (references/) means large research docs only load when needed

**Source**: [Anthropic Skills Reference](https://code.claude.com/docs/en/skills), [Anthropic skills repo](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md)

### 2.2 MCP is synchronous, not async

**Problem**: Our `BLENDER_MCP_ALIGNMENT.md` proposed `async/await` pattern:
```python
result = await mcp.execute_code(code)  # WRONG
```

**Reality** (verified by reading `/Users/roble/.tools/blender-mcp/src/blender_mcp/server.py:116-169`):
- Uses **socket.socket** (blocking I/O)
- 180-second timeout per call
- Single request → single response → no streaming
- The MCP tool we call is `mcp__blender__execute_blender_code` — Claude invokes it like any tool

**Correct pattern** (within a Claude skill, not user Python code):
```
[Claude calls mcp__blender__execute_blender_code with code parameter]
[Claude waits for tool result]
[Claude reads result, decides next step]
```

We don't need a `BlenderMCP` wrapper class at all. **Claude itself is the orchestrator** when running the skill — the skill's job is to instruct Claude on what code to generate and what tool calls to make.

This is a **major simplification**. We can delete the planned `src/blender_mcp.py` wrapper.

### 2.3 No state persistence between execute_blender_code calls

**Problem**: We assumed we could spread one workflow across multiple `execute_blender_code` calls and pass Python variables between them.

**Reality** (verified at `addon.py:421-436`):
```python
def execute_code(self, code):
    namespace = {"bpy": bpy}        # ← FRESH NAMESPACE EACH CALL
    capture_buffer = io.StringIO()
    with redirect_stdout(capture_buffer):
        exec(code, namespace)
    return {"executed": True, "result": capture_buffer.getvalue()}
```

**Implications**:
- Python variables defined in call N **DO NOT EXIST** in call N+1
- Only `bpy` is provided; everything else (json, math, mathutils) must be re-imported each call
- **bpy.data persists** (it's the global Blender state) — so we identify objects by `bpy.data.objects['Name']`, not by Python variable
- **Output capture is via stdout** — to inspect results, our code must `print(json.dumps(info))`, then Claude parses the stdout from the tool result

**Correct pattern**:
```python
# Call 1 — create object
import bpy
curve_data = bpy.data.curves.new('GEO-lens-right', 'CURVE')
# ...
print("created:GEO-lens-right")    # ← signal back via stdout

# Call 2 — operate on it
import bpy   # MUST re-import even though it was imported in call 1
obj = bpy.data.objects['GEO-lens-right']   # ← identify by name
# ...
print(f"verts:{len(obj.data.vertices)}")
```

This means our code generators must:
1. Always emit complete, self-contained code blocks
2. Use stable `bpy.data.objects['name']` references, not Python variables
3. Print output as structured strings (JSON in stdout) for Claude to parse

---

## 3. ⚠️ What to Adjust

### 3.1 Lighter implementation than planned

Originally we planned 3 phases, ~3-5 days:
- BlenderMCP wrapper
- Code generators
- Skill orchestrator
- Validation/optimization
- Skill packaging

**With corrected understanding, this collapses to**:
- Phase 1: Restructure docs into proper skill directory (½ day)
- Phase 2: Write SKILL.md as decision logic for Claude (½ day)
- Phase 3: Bundle wireframe_analyzer.py in scripts/ (existing, no work)
- Phase 4: Test end-to-end with actual wireframes (1 day)

**Total: ~2 days** instead of 3-5. The "code generators" and "BlenderMCP wrapper" are not separate Python modules — they're **prose instructions in SKILL.md** that tell Claude what code patterns to emit.

### 3.2 The skill is shorter than we thought

The current `WIREFRAME_SKILL.md` (700 lines) is too long for SKILL.md. The body should be ~200-400 lines: a decision tree, key code patterns inline, and pointers to `references/` for depth.

### 3.3 Description must be "pushy" for triggering

Per the skill-creator best practices, descriptions should counter undertriggering:
- ❌ Bad: "Converts 2D wireframes to 3D"
- ✅ Good: "Convert 2D wireframe PNG drawings to 3D Blender models exported as glTF/GLB. Use this skill whenever the user provides wireframe images and asks for a 3D model — make sure to invoke this even if the user doesn't explicitly say 'wireframe' (also covers 'orthographic views', 'technical drawings', 'side/front/back panels', 'line drawings of objects')."

---

## 4. What Was Validated (No Changes)

| Claim | Verified? | Source |
|-------|-----------|--------|
| Canny edge detection optimal for clean wireframes | ✅ | OpenCV docs, multiple academic papers |
| RDP simplification standard for polyline reduction | ✅ | Implemented in `cv2.approxPolyDP`, well-documented |
| Cubic Bezier fitting via least-squares | ✅ | scipy.linalg.lstsq, standard CV approach |
| Principled BSDF only for glTF export | ✅ | Khronos glTF spec + Blender 5.1 manual |
| Bevel before Subdivision Surface order | ✅ | Multiple Blender tutorials, official docs |
| Quad-dominant topology for deformation | ✅ | Topology guides, animation best practices |
| Blender Studio naming conventions | ✅ | Official Blender Studio site |
| ALIGNED handle types for C¹ continuity | ✅ | Blender curve documentation |
| 15 MB / 8 MB GLB targets | ✅ | TECH-SPEC.md (this project) + glTF best practices |
| Decimate modifier for size reduction | ✅ | Standard Blender workflow |

**All technical foundation in `SKILL_FOUNDATION.md` and `BLENDER_BEST_PRACTICES.md` is correct and remains as the `references/` body.**

---

## 5. The Corrected Architecture

### Old (overengineered)
```
User → Skill Orchestrator (Python) → BlenderMCP wrapper (Python)
                                          → MCP server → Blender
                ↓
        wireframe_analyzer.py
                ↓
        Code generators (Python)
                ↓
        Validators (Python)
```

### New (correct)
```
User → /wireframe-to-3d <image>
        ↓
[SKILL.md content enters Claude's context]
        ↓
Claude reads SKILL.md instructions, decides:
  1. Run wireframe_analyzer.py via Bash → JSON output
  2. Read JSON, generate Blender Python code
  3. Call mcp__blender__execute_blender_code with code
  4. Read tool result (stdout from Blender)
  5. If error: parse, retry with different params, or escalate
  6. If success: call mcp__blender__get_object_info to validate
  7. Generate export code, call mcp__blender__execute_blender_code
  8. Verify file size, apply Decimate if needed
  9. Report result to user
```

**Claude is the orchestrator.** The skill provides:
- Decision logic (when to do what)
- Code patterns (what to emit for each operation)
- Error recovery (what to do when something fails)
- References to deeper documentation when needed

---

## 6. Recommended Next Steps

### Immediately
1. **Restructure repository** to match Claude Skill spec:
   ```
   cc-blender-skill/
   ├── README.md (existing, keep)
   ├── DEVELOPMENT.md (existing, update)
   ├── VERIFICATION_REPORT.md (this file)
   └── skill/
       └── wireframe-to-3d/
           ├── SKILL.md           ← NEW, the actual skill
           ├── scripts/
           │   └── wireframe_analyzer.py
           ├── references/
           │   ├── algorithms.md
           │   ├── blender-patterns.md
           │   └── best-practices.md
           └── assets/
               └── (test wireframes)
   ```

2. **Write the actual SKILL.md** (≤500 lines) with:
   - Frontmatter: name, description (pushy), allowed-tools
   - Decision tree for view-type, detail-level, geometry-type
   - Inline code patterns for the most common operations
   - Pointers to references/*.md for edge cases
   - Pointers to scripts/wireframe_analyzer.py for invocation

3. **Move existing docs** into `references/`:
   - `SKILL_FOUNDATION.md` → `references/algorithms.md`
   - `BLENDER_INTEGRATION_GUIDE.md` → `references/blender-patterns.md`
   - `BLENDER_BEST_PRACTICES.md` → `references/best-practices.md`
   - `BLENDER_MCP_ALIGNMENT.md` → archive (no longer needed; we're not building Python wrappers)
   - Old `WIREFRAME_SKILL.md` → archive (replaced by `SKILL.md`)

4. **Test in Claude Code**:
   - Symlink `skill/wireframe-to-3d/` to `~/.claude/skills/wireframe-to-3d/`
   - Run `/wireframe-to-3d` and check it triggers
   - Try with the existing aviator glasses wireframes

### Drop from scope
- `BlenderMCP` Python wrapper class (Claude calls MCP tools directly)
- `code_generators.py` Python module (code patterns are prose in SKILL.md)
- Async/await orchestration (MCP is sync; Claude orchestrates)
- Custom error-handling Python module (instructions in SKILL.md)

### Keep
- `wireframe_analyzer.py` (the only actual Python we need — bundled in `scripts/`)
- All research documentation (moved to `references/`)
- README.md, DEVELOPMENT.md, requirements.txt

---

## 7. Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| 180s timeout on large code blocks | Medium | Chunk operations into smaller execute_blender_code calls |
| State doesn't persist between calls | Certain | Use `bpy.data.objects['name']` patterns, not variables |
| Blender 5.x API drift from earlier examples | Low | Materials API stable; we use Principled BSDF only |
| User's Blender MCP not running | High at start | SKILL.md must check `mcp__blender__get_scene_info` first; if it fails, instruct user to start Blender + addon |
| Wireframe analyzer fails on edge cases | Medium | Documented fallbacks (adaptive thresholding, manual params) |
| Description doesn't trigger reliably | Medium | Use "pushy" description style; include trigger eval scenarios |

---

## 8. Bottom Line

**You're 90% there. The research is solid, the architecture choice is correct, and the algorithms are right.** The 10% is structural: package this as a real Claude Skill instead of a Python application.

The shift is from "build an automated pipeline that calls Blender" to "give Claude a runbook + a tool + reference material so it can do it itself." That's a much smaller surface area to maintain and exactly the pattern Anthropic intends for skills.

**Estimated implementation time after these corrections**: 1-2 days, not 3-5.

---

## Sources

- [Anthropic Claude Code Skills documentation](https://code.claude.com/docs/en/skills)
- [Anthropic skills repository (skill-creator example)](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md)
- [SKILL.md Format Reference](https://www.agensi.io/learn/skill-md-format-reference)
- [Claude Agent Skills First-Principles Deep Dive](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/)
- [ra100/blender-claude-plugin (existing complementary skill set)](https://github.com/ra100/blender-claude-plugin)
- [ahujasid/blender-mcp (the MCP server we depend on)](https://github.com/ahujasid/blender-mcp)
- [Blender 5.0 Python API Release Notes](https://developer.blender.org/docs/release_notes/5.0/python_api/)
- Local source: `/Users/roble/.tools/blender-mcp/src/blender_mcp/server.py:116-347` (verified MCP behavior)
- Local source: `/Users/roble/.tools/blender-mcp/addon.py:421-436` (verified execute_code semantics)
