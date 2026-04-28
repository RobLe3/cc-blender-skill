# Changelog

All notable changes to **cc-blender-skill** since first commit. Detailed rationale per version is in [`VERSIONING.md`](./VERSIONING.md). Patch-by-patch root-cause notes are in [`docs/process/IMPLEMENTATION_LOG.md`](./docs/process/IMPLEMENTATION_LOG.md). Test results are in [`docs/test-results/`](./docs/test-results/).

## [1.2.3] — 2026-04-28

### Repo hygiene reorg + .github scaffolding

Top-level was cluttered with 14 .md files (process docs + test results). Reorg moves them into `docs/process/` and `docs/test-results/`, leaving only canonical files at the root.

**Top-level after reorg** (4 .md + LICENSE + requirements.txt + .gitignore):
- `README.md`
- `CHANGELOG.md`
- `VERSIONING.md`
- `LICENSE`

**Moved to `docs/process/`** (8 dev journals): `PLAN.md`, `DEVELOPMENT.md`, `TESTING_PLAN.md`, `IMPLEMENTATION_LOG.md`, `VERIFICATION_REPORT.md`, `MCP_COVERAGE_ASSESSMENT.md`, `BLENDER_TOOLKIT_COMPARISON.md`, `INSTALL_BLENDER_MCP.md`.

**Moved to `docs/test-results/`** (3 round logs): `test.md`, `test_round2.md`, `test_round3.md`.

**Added `.github/`**:
- `CONTRIBUTING.md` — bug-report and feature-request workflow, honesty principle, semver
- `ISSUE_TEMPLATE/bug_report.yml` — structured form (Blender version, OS, prompt, failure type, what happened vs expected)
- `ISSUE_TEMPLATE/feature_request.yml` — structured form (change type, description, motivation, optional draft recipe)
- `ISSUE_TEMPLATE/config.yml` — disables blank issues, links to discussions and ahujasid/blender-mcp for upstream MCP bugs

Updated cross-references in README, CHANGELOG, and VERSIONING to point at new locations. `git mv` preserves blame history.

This is structural housekeeping. No skill code changed.

## [1.2.2] — 2026-04-28

### Repo housekeeping — LICENSE, GitHub metadata, formal releases

Used `gh` CLI to set up the repo's discoverability and legal context:

- **`LICENSE`** added (MIT) — the README has claimed MIT since v0.3.0, but the actual file was missing
- **Repo description** set: "Claude Code skill plugin: drive Blender 5.x like a senior 3D artist via natural language. 10 chain-loadable skills..."
- **Repo topics** added: `claude-code`, `claude-skill`, `blender`, `blender-mcp`, `blender-python`, `3d-modeling`, `mcp`, `ai-3d`, `procedural-modeling`, `gltf`
- **Homepage URL** set to the README
- **Formal GitHub Releases** created for v1.0.0, v1.1.0, v1.2.0, v1.2.1 — each with curated release notes, not just auto-generated tag pages

This is housekeeping, not feature work — making the repo properly discoverable and legally clear. Users finding the repo via GitHub topics can now see what it does at a glance, and the formal releases give them clean version-by-version notes instead of having to read commit logs.

## [1.2.1] — 2026-04-28

### Hard limit on "human face from primitives" — three escape paths documented

User feedback on v1.2.0 broadcaster: "does not even close resemble a human." Accurate. Tried adding facial features (cube nose, sphere ears, line mouth, bar brows) to test whether more primitives could cross from "abstract avatar" to "human face." Result: validation iteration `assets/v1.2.0-validation/04_broadcaster_with_features_still_not_human.png` shows the limit — added features cross from "ball" to "abstract avatar" but NOT to "human."

The hard limit: real human faces require **subtractive sculpting** (eye sockets recessed into the head, cheekbones pulled out, lip curvature, jaw line, chin shape) — features that can't be added as floating primitives, only carved into a base mesh.

Documented in `references/common-object-dimensions.md` as **three realistic paths past the limit** (all out of pure-recipe scope):

1. **Import existing human base mesh** via Blender MCP's asset tools (`download_polyhaven_asset` / `download_sketchfab_model` / `generate_hyper3d_model_via_text`) — cheapest automated route, then chain skin/lighting/rendering
2. **Sculpt mode** — gestural, not driven well from natural language; recipe can prepare base mesh, user sculpts manually
3. **Commission a Blender character artist** per `prompts/04-blender-workflow.md` (6-10 hours)

Added a corresponding row to the orchestrator's failure-modes table (`text-to-blender/SKILL.md`): "User asks for a 'human' / 'character' / 'face'" → suggest one of the three paths; do NOT pretend a sphere-with-features looks human.

This is the same kind of honesty as v0.8.0's chair-design boundary and v1.2.0's character-scope statement, but with a concrete failure-mode entry pointing the orchestrator at MCP tools (`generate_hyper3d_model_via_text` etc.) that ARE available even though they're outside pure-recipe scope. Real automated humans require AI 3D generation; the skill plugin is the orchestration layer on top.

Quality estimate: 8.5/10 unchanged. The honest documentation of limits IS the contribution.

## [1.2.0] — 2026-04-28

