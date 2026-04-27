# Changelog

All notable changes to **cc-blender-skill** since first commit. Detailed rationale per version is in [`VERSIONING.md`](./VERSIONING.md). Patch-by-patch root-cause notes are in [`IMPLEMENTATION_LOG.md`](./IMPLEMENTATION_LOG.md). Test results are in [`test.md`](./test.md) and [`test_round2.md`](./test_round2.md).

## [1.0.0] — 2026-04-27

### First stable release

- 10-skill plugin (orchestrator + 8 domain skills + wireframe-to-3d specialty) validated end-to-end against Blender 5.1.1
- Three real scene classes proven: sword (primitive assembly + metallic), bottle (surface revolution + glass), chair (multi-part + wood) — first-try renders with v0.6.0+ patches
- Wireframe-to-3d e2e closure: aviator wireframe → 21 contours → recognisable Ray-Ban-style render
- 200-query trigger-eval set across the 10 skills
- Cross-version compat documented for Blender 4.x and 5.x users
- Honest scope boundaries documented: design quality ≠ build correctness, wireframe-to-3d as foundation not deliverable

### What's stable

- Pipeline: world reset → real-world dimension lookup → modeling → materials → lighting → camera → render → export → visual-validation checkpoint
- All Blender 5.x cross-version patches verified live (BLENDER_EEVEE_NEXT fallback, action.fcurves compat helper, set_input for disabled BSDF inputs, ensure_camera guard)
- Subject-class lighting (`metal` / `glass` / `wood` / `fabric` / `skin` / `product`)
- Volume Absorption recipe for coloured glass with density tables
- Connection-overlap pattern (5–15 mm interpenetration to hide cylinder→cube seams)
- Real-world dimension reference for swords, chairs, bottles, mugs, tables, lamps, eyewear

### Known limitations (honest)

- **Design quality ≠ build correctness.** Plugin produces functionally correct objects, not aesthetically polished ones. A "well-designed chair" requires curated style libraries beyond automated generation.
- **Wireframe-to-3d auto-extraction.** Single front-view wireframes drop classic-design DNA (e.g., Ray-Ban double-bar bridge, lens droop). For complex named-design objects, use wireframes as REFERENCE alongside hand-crafted geometry.
- **Thin-metal specular flare.** Hero shots of thin metal (eyewear arms, jewellery) catch side lighting as bright streaks. Workaround: top-down softbox or crop.
- **Subjective quality is human-driven.** Numerical validation (object count, file size, no errors) passes ≠ render looks right. The mandatory visual-validation checkpoint exists; the user remains the final oracle.
- **External user feedback pending.** v1.0.0 is internal-validated; broader real-use feedback is the next step.

---

## [0.9.3] — 2026-04-27

- Trigger-eval scaffolding: 200 queries across 10 skills (10 trigger + 10 no-trigger each)
- Companion `EVALS_README.md` describing schema, manual run loop, and Claude `--print` automation sketch

## [0.9.2] — 2026-04-27

- Aviator hand-crafted with proper Ray-Ban dimensions: 58×50mm teardrop lens with droop, double-bar bridge, gunmetal frame, mirror lens, silicone nose pads, articulated temple arms
- "Eyewear / sunglasses" section added to `references/common-object-dimensions.md`
- Methodological lesson: wireframes as VISUAL REFERENCE for complex named-design objects, not auto-extracted contours

## [0.9.1] — 2026-04-27

- Scope-boundary section in `wireframe-to-3d/SKILL.md`: skill produces 2D outline tracing extruded to thin curves, NOT full 3D models
- Aviator chained-upgrade demo: wireframe-to-3d + blender-modeling + blender-materials + blender-lighting + blender-cameras + blender-rendering produces a Ray-Ban-style hero render
- Validates orchestrator's multi-skill chain capability

## [0.9.0] — 2026-04-27

