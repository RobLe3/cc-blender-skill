# Testing Plan — Haiku-Driven Validation

**Purpose**: Token-efficient test execution. Haiku runs the deterministic loop (execute → observe → log); Opus reads `test.md` later and patches what's broken.

**Target tester**: Haiku 4.5 (or any cheap model) with `mcp__blender__execute_blender_code` access.

---

## Roles

| Role | Model | Job |
|------|-------|-----|
| **Tester** | Haiku 4.5 | Run the test cases. Log results in `test.md`. **Do not attempt fixes.** |
| **Patcher** | Opus 4.7 | Read `test.md`. Decide which failures need code changes. Write the patches. |

This separation matters: testers shouldn't second-guess. Just record what happened.

---

## Pre-test checklist

Before starting, the tester confirms:

- [ ] Blender app running
- [ ] BlenderMCP addon socket listening on :9876 (run `lsof -iTCP:9876 -sTCP:LISTEN`)
- [ ] `mcp__blender__get_scene_info` returns valid JSON (not "Could not connect")
- [ ] `python3 -c "import cv2, numpy, scipy"` succeeds (only needed for wireframe-to-3d tests)
- [ ] Working directory contains the cc-blender-skill repo (so `wireframe_analyzer.py` and the skill files are reachable)

If any check fails, **stop**. Update `test.md`'s "Environment" section with what's missing and exit.

---

## Test cases — execute in order

Each test: read the relevant SKILL.md recipe, generate the Python, call `mcp__blender__execute_blender_code`, capture the result. Log per the `test.md` schema.

### Group A — `blender-modeling` (5 tests)

| ID | Prompt to Claude | Expected |
|----|-----------------|----------|
| A1 | Add a cube primitive named `GEO-A1_cube` at origin | Object exists in scene with correct name |
| A2 | Add a cube and apply Bevel + SubSurf in correct order, name `GEO-A2_hardsurface` | Object has 2 modifiers, BEVEL listed before SUBSURF |
| A3 | Boolean-cut a cylinder hole through a cube, name result `GEO-A3_drilled` | Final object exists; vertex count differs from a plain cube |
| A4 | Apply Mirror modifier to half-mesh `GEO-A4_half` | Mirror modifier present; bounding-box symmetric across X |
| A5 | Convert a Bezier curve to mesh and apply remove-doubles | Object type is now MESH; vertex count > 0 |

### Group B — `blender-materials` (5 tests)

| ID | Prompt | Expected |
|----|--------|----------|
| B1 | Create `MAT-B1_steel`, brushed steel preset, assign to `GEO-A1_cube` | Material exists; metallic=1.0; assigned to object |
| B2 | Create `MAT-B2_glass`, clear glass with transmission, assign to `GEO-A2_hardsurface` | Material exists; transmission_weight=1.0; IOR=1.5 |
| B3 | Create `MAT-B3_skin`, skin with subsurface scattering, assign to a sphere | Subsurface_weight=1.0; subsurface_radius reasonable for skin |
| B4 | Create `MAT-B4_velvet`, fabric with sheen, assign to a cube | Sheen_weight > 0; roughness ≥ 0.6 |
| B5 | Create `MAT-B5_wood_procedural` using Wave + Noise + ColorRamp + Principled BSDF | Material has all 4 nodes wired into Base Color |

### Group C — `blender-lighting` (3 tests)

| ID | Prompt | Expected |
|----|--------|----------|
| C1 | Set up three-point lighting: `LGT-C1_key`, `LGT-C1_fill`, `LGT-C1_rim` | All 3 light objects exist; energies in 4:1:2 ratio |
| C2 | Configure HDRI world environment from a path | World node tree contains Environment Texture node |
| C3 | Add a Sun light for outdoor sunlit scene | Sun light exists; energy 3-10 range |

### Group D — `blender-cameras` (3 tests)

| ID | Prompt | Expected |
|----|--------|----------|
| D1 | Add camera `CAM-D1_hero` at 85mm with shallow DoF (f/2.8) | Camera exists; lens=85; dof.use_dof=True; aperture_fstop≈2.8 |
| D2 | Add wide establishing camera `CAM-D2_wide` at 24mm | Camera exists; lens=24 |
| D3 | Set up orbit camera with empty as pivot, 360° over 240 frames | Pivot empty + camera; 2 keyframes on pivot rotation_euler[2] |

### Group E — `blender-rendering` (3 tests)

| ID | Prompt | Expected |
|----|--------|----------|
| E1 | Configure Cycles 256 samples + OIDN denoise | engine='CYCLES'; samples=256; use_denoising=True |
| E2 | Configure EEVEE preset | engine resolves to a valid EEVEE variant for this Blender version |
| E3 | Render single frame to `/tmp/test-E3.png`, 640x360 | File exists at path; size > 1 KB |

### Group F — `blender-animation` (3 tests)