### Stylized broadcaster avatar — character-work scope boundary documented

Tested the skill against `docs/avatar-design-kit/prompts/01-concept-sheet.md` — a Max-Headroom-flavour digital broadcaster character (head + suit + hair + glasses + cyan/magenta synthwave lighting). Built a primitives-only version using existing recipes; documented what works and what doesn't.

**What works** (committed to `references/common-object-dimensions.md` under "Characters / avatars"):
- Sphere-head broadcaster silhouette with subsurface skin + sheen suit + flat hair shape + aviator glasses + dramatic cyan/magenta lighting
- Final synthwave-lit render shows recognizable retro-CGI broadcaster look
- Subsurface skin recipe (Subsurface Weight 1.0, Radius (1.0, 0.25, 0.10)) validates the v0.5.0 `set_input` helper for the disabled `Subsurface IOR` input

**What doesn't work** (honest scope boundary added):
- Realistic facial features (eyes, nose, mouth, ears) — primitives can't carve these
- 15-viseme animation blendshapes per TECH-SPEC.md
- Hand-textured skin / believable hair / proper anatomy
- Posing / rigging / production character animation

The orchestrator should warn users when they request character work that automated generation produces a **recognizable silhouette only**, and recommend a human Blender character artist for production output (per `prompts/04-blender-workflow.md`'s 6-10 hour estimate).

**New recipe finding**: strong colored lighting (cyan/magenta synthwave) overpowers subtle PBR materials. To keep both visible: reduce dramatic light energy 10x compared to standard 3-point intuition (cyan key 250W not 800W; magenta rim 200W not 600W; warm fill 15W max). World Strength 0.15 for proper contrast.

**Three render iterations** committed for honesty:
- `01_broadcaster_too_bright.png` — first attempt, lights at 800W washed everything out
- `02_broadcaster_neutral_dominates.png` — added neutral key, materials still washed
- `03_broadcaster_synthwave_FINAL.png` — final synthwave-mood result with proper light energy ratios

Quality estimate stays at **8.5/10** — character work is honestly out of scope; the limit is documented.

## [1.1.0] — 2026-04-27

### New scene class — desk lamp; emission material + practical lighting recipes

Built a desk lamp scene end-to-end (base + articulated arms + shade + emissive bulb + desk surface) — fourth scene class after sword/bottle/chair, testing the missing primary material class (**emission**) and a new lighting paradigm (**practical lighting**: subject contains its own light source).

**New recipes**:

1. **`blender-materials/SKILL.md` Recipe 11b — Emission**: replaces Principled BSDF with `ShaderNodeEmission` for light-emitting meshes (bulbs, neon, screens). Includes a strength-tuning table because mesh emission scales with surface area (small bulb sphere needs Strength 800-3000; large window plane needs Strength 5-20). Companion sub-recipe for **lamp-shade interior** using flipped-normal duplicate with bright-white material so the bulb illuminates the shade interior realistically.

2. **`blender-lighting/SKILL.md` Recipe 0c — Practical lighting**: 5-step setup for scenes whose subject contains an emissive source (desk lamp, candle, monitor). Dim world background, drop standard 3-point, single subtle ambient fill, high emission strength, Cycles `max_bounces ≥ 16` for proper interior-shade bouncing.

**Validation proof**: `text-to-blender/assets/v1.1.0-validation/desk_lamp_emission.png` shows the result: recognisable articulated desk lamp with visible bulb glow inside the shade, warm pool of practical light on the desk, lamp body silhouetted correctly against dark scene.

**Findings worth documenting**:
- Mesh emission strength is **NOT comparable** to light-object energy — strength scales with surface area, so small mesh emitters need values 100x+ higher than intuition suggests
- Single-mesh shades only show one material side; a flipped-normal interior duplicate is needed for realistic shade-illumination effect
- Practical lighting requires dropping standard 3-point — fight the temptation to add fill or rim, the emissive subject should dominate

## [1.0.1] — 2026-04-27

### Trigger-eval self-assessment — descriptions validated, no patches needed

Closed the loop on the 200-query trigger-eval set shipped in v0.9.3 by running each query against its skill's `description` + `when_to_use` text and judging whether the description would cause Claude to load the skill.

**Results**:
- **TP rate: 100% (100/100)** — every trigger query cleanly matches a relevant phrase in the supposed-to-trigger skill's description
- **FP rate: 4% (4 borderline / 100)** — well below the 10% intervention threshold
- **Decision**: descriptions ship unchanged. The 5 borderline FPs identified are intrinsically ambiguous queries where description tuning would risk hurting legitimate TP recall.

**Borderline cases documented as known soft spots** in `test_round3.md` (not bugs, just edge cases for real-use observation):
- text-to-blender on explanatory/theory questions
- blender-materials on animation-of-material-properties
- blender-export on "without Blender" conversion requests
- blender-pro-workflow on Cycles-vs-EEVEE comparisons
- wireframe-to-3d on 2D-to-2D vectorization

This is a **self-assessment**, not a black-box eval. Real Claude-fresh-session validation comes from actual usage. The 10/10 per-skill starter set is appropriate for v1.0.x; expanding to 20/20 would surface more edge cases in v1.x.

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
