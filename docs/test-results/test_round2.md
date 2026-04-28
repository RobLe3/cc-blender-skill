# Test Results — Round 2 (v0.5.0 → next)

**Run date**: 2026-04-27
**Tester**: Haiku 4.5 (claude-haiku-4-5-20251001)
**Environment**: Blender 5.1.1, ahujasid/blender-mcp v1.5.5, addon connected on :9876
**Goal**: extend coverage beyond the 30 unit-style tests in `test.md` AND validate on a real complete scene-build.

**Round 2 plan executed**:
- 3 extended material recipes (J: gold, chrome, lacquer with Coat) ✓
- 3 extended modeling tests (K: sweep along path with bevel_object, surface revolution via Screw, mirror with offset half-mesh) ✓
- 1 extended lighting recipe (L1: sunny outdoor sun) ✓
- 1 full sword scene build (M: 4 mesh parts, 3 materials, 3-point lighting, Cycles render) ✓ with caveats
- Bottle scene (N) and animation extras (O) deferred to next round to keep this round focused

**Score**: **6 PASS / 1 PARTIAL / 1 PASS-with-subjective-issues out of 8**

| Group | Test | Result |
|-------|------|--------|
| J1 | Polished gold | PASS |
| J2 | Mirror chrome | PASS |
| J3 | Lacquered plastic with Coat layer | PASS |
| K1 | Sweep along path (`bevel_object`) | **PARTIAL** — 0 faces; needs profile.dimensions='2D' |
| K1b | Sweep along path (`bevel_depth`, alternative) | PASS |
| K2 | Surface revolution (Screw modifier) | PASS |
| K3 | Mirror with offset half-mesh | PASS — addresses round-1 A4 caveat |
| L1 | Sunny outdoor (Sun light) | PASS |
| M | **Real sword scene build + render** | **PASS technically / FAIL subjectively** — see findings |

---

## Test results

### J1
- **Skill**: blender-materials
- **Status**: PASS
- **Prompt**: Apply Recipe 2 (Polished gold) to a cube
- **Code chunks executed**: 1 (combined with J2, J3)
- **Result text**: `GEO-J1_gold: assigned=True metallic=1.0 roughness=0.05 coat=0.0`
- **Evidence**: F0 base color (1.022, 0.782, 0.344) set; metallic=1.0; roughness=0.05

### J2
- **Skill**: blender-materials
- **Status**: PASS
- **Prompt**: Apply Recipe 4 (Mirror chrome) to a cube
- **Result text**: `GEO-J2_chrome: assigned=True metallic=1.0 roughness=0.02 coat=0.0`
- **Evidence**: metallic=1.0, roughness=0.02 (mirror-smooth)