| ID | Prompt | Expected |
|----|--------|----------|
| F1 | Animate `GEO-A1_cube` location (0,0,0) → (5,0,0) over frames 1-60 | 2 keyframes set on location.x; using compat helper if Blender 5.x |
| F2 | Animate 360° Z-rotation across 240 frames with linear interpolation | 3+ keyframes on rotation_euler.z; all interpolation == LINEAR |
| F3 | Add a shape key `Smile` to a mesh, animate value 0→1 over 24 frames | Shape key exists; 2 keyframes on its value |

### Group G — `blender-export` (4 tests)

| ID | Prompt | Expected |
|----|--------|----------|
| G1 | Export current scene as `/tmp/test-G1.glb` | File exists; size > 1 KB; `file` command identifies as glTF |
| G2 | Export current scene as `/tmp/test-G2.fbx` for Unity (Y-up, -Z forward) | File exists; size > 1 KB; `file` identifies as Kaydara FBX |
| G3 | Export current scene as `/tmp/test-G3.obj` | File exists; OBJ + MTL written |
| G4 | Apply Decimate (ratio 0.7) before re-exporting glTF | Pre-decimate verts > post-decimate verts on at least one object |

### Group H — `wireframe-to-3d` (1 test, conditional)

Only attempt if `python3 -c "import cv2"` succeeded in pre-check.

| ID | Prompt | Expected |
|----|--------|----------|
| H1 | Run `wireframe_analyzer.py` on a sample wireframe PNG; convert output JSON to a Blender curve | Curve object created; vertex count > 0 |

If no sample wireframe is available, mark H1 as `SKIPPED — no input image`.

### Group I — `text-to-blender` orchestrator (2 end-to-end tests)

These exercise the orchestrator's chaining ability — multiple sub-skills in sequence.

| ID | Prompt | Expected |
|----|--------|----------|
| I1 | "Model a cube, give it brushed steel, light it three-point, render to `/tmp/test-I1.png`" | Object + material + 3 lights + render file all present |
| I2 | "Animate the cube spinning 360° over 96 frames and export the scene as glTF" | Keyframes + GLB file present |

---

## test.md schema (output format)

Tester writes results into `test.md` at repo root. Use exactly this schema so Opus can parse it:

```markdown
# Test Results — vX.Y.Z

**Run date**: YYYY-MM-DD
**Environment**:
- Blender version: <e.g. 5.1.1>
- OS: <e.g. macOS 14.5>
- ahujasid/blender-mcp version: <e.g. 1.5.5>
- Python deps for wireframe-to-3d: <available | missing>

**Score**: P/F/S out of N (Pass / Fail / Skipped)

---

## Test results

### A1
- **Skill**: blender-modeling
- **Status**: PASS | FAIL | SKIP
- **Prompt**: <verbatim prompt sent>
- **Code chunks executed**: <count>
- **Result text**: <full text returned by mcp__blender__execute_blender_code>
- **Evidence**:
  - object_name: <name>
  - vert_count: <number>
  - file_path: <if applicable>
- **If FAIL — error**: <verbatim error message>
- **If FAIL — likely root cause**: <one short line; do NOT propose fix>
- **If SKIP — reason**: <why>

### A2
... (same structure)
```

**Notes for the tester**:
- One block per test case; no block omitted (use SKIP if not run).
- Do not edit recipes mid-run. Even if a recipe looks wrong, run it as-is and log FAIL.
- Do not chase fixes during the run. The patcher (Opus) will handle that.
- "Evidence" should be objective (counts, paths, attribute values), not subjective ("looks right").
- "Likely root cause" is a hypothesis, not a fix. Keep it to one line.

---

## Patcher protocol (for Opus, after Haiku finishes)

When Opus picks up `test.md`:

1. Read all FAIL entries in order.
2. Group them by skill file affected.
3. For each group, read the current SKILL.md, identify the specific recipe, write the patch.
4. Re-run the failed test cases via the same `mcp__blender__execute_blender_code` (verify the patch works).
5. Append a `## Patches applied` section to `test.md` listing changes.
6. Commit + tag the next version.

---

## Stopping conditions

Tester should stop and ask before continuing if:

- Same error appears 3+ times in a row across different tests (likely environmental, not a recipe bug)
- An MCP call times out (180 s default)
- Blender crashes or addon disconnects
- More than 50% of tests in a single group FAIL (suggests group-wide issue worth investigating before continuing)

---

## Estimated cost (approximate)

- ~30 tests × ~3 MCP calls each = ~90 MCP calls
- Each call ≈ small Python chunk (50-200 tokens generated, similar received)
- Haiku token cost: should run for under $0.50 total
- Opus patch session afterwards: typically 5-10 minutes of work, much higher per-token cost but only on the failures

This split is roughly **10× cheaper** than running the same loop on Sonnet/Opus throughout.