- Subject-class lighting (`Recipe 0a` in `blender-lighting`) with profiles for metal/glass/wood/fabric/skin/product — resolves v0.7.0 known limitation
- Wireframe-to-3d full end-to-end validation: 2 real bugs surfaced and fixed in `wireframe_analyzer.py` (contour filter using `cv2.contourArea` returned ~0 for thin Canny edges; morphological closing destroyed wireframe lines)
- Bottle volume density correction (Density 30 → 80 for proper wine-bottle green)
- New dimension entries: dining table, desk lamp, floor lamp; refined coffee mug
- Cross-version compat doc (`blender-version-compat.md`) with smoke-test snippet

## [0.8.0] — 2026-04-27

- Chair scene end-to-end validation (multi-part assembly + procedural wood)
- Updated `references/common-object-dimensions.md` chair entry with structural details (stretchers, slatted back, top rail, leg taper) to produce a Mission/Shaker chair
- Wood material tuning lessons documented (bump 0.20, smooth 3-stop ColorRamp, Voronoi ≤0.10 OVERLAY)
- Honest design-quality limitation made explicit: build correctness ≠ aesthetic polish

## [0.7.0] — 2026-04-27

- Bottle scene end-to-end validation (surface revolution via Screw modifier + transmissive glass)
- New `Recipe 6b (Coloured glass with Volume Absorption)` in `blender-materials/SKILL.md`
- Surface near-white + slight roughness + Volume Absorption shader on Material Output's Volume input → proper depth-based glass colour
- Density tuning guide + 5-row colour table (wine, champagne, cobalt, amber, ruby)
- Documented Cycles `transmission_bounces=24` for thick/layered glass

## [0.6.0] — 2026-04-27

- User-driven scene-quality iteration on the sword: 7 patches across 4 skill files
- `references/common-object-dimensions.md` added — real proportions for sword, chair, bottle, etc.
- `text-to-blender/SKILL.md` workflow restructured: 7 steps → 10 steps with mandatory world reset, dimension lookup, visual validation, viewport-shading switch
- `blender-modeling/SKILL.md`: axis-orientation guidance, proper tapering recipe, connection-overlap pattern
- `blender-lighting/SKILL.md`: `aim_at(light, target)` helper + Recipe 0 (subject-aware three-point)
- `blender-cameras/SKILL.md`: Recipe 0 (bbox-aware hero camera)

## [0.5.0] — 2026-04-27

- Tester+Patcher validation loop complete (Haiku tester ran 30 tests; Opus root-caused and patched failures)
- Bug 1: `Subsurface IOR` BSDF input has `enabled=False` flag on Blender 5.x — string-key lookup fails. Added `set_input(node, name, value)` helper that iterates inputs.
- Bug 2: `bpy.ops.render.render()` requires active `scene.camera`. Added `ensure_camera(scene)` guard.
- Failure-modes table updated in `text-to-blender/SKILL.md` for both errors

## [0.4.0] — 2026-04-27

- First end-to-end validation pass against live Blender 5.1.1
- 5/5 representative prompts pass after patches
- Bug 1: `BLENDER_EEVEE_NEXT` doesn't exist on Blender 5.x — added `try/except` fallback to `BLENDER_EEVEE`
- Bug 2: `action.fcurves` removed in Blender 5.x layered Actions — added `get_fcurves_compat()` helper

## [0.3.0] — 2026-04-27

- Initial plugin scaffolding: 10 skills written to official Anthropic Skills spec
- Each sub-skill ≤500 lines per cap, with `references/overview.md` for long-tail depth
- Manifest, READMEs, install instructions, repository structure
- **Not yet validated** — scaffolding-only release; ships as known-untested foundation

## [0.2.0] — 2026-04-27

- 16-domain knowledge base researched (~6500 lines aggregated from ~80 web sources)
- Tier A/B/C/D source quality grading

## [0.1.0] — 2026-04-26

- Initial research foundation: 6 documents covering algorithms, Blender best practices, MCP alignment, skill specification
- Production-ready `wireframe_analyzer.py` image processing pipeline (untested e2e at this point)
- Initial `wireframe-to-3d` SKILL.md as proof-of-concept