### J3
- **Skill**: blender-materials
- **Status**: PASS
- **Prompt**: Apply Recipe 8 (Lacquered plastic with Coat layer)
- **Result text**: `GEO-J3_lacquer: assigned=True metallic=0.0 roughness=0.15 coat=0.800000011920929`
- **Evidence**: Coat Weight=0.8 set successfully (note: this is a "Coat *", not "Subsurface IOR" — the disabled-input quirk doesn't affect Coat inputs)

### K1
- **Skill**: blender-modeling (extended; references/blender-patterns.md sweep-along-path pattern)
- **Status**: **PARTIAL** — produced 0 faces
- **Prompt**: Sweep a Bezier path with a Bezier circle as `bevel_object`
- **Code chunks executed**: 2
- **Result text**: `K1:swept_curve_to_mesh type=MESH verts=13 faces=0`
- **Evidence**: After conversion, mesh has only 13 vertices (just the resampled spline) and ZERO faces. The bevel_object profile didn't sweep — likely because Blender requires the profile curve to have `dimensions='2D'` for use as a `bevel_object`, but `bpy.ops.curve.primitive_bezier_circle_add()` creates a 3D curve by default.
- **If FAIL — likely root cause**: `references/blender-patterns.md` (which contains the sweep-along-path recipe inherited from `wireframe-to-3d`) likely does NOT mention the `dimensions='2D'` requirement on the profile curve. Recipe needs `profile.data.dimensions = '2D'` before assigning as bevel_object.
- **Patch suggestion for Opus**: add explicit `profile.data.dimensions = '2D'` to the sweep-along-path recipe wherever it appears (probably in `wireframe-to-3d/references/blender-patterns.md` and any sub-skill that references this pattern). Also consider adding K1b as the recommended primary pattern (simpler, no profile object needed).

### K1b
- **Skill**: blender-modeling
- **Status**: PASS
- **Prompt**: Same as K1 but using built-in `bevel_depth` (cylindrical) instead of `bevel_object`
- **Result text**: `K1b:bevel_depth_method type=MESH verts=208 faces=192`
- **Evidence**: 208 verts / 192 faces — clean tube along the curve

### K2
- **Skill**: blender-modeling (extended; references/overview.md surface revolution pattern)
- **Status**: PASS
- **Prompt**: Build a bottle profile and apply Screw modifier for 360° revolution
- **Code chunks executed**: 1
- **Result text**: `K2:bottle_revolution verts=704 faces=640`
- **Evidence**: Screw modifier with `axis='Z', angle=2π, steps=64` produced 704 verts and 640 faces. Surface revolution working as documented.

### K3
- **Skill**: blender-modeling
- **Status**: PASS — **fixes round-1 A4 test-design caveat**
- **Prompt**: Mirror modifier on a half-mesh that's actually offset to one side of object origin
- **Result text**: `K3:mirror_offset_half bbox_before=[0.00,1.00] bbox_after=[-1.00,1.00] symmetric=True doubled=True`
- **Evidence**: bbox doubled from [0,1] to [-1,1] after mirror application; symmetric across object origin. The Mirror modifier works correctly when the input mesh is properly placed; round-1 A4 simply used a centred cube which made the mirror produce overlapping geometry.

### L1
- **Skill**: blender-lighting
- **Status**: PASS
- **Prompt**: Apply outdoor-sun preset (Sun light, warm color, sharp shadows)
- **Result text**: `L1:sun_type=SUN energy=5.0 color=(1.0, 0.95, 0.8) angle_deg=0.50`
- **Evidence**: SUN type, golden-hour color, realistic sun angle (0.5° = sharp shadows)

---

### M — REAL SCENE BUILD (the most important test)

**This was the key test of the round.** Goal: drive the orchestrator-style chain end-to-end on a multi-part subject and check whether the recipes actually produce a *good* render. The skill recipes worked **mechanically** — every API call succeeded, every object was created, every material was applied, the render produced a valid PNG. But the **output quality** revealed real recipe gaps.

#### M.build — scene assembly
- **Status**: PASS
- **Steps executed in 1 chunk**:
  1. Create blade (scaled cube + bevel modifier)
  2. Create guard (scaled cube + bevel)
  3. Create grip (cylinder)
  4. Create pommel (sphere)
  5. Three materials (steel for blade, gold for guard+pommel, dark leather for grip)
  6. Three-point lighting (warm key, cool fill, cool rim)
  7. 85mm camera with f/4 DoF, Track-To constraint
- **Result text**: `M:scene_built objects=8 meshes=4 lights=3 cameras=1 materials=3`
- **Evidence**: Every object exists, every material is assigned, scene topology is correct.

#### M.render attempts — three iterations to surface recipe gaps

**Attempt 1** (`M_sword_attempt1_broken_world.webp`):
- Used recipes verbatim with no scene-prep
- **Render**: magenta dominates, sword barely visible as thin streak
- **Root cause**: The world tree from round-1 test C2 was still in place — an Environment Texture node with `image=None` cascading into Background. Result: undefined shader output, magenta visible everywhere.
- **This is a real recipe gap**: scene-build recipes assume a clean default world. The orchestrator should **reset world to a known state** before composition, or at least detect a broken world (Environment Texture without image) and substitute a neutral background.

**Attempt 2** (`M_sword_attempt2_clean_world.webp`):
- After replacing world with simple dark background (0.05, 0.05, 0.06) at strength 0.3
- Pulled camera back to (0.7, -1.6, 0.3); set lens to 60mm
- **Render**: clean dark BG, blade visible, but sword mostly in shadow — gold/leather details are barely visible, only blade reflects light from the rim
- **Issue**: Light positions in the lighting recipe (`(3, -3, 3.5)`, `(-3, -2, 2.5)`, `(0, 4, 3.0)`) are absolute world coords matching a generic 1m-cube subject — they're poorly positioned for a small (~1.3m vertical) sword scene
- **Issue**: Lights had explicit `rotation_euler` angles in the recipe but those don't necessarily aim at the new subject

**Attempt 3** (`M_sword_attempt3_aimed_lights.webp`):
- Programmatically aimed each light at the scene center (computed by averaging mesh locations)
- Repositioned lights closer to subject scale
- Used Track-To on an Empty at scene center for camera
- **Render**: gold guard, leather grip, gold pommel all clearly visible at correct shading. Blade extends out of top of frame because the "scene center" averages locations and biases focus down toward the smaller bottom parts.
- **Subjective quality**: image is not yet professional-quality but it IS a credible 3D render of the modelled object. Materials read correctly (gold reflects warm key, leather is matte dark, blade has metallic specular).

#### Findings for Opus (in priority order)

1. **CRITICAL — World state pre-condition**: The orchestrator (`text-to-blender/SKILL.md`) and/or every render-producing recipe should **reset the world to a neutral state** before composition. Suggested helper:
   ```python
   def reset_world(scene, color=(0.05, 0.05, 0.06, 1.0), strength=0.3):
       world = scene.world
       world.use_nodes = True
       nodes = world.node_tree.nodes
       for n in list(nodes):
           nodes.remove(n)
       output = nodes.new('ShaderNodeOutputWorld')
       bg = nodes.new('ShaderNodeBackground')
       bg.inputs['Color'].default_value = color
       bg.inputs['Strength'].default_value = strength
       world.node_tree.links.new(bg.outputs['Background'], output.inputs['Surface'])
   ```
   Add to `text-to-blender/SKILL.md` orchestrator workflow as step 0 ("ensure clean world"). Alternative: detect broken world (Environment Texture with `image=None` upstream of Background) and warn or repair.

2. **HIGH — Lighting recipe lacks subject-awareness**: The `blender-lighting/SKILL.md` Recipe 1 (three-point) places lights at fixed world coords `(3, -3, 3.5)` etc. and has explicit `rotation_euler` angles that don't necessarily aim at the subject. For the orchestrator's E2E pipeline, the lighting recipe needs an "aim at subject" parameter or an `aim_at(light, target)` helper. Suggested helper:
   ```python
   from mathutils import Vector
   def aim_at(light_obj, target_pos):
       direction = (Vector(target_pos) - light_obj.location).normalized()
       light_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
   ```
   Add to `blender-lighting/SKILL.md` with a recipe variant: "three-point aimed at subject".

3. **HIGH — Camera framing not subject-aware**: The `blender-cameras/SKILL.md` recipes assume a generic subject. For multi-part subjects, the orchestrator should compute a bounding box of the relevant meshes and frame accordingly (camera distance + focal length picked so the bbox fills ~80% of the frame vertically). Right now, generic 85mm at 1.8m distance worked for a 1m cube but clips the top of a 1.3m sword.

4. **MEDIUM — K1 sweep-along-path requires `dimensions='2D'`**: `references/blender-patterns.md` sweep-along-path recipe needs explicit `profile.data.dimensions = '2D'` line, otherwise the surface generation produces zero faces. Or recommend the simpler `bevel_depth` alternative (K1b passes; K1 with `bevel_object` failed).

5. **LOW — Round-1 A4 is now superseded by K3**: The A4 caveat in `test.md` (mirror modifier criterion weak on centred cube) is RESOLVED by K3 — the issue was test-design, not a recipe bug. Update `TESTING_PLAN.md` A4 to use an offset half-mesh.

#### What WORKED well in M (positive signal)

- Material recipes produced visually distinct surfaces (gold = clearly gold, steel = reflective, leather = matte dark)
- The `set_input` helper from v0.5.0 worked seamlessly across all 3 sword materials (no Subsurface IOR involved here, but the pattern is consistent)
- The `ensure_camera()` guard from v0.5.0 was used and correctly provided a camera reference
- Cycles 128 samples + OpenImageDenoise produced clean output in reasonable time (~10s render)
- AgX view transform handled the bright metallic highlights well (no blowouts on the gold)

---

## Output artefacts (committed for Opus visual review)

`plugin/skills/text-to-blender/assets/v0.6.0-round2-validation/`:

| File | Iteration | Notable |
|------|-----------|---------|
| `M_sword_attempt1_broken_world.webp` | First — recipes verbatim | Magenta-flooded; world from round-1 C2 was broken |
| `M_sword_attempt2_clean_world.webp` | After world reset | Clean BG; sword mostly in shadow due to fixed-coord lighting |
| `M_sword_attempt3_aimed_lights.webp` | After aiming lights at scene center + reframing | Best result; sword parts clearly visible; blade still clips top |

---

## Issues for Opus to address (Round 2)

In priority order:

1. **(CRITICAL)** World-state pre-condition: orchestrator should reset world (or repair broken Environment Texture) as step 0 of any scene assembly. Patch `text-to-blender/SKILL.md`.

2. **(HIGH)** Subject-aware lighting recipe: add `aim_at(light, target)` helper to `blender-lighting/SKILL.md` and a "three-point aimed at subject" recipe variant.

3. **(HIGH)** Subject-aware camera framing: add bounding-box framing logic to `blender-cameras/SKILL.md` (compute scene bbox of selected meshes, position camera at appropriate distance for the focal length, optionally adjust focal length to fit subject). Pair with Track-To on an Empty placed at bbox center.

4. **(MEDIUM)** Sweep-along-path 2D-dimension fix: in `wireframe-to-3d/references/blender-patterns.md` (and any inline reference), add `profile.data.dimensions = '2D'` to the sweep recipe. Mention `bevel_depth` as the simpler alternative.

5. **(LOW)** Update `TESTING_PLAN.md` A4 to use an offset half-mesh instead of a centred cube.

## Issues NOT to fix (already working correctly)

- All 3 extended material recipes (J1-J3): clean
- Surface revolution via Screw (K2): clean
- Mirror with offset half-mesh (K3): clean
- Outdoor sun (L1): clean
- Sword scene assembly mechanics (M.build): every API call succeeded; the issues are recipe-tuning around environment, lighting aim, and camera framing — NOT in the modeling/material recipes themselves.

---

## Note on subjective-quality testing

This round shows clearly: **objective tests** (does the API call succeed? does the file exist? is the metallic value 1.0?) catch a different class of bug than **subjective tests** (does the render look good?). The skill plugin passes 28/30 objective tests but produces a marginal-quality render on its first try at a real scene.

The patcher (Opus) needs to look at the three M_sword_attempt PNGs and decide whether the recipe gaps justify the patches in the priority list. This is exactly the work Opus is good at and Haiku can't reliably do.

---

## Patcher protocol reminder

Opus follow-up:
1. Read each FAIL/PARTIAL/SUBJECTIVE entry in priority order
2. Locate the affected `plugin/skills/<name>/SKILL.md` recipes
3. Write the patches per the suggestions above
4. Verify by re-running the M sword scene with the patched recipes — render attempt should succeed first try without the manual fixes I had to make
5. Append `## Patches applied` section here listing changes
6. Commit, tag v0.6.0, push

---

## Patches applied — 2026-04-27 (v0.5.0 → v0.6.0)

User-driven iteration: the user repeatedly inspected the actual Blender viewport (not just the rendered file) and called out errors that the orchestrator's numerical checks didn't catch. Each round of feedback drove a concrete patch.

### User's observations that drove patches

| User said | Diagnosis | Patch |
|-----------|----------|-------|
| "There is factually no sword, just a working pommel and grip" | Blade was 50×50cm flat panel (`scale=(0.04, 0.5, 0.5)` on a `size=1` cube) — wrongly sized; broad faces exposed instead of edge | Real-world reference dimensions added to `references/common-object-dimensions.md`; orchestrator must consult it before sizing |
| "Looks like a giant screwdriver" | Camera viewed thin axis (8mm) instead of broad face (4.5cm) | Axis-orientation guidance added to `blender-modeling`; explicit Z-rotation in the build code |
| "These mistakes should not happen in the future" | No visual validation between API-success and "done" | Mandatory `get_viewport_screenshot` + visual check in orchestrator workflow |
| "No sharp end now the sword" | Top vertices were scaled toward 0 but not merged → chiseled flat tip | Proper tapering recipe added to `blender-modeling` (collapse to centerline AND `remove_doubles`) |
| "The sword is grey and has no textures" | Blender viewport defaults to Solid shading mode (ignores materials); also the materials were flat colours | Viewport→Material Preview switch in orchestrator; procedural texture variation added (brushed-noise on steel, hammered-noise on gold, voronoi+bump on leather) |
| "The objects do not connect smooth to each other" | Adjacent primitives abutting exactly at boundaries left visible seams; cylinder-on-rectangle artifacts | Connection-overlap pattern added to `blender-modeling`: parts interpenetrate by 5-15mm; smooth shading on rounded parts |
| "Grip looks like a cylinder sitting on a rectangle" | Grip top abutting flat guard bottom showed obvious cylinder→rectangle transition | Same overlap pattern: grip extends 1.5cm INTO the guard volume, hiding the cylinder→rectangle transition |

### Concrete file changes

1. **`plugin/skills/text-to-blender/SKILL.md`**:
   - Workflow restructured: now 10 steps (was 7). New steps: world reset, dimension lookup, visual validation checkpoint, viewport-shading switch.
   - Added `reset_world()` helper section.
   - Added "Visual validation checkpoint" section requiring `get_viewport_screenshot` between rendering and reporting success.
   - Added "Set viewport to Material Preview mode" section as last step before reporting.
   - Added "Real-world dimension lookup" section pointing at the new reference file.
   - Added 6 new rows to the failure-modes table: viewport-grey, flat-materials, wrong-proportions, thin-pole-orientation, blunt-tip, axis-orientation.

2. **NEW `plugin/skills/text-to-blender/references/common-object-dimensions.md`** (~120 lines):
   - Reference dimensions for swords (multiple types), furniture, containers, vehicles, architecture, human-scale anchor.
   - Used as a lookup table BEFORE generating any modeling code.

3. **`plugin/skills/blender-modeling/SKILL.md`**:
   - Added "Critical: axis orientation for elongated objects" section (broad face vs thin axis convention).
   - Added "Critical: tapering to a point" section (collapse + `remove_doubles` for proper geometric points).
   - Added "Critical: connecting parts smoothly" section (deep overlaps + smooth shading + Boolean Union for seamless joins).

4. **`plugin/skills/blender-lighting/SKILL.md`**:
   - Added `aim_at(light, target)` helper.
   - Added `compute_scene_bbox_center()` helper.
   - Added Recipe 0 (subject-aware three-point lighting; positions + energies scale to subject extent).

5. **`plugin/skills/blender-cameras/SKILL.md`**:
   - Added Recipe 0 (bbox-aware hero camera; computes scene bbox, fits subject to ~80% vertical frame at chosen focal length, Track-To via Empty).

### Verification (post-patch)

The user-observed sword scene was rebuilt fresh using the patched recipes (referencing `common-object-dimensions.md` for sizing, applying the orientation/tapering/overlap rules from `blender-modeling`, the subject-aware lighting from `blender-lighting`, the bbox camera from `blender-cameras`, the world-reset and viewport-mode steps from the orchestrator).

Final result: `plugin/skills/text-to-blender/assets/v0.6.0-round2-validation/M_sword_FINAL_v0.6.0.webp` — a recognizable sword with proper proportions, sharp pointed tip, gold guard with hammered finish, leather grip with voronoi grain, gold pommel, all parts integrated without visible seams.

### Quality estimate

- v0.5.0 — 8/10 (28/30 unit tests pass)
- **v0.6.0 — 8.5/10** — orchestrator now produces credible scene-builds on first try when given a real-world subject (was: produced broken renders that required 5+ iterations of user-driven correction)

### What v1.0 still needs (from VERSIONING.md)

Even with v0.6.0's improvements, several items remain:
- [ ] Cross-test on Blender 4.x (compat branches)
- [ ] Wireframe-to-3d full e2e (with `pip install` of cv2/numpy/scipy)
- [ ] Add 5-10 more sample objects to `common-object-dimensions.md` (table, mug, lamp, helmet, etc.)
- [ ] Worked example scenes for chair, bottle, character — not just sword
- [ ] Trigger-eval JSON files per skill (~20 trigger / 20 no-trigger queries each)
- [ ] External user feedback (1+ week of real use)

### Key lesson from this round

**The user is the visual-validation oracle that the orchestrator cannot replace.** Every patch in this round came from the user looking at the *actual* Blender viewport and the *actual* render and saying "this is wrong" — when the API calls reported success and the numerical checks all passed. The orchestrator now has a mandatory visual-validation checkpoint, but the LESSON is that subjective quality checks remain part of the pipeline; we made them explicit rather than skipping them.
