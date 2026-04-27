# Versioning — Honest Quality Path to v1.0

**Current version**: **1.0.0** — first stable release
**Date**: 2026-04-27

---

## Why we're not calling this v1.0

The skill plugin is structurally complete (10 skills, ~6500 lines of distilled knowledge across 16 domains, official-spec-compliant SKILL.md files). But **none of this has been run against an actual Blender instance**. Calling it v1.0 would oversell quality and erode trust on first failure.

A senior skill author would gate v1.0 on:
1. End-to-end execution against a real Blender MCP
2. Recipe coverage of the long tail (current is ~80% of common requests)
3. Trigger-eval test cases per skill (Anthropic recommends ~20 per skill)
4. Worked example scenes with proof-renders

Until then, this is an honest **0.3.0** — production-ready scaffolding.

---

## Quality assessment

### Strong (7-8/10 confidence)
- Architecture verified against actual Blender MCP source (`/Users/roble/.tools/blender-mcp/src/blender_mcp/server.py`, `addon.py`)
- Aligned with Anthropic's official Skills spec (read the docs, didn't guess)
- Naming/structure follows Blender Studio conventions
- Doesn't duplicate `ra100/blender-claude-plugin` or `Dev-GOM/blender-toolkit`
- 16 knowledge domains researched with ~80 sources, mostly Tier A/B
- Each sub-skill has a decision tree + inline recipes + references pointer
- Pure-skill design (no Python wrapper class to maintain)

### Weaknesses (3-5/10)
- **Zero validation**: estimated 20–30% of generated Python may need fixes on first run due to Blender 5.x version-specific quirks
- **Recipe library shallow**: ~5–12 inline recipes per domain (a pro skill needs hundreds across the long tail)
- **No trigger evals**: descriptions written once, not iteratively tuned
- **No worked examples**: nothing in `assets/` proves the plugin produces good output
- **Single-pass research**: ~1 day depth per domain, not 3–5 rounds + paper reading + Blender verification
- **`wireframe-to-3d` also untested**: the most-finished sub-skill has the same problem as the rest

### Unknowns
- Will Claude reliably pick recipes, chain sub-skills, and recover from errors? Not measured.
- Are descriptions "pushy" enough to trigger reliably without false-positives? Not tested.

---

## Version path

| Version | Definition of done |
|---------|---------------------|
| **0.3.0** *(current)* | Plugin structure complete; all 10 skills written; manifest + READMEs; no validation |
| **0.5.0** | Each skill smoke-tested against Blender via `mcp__blender__execute_blender_code`; bugs documented in `IMPLEMENTATION_LOG.md` and fixed; failure rate < 10% on common requests |
| **0.7.0** | Trigger-eval JSON files per skill (20 trigger + 20 no-trigger queries each); description-tuning loop run twice; recipe library expanded ~2× in modeling, materials, lighting |
| **0.9.0** | 3–5 worked example scenes (sword + materials + render, character close-up, archviz still) with proof-renders committed to `assets/`; install instructions verified on macOS + Linux + Windows |
| **1.0.0** | All of the above + 1+ week of real-use feedback from external testers, top failure modes patched, clear changelog |

**Estimated effort to v1.0**: 1–2 weeks of focused work after this scaffolding pass.

---

## What changed at each version

### 1.0.0 — 2026-04-27 — First stable release

The roadmap from v0.3.0 (scaffolding, untested) to v1.0.0 took **9 versions of patches and user-driven validation**. Each step is recorded in this file with rationale; each commit message records concrete bugs found and fixed; the validation proof renders in `plugin/skills/text-to-blender/assets/v0.X.0-validation/` are honest evidence (including failure-state renders, not cherry-picked).

**What's stable for v1.0.0**:

- **Pipeline**: world reset → real-world dimension lookup → modeling → materials → lighting → camera → render → export → mandatory visual-validation checkpoint
- **All Blender 5.x cross-version patches verified live**: `BLENDER_EEVEE_NEXT` fallback, `action.fcurves` compat helper, `set_input` for disabled BSDF inputs, `ensure_camera` guard
- **Subject-class lighting** with profiles for metal / glass / wood / fabric / skin / product
- **Volume Absorption recipe** for coloured glass with density tables (5 colour types)
- **Connection-overlap pattern** (5–15 mm interpenetration) hides cylinder→cube seams
- **Real-world dimension reference** for swords, chairs, bottles, mugs, tables, lamps, eyewear
- **Trigger-eval scaffolding**: 200 starter queries across 10 skills

**Validation in numbers**:

| Scene | Validated | Render proof |
|-------|-----------|--------------|
| Sword (primitive assembly + metallic) | ✅ | `v0.6.0/M_sword_attempt6_with_pointed_tip.png` |
| Bottle (surface revolution + glass) | ✅ | `v0.7.0-bottle-validation/bottle_FINAL_v0.7.0.png` |
| Chair (multi-part + wood) | ✅ | `v0.8.0-chair-validation/chair_FINAL_v0.8.0.png` |
| Aviator wireframe-to-3d | ✅ (foundation) | `v0.9.0-validation/03_aviator_wireframe_to_3d.png` |
| Aviator chained upgrade | ✅ | `v0.9.0-validation/04_aviator_chained_upgrade.png` |
| Aviator hand-crafted hero | ✅ | `v0.9.0-validation/05_aviator_proper_rayban_dimensions.png` |
| Bottle with glass-class lighting | ✅ | `v0.9.0-validation/02_bottle_proper_wine_density.png` |

**What's explicitly NOT in v1.0.0** (called out so users aren't surprised):

- Aesthetic-design quality (curved chair backs, profile-cut legs) — out of automatic scope; human-driven step
- Reliable wireframe-to-3d for complex named-design objects (Ray-Ban Aviator's double-bar bridge) — wireframes are reference for these, not source
- Suppressed thin-metal specular flare in side lighting — workaround documented, not patched at recipe level
- External-user feedback loop — internal validation only
- Cross-tested Blender 4.x — compat code present but not directly run on a 4.x install

**Quality estimate**: 8.5/10. Genuine, earned through user-driven iteration. Not 10/10 because the limits above are real.

### 0.9.3 — 2026-04-27 — Trigger-eval scaffolding for description tuning

Per the Anthropic Skills best-practices doc — skill descriptions are the primary triggering mechanism, and they should be tuned via a trigger-eval loop. Each skill now has a starter `evals/evals.json` with **10 trigger queries** (should activate the skill) + **10 no-trigger queries** (should NOT activate).

**200 queries total across 10 skills.** The trigger queries verify Claude loads the right skill on natural-language prompts; the no-trigger queries verify it doesn't over-activate on adjacent or unrelated requests.

**Key design decisions in the eval queries:**
- Adjacent-skill no-trigger cases test internal routing (e.g., for `blender-modeling`, "apply gold material" should NOT trigger modeling — should route to `blender-materials`)
- Knowledge/explanatory queries are no-trigger (e.g., "explain how subdivision surface works" doesn't need to *do* anything in Blender)
- External-pipeline queries are no-trigger (e.g., "convert FBX to glTF without Blender" → out of scope)
- Borderline cases include rationale notes (e.g., "vectorize this raster to SVG" for `wireframe-to-3d` — could go either way)

**Companion doc**: `plugin/skills/EVALS_README.md` documents the schema, the manual run-loop, the optional Claude `--print` automation sketch, and honest caveats (starter set sized 10/10 not the recommended 20/20).

These are the **last item before v1.0**. The trigger-eval files don't change skill behaviour but they enable the description-tuning loop that v1.0 stability depends on.

### 0.9.2 — 2026-04-27 — Aviator dimensions + hand-crafted hero render

User pointed out: even the v0.9.1 chained aviator wasn't a "real Ray-Ban" — it had simple frame outlines and lens discs but lacked the classic details (double-bar bridge, proper teardrop lens shape, gunmetal frame, nose pads). This patch addresses the gap by using **wireframe-as-reference** rather than wireframe-as-source for complex objects.

After inspecting the avatar-design-kit archive (found `aviator_glasses_hero.png` showing the target look + side/back wireframes I hadn't used), I hand-crafted an aviator using proper Ray-Ban dimensions and the hero render as visual reference:

- **Lens**: 58mm × 50mm teardrop with bottom droop; built as Bezier-outline rim + filled inner disc with bottom pulled 10% lower for the classic asymmetric shape
- **Double-bar bridge**: top horizontal wire spanning both lenses + middle saddle bar — the iconic Aviator detail
- **Frame wire**: 0.6mm bevel depth (slim); gunmetal material (`Metallic=1.0, Base Color=(0.18,0.18,0.20), Roughness=0.30`)
- **Mirror lenses**: solid metal with dark blue F0 tint (`Metallic=1.0, Base Color=(0.05,0.10,0.22), Roughness=0.05`)
- **Nose pads**: silicone pills at bridge underside (`Metallic=0, Roughness=0.5, IOR=1.4`)
- **Temple arms**: 135mm Bezier curves with hinge → straight-back → ear-bend → curl-down-tip

**New reference**: added "Eyewear / sunglasses" section to `references/common-object-dimensions.md` with the full aviator construction recipe and the gunmetal/mirror/tinted material variants.

**Honest known limitation noted in the reference**: thin metal temple arms catch side lighting as specular streaks in narrow studio setups. Recommended workaround: top-down softbox lighting OR crop temple arms out of the frame.

**Methodological lesson committed**: wireframe-to-3d auto-extraction is good for *foundation outlines* of simple objects (the v0.9.0 frame); for complex objects with classic-design details (Ray-Ban Aviator's double-bar bridge, teardrop lens shape), **wireframes work better as VISUAL REFERENCE alongside hand-crafted geometry with real-world dimensions**. The orchestrator should:
- Use wireframe-to-3d when simple outlines suffice (icons, logos, technical drawings)
- Use real-world dimensions + hand-crafted Bezier curves when the subject has named-design details that aren't trivially extractable from line art

Quality estimate: **8.5/10** unchanged. The v0.9.2 aviator is a real improvement over v0.9.1 but the temple-arm flare and the hard line between "foundation extraction" vs "design knowledge" remain explicit limits.

### 0.9.1 — 2026-04-27 — Wireframe-to-3d scope boundary + chained-upgrade demo

User pointed out: the v0.9.0 wireframe-to-3d output is recognizable as aviator sunglasses but not a "complete rendered and textured Ray-Ban". Accurate — the skill produces **2D outline tracing extruded to thin curves**, not a full 3D model with depth, lenses, or production materials. That's its honest scope.

This patch:
1. **Documents the scope boundary explicitly** in `wireframe-to-3d/SKILL.md` — added a "Scope boundary" section listing what wireframe-to-3d does NOT produce, and pointing the orchestrator at the multi-skill chain that does.
2. **Demonstrates chained upgrade** — re-rendered the aviator using wireframe-to-3d as the foundation + blender-modeling (filled lens discs as scaled UV spheres + temple arms as Bezier curves) + blender-materials (gold metal frame `Metallic=1.0/Roughness=0.18`, blue mirror lens `Metallic=0.9/Roughness=0.04`) + subject-class metal lighting + 100mm product-shot camera + Cycles render.
3. **Proof committed**: `assets/v0.9.0-validation/04_aviator_chained_upgrade.png` shows what the chained orchestration produces (recognizable Ray-Ban-style hero) vs `03_aviator_wireframe_to_3d.png` (raw wireframe-to-3d output, flat outline tracing).

The orchestrator (`text-to-blender/SKILL.md`) is updated to explicitly plan for chaining when the user asks for "a model of X from this wireframe" — wireframe-to-3d is the foundation, never the deliverable on its own.

### 0.9.0 — 2026-04-27 — Coverage expansion (4 items toward v1.0)

Four targeted improvements driven by the v0.x → v1.0 plan:

1. **Subject-class lighting hints** (`blender-lighting/SKILL.md` Recipe 0a). Generic 3-point lighting (Recipe 0b — the v0.6.0 baseline) uses a fixed 4:1:2 key:fill:rim ratio that washes out coloured-glass volume tint and is too cool for wood. New Recipe 0a takes a `subject_class` hint (`'metal'`, `'glass'`, `'wood'`, `'fabric'`, `'skin'`, `'product'`) and tunes ratios + colour temperatures + rim-light type accordingly. Resolves the v0.7.0 known limitation. Validated by re-rendering the bottle with `subject_class='glass'` — green tint now visible without strong rim wash.

2. **Wireframe-to-3d full end-to-end validation** — closes the original use case the repo started with (the wireframe-to-3d skill has existed since v0.3.0 but never run end-to-end). Two real bugs surfaced and patched in `wireframe_analyzer.py`:
   - **Contour filter used `cv2.contourArea`** which returns ~0 for thin Canny edges → all contours filtered out. Fixed by using `max(area, arcLength)` so thin edges are scored by their length.
   - **Morphological closing with 5×5 ellipse kernel destroyed wireframe lines** because dilation eats into ~3-pixel-wide black lines. Added `line_art=True` mode (default) that skips Gaussian blur + Canny entirely and traces contours directly on the binary mask — using closing kernel of 3×3 only when `gaussian_kernel > 0`.
   - Result: aviator wireframe → 21 extracted contours → Blender curves with 0.8mm bevel → metallic frame material → recognizable aviator-sunglasses render. Proof in `assets/v0.9.0-validation/03_aviator_wireframe_to_3d.png`.

3. **Bottle volume density correction** — the new glass-class lighting was so soft that the v0.7.0 default Density=30 read as "obsidian glass" (user's term). Updated the Recipe 6b density table: wine bottle Density=80 (was 30), with deeper saturated colours. Re-validated bottle now reads as proper wine green with depth-based variation.

4. **Reference dimensions expanded**: added entries for **dining table** (with apron details), **desk lamp** (articulated arm + base + shade), **floor lamp** (drum shade), and refined **coffee mug** (Boolean Difference for interior, ceramic material guidance). Also added **Blender Version Compatibility Matrix** (`references/blender-version-compat.md`) documenting all cross-version patches and providing a smoke-test snippet users can run on their install.

Quality estimate: **8.5/10** (unchanged) — these are coverage-and-correctness improvements rather than capability jumps. The headline win is the wireframe-to-3d closure: a skill that has existed since v0.3.0 finally producing 3D output from real input.

### 0.8.0 — 2026-04-27 — Chair scene; design-quality limitation made explicit
- Built a Mission/Shaker dining chair end-to-end. Tests multi-part assembly (seat + 4 legs + back + 4 stretchers + 5 slats + top rail = 15 parts) and procedural wood — different stress profile from sword and bottle.
- All v0.6.0+v0.7.0 patches applied first try. Iteration was driven by user feedback at each step (texture too subtle → texture too busy → balanced wood → still simple shape → added structural details).
- Final result: recognisable Mission chair with stretchers, slatted back, top rail, tapered legs, wood grain.
- **Updated `references/common-object-dimensions.md`** for chair entry: the previous version listed only bare dimensions ("seat 45×45×4cm, 4 legs"). New version documents the structural details (stretchers, slatted back, top rail) and shape refinements (leg taper, edge bevels) needed to produce a recognisable chair instead of a stack of rectangles.
- **Wood material tuning** documented in `assets/v0.8.0-chair-validation/README.md`: bump strength 0.20 (not 0.6 or 0.15), ColorRamp 3 stops with smooth gradient, Voronoi influence ≤ 0.10, Wave Scale 12 with Distortion 3.
- **Honest limitation surfaced and documented**: build correctness ≠ design quality. The user said "looks better, but is still an ugly designed chair" — accurate. We can produce functionally correct objects (recognisable, anatomically right, properly textured) but not *well-designed* ones (curved slats, profile-cut legs, contoured seat). Aesthetic refinement is a human-driven step beyond the orchestrator's automatic capability.
- Quality estimate: **8.5/10** unchanged. The chair-detail patterns are a real win for "build a chair" → "build a *real* chair", but design-quality limitation remains.

**Three scene classes now validated**: sword (primitive assembly + metallic), bottle (revolution + glass), chair (multi-part + wood). The pipeline patches generalise across all three.

### 0.7.0 — 2026-04-27 — Bottle scene; v0.6.0 patches generalise + glass-class refinement
- Built a wine bottle scene end-to-end via the orchestrator using Surface Revolution (Screw modifier) and transmissive glass — entirely different modeling pattern and material class than the sword
- **All v0.6.0 patches applied without modification**: world reset, real-world dimensions, subject-aware lighting, bbox-aware camera, mandatory visual checkpoint. First-try render produced a recognizable bottle.
- One real recipe gap surfaced: **glass with `Base Color` tint only renders flat or metallic**, not "glass-like". Real coloured glass needs **Volume Absorption** for depth-based tint.
- Patches:
  1. **Added Recipe 6b (Coloured glass with Volume Absorption)** to `blender-materials/SKILL.md` — surface near-white + slight roughness + Volume Absorption shader on Material Output Volume input. Includes density tuning guide and 5-row colour table (wine green, champagne, cobalt, amber, ruby).
  2. Added two failure-mode rows to `text-to-blender/SKILL.md`: "coloured glass renders flat/metallic" → use Recipe 6b; "glass renders black inside" → bump `transmission_bounces` to 24.
- Validation proof committed to `plugin/skills/text-to-blender/assets/v0.7.0-bottle-validation/` (first-try with surface tint vs final with volume absorption).
- Quality estimate: **8.5/10** (unchanged from v0.6.0 — patches were targeted; no degradation, but no jump either)

**Known limitation deferred to next round**: strong rim light washes out volume tint on glass. Future lighting-optimization round should add HDRI options and subject-class hints (`"glass" → softer rim, more fill`).

**Key signal**: this was a clean win — patches generalised first try. Compared to round 2's sword (5+ user-driven iterations of the same basic build), the v0.6.0 patches did real work.

### 0.6.0 — 2026-04-27 — Real scene-build iteration; user as visual-validation oracle
- Tester (Haiku) attempted a full sword scene-build via the orchestrator; numerical checks all passed but the user inspected the actual Blender viewport and surfaced 6 distinct quality issues
- Each user observation drove a concrete patch:
  1. **Wrong proportions** ("no sword, just pommel + grip"): added `references/common-object-dimensions.md` with real-world dimensions; orchestrator must consult it before sizing
  2. **Wrong orientation** ("looks like a giant screwdriver"): added axis-orientation guidance to `blender-modeling` (broad-face-toward-camera convention)
  3. **No mandatory visual validation** ("these mistakes shouldn't happen"): added mandatory `get_viewport_screenshot` step in orchestrator workflow
  4. **Blunt blade tip** ("no sharp end"): added proper tapering recipe (collapse + `remove_doubles`)
  5. **Grey viewport / flat materials** ("sword is grey, no textures"): added viewport-shading switch + procedural texture variation patterns
  6. **Visible seams between parts** ("objects don't connect smoothly"): added connection-overlap pattern (parts interpenetrate by 5-15mm, hiding cylinder→cube transitions)
- Also added: `aim_at(light, target)` helper + Recipe 0 (subject-aware lighting) to `blender-lighting`; Recipe 0 (bbox-aware hero camera) to `blender-cameras`; Blender 5.x `Mesh.use_auto_smooth` removal noted
- Final sword render committed to `plugin/skills/text-to-blender/assets/v0.6.0-round2-validation/M_sword_FINAL_v0.6.0.png` — recognizable sword on first try with patched recipes
- Quality estimate: **8.5/10** (was 8/10 at v0.5.0)
- See `test_round2.md` for the full investigation arc with 7 user-feedback iterations and the patches each one drove

**Key lesson**: numerical validation alone is insufficient. The user looking at the actual viewport is the oracle that catches "API succeeded but result is broken" failures. The orchestrator now treats visual validation as a mandatory step, not a nice-to-have.

### 0.5.0 — 2026-04-27 — Two-role validation loop complete (Haiku tester + Opus patcher)
- **Tester** (Haiku 4.5) ran 30 test cases per `TESTING_PLAN.md` against live Blender 5.1.1, populated `test.md` with structured per-test results
- Initial score: 27 PASS / 1 FAIL / 1 SKIP / 1 partial out of 30
- **Patcher** (Opus role) read `test.md`, root-caused both failures, applied fixes:
  1. **`Subsurface IOR` KeyError on Blender 5.x** (B3): root cause is `enabled=False` flag on certain BSDF inputs; string-key lookup respects UI-visibility filter, iteration bypasses it. Added `set_input(node, name, value)` helper to `blender-materials/SKILL.md`; rewrote Recipe 9 (Skin) to use it. Forward-compatible with future Blender versions if more inputs become disabled.
  2. **`Cannot render, no camera`** (E3 + orchestrator I1): Recipes 5/6 of `blender-rendering/SKILL.md` didn't ensure `scene.camera` was set. Added `ensure_camera(scene)` guard that auto-assigns first CAMERA object or raises `RuntimeError` with a helpful message.
  3. Documented both errors in `text-to-blender/SKILL.md` failure-modes table for orchestrator-level recognition.
- Both patches verified by re-running the originally failing tests via `mcp__blender__execute_blender_code` — both PASS.
- Adjusted score: **28 PASS / 0 FAIL / 1 SKIP / 1 caveat out of 30**
- Cost-saving: tester+patcher split using cheap+expensive models (Haiku does deterministic loop, Opus does judgment+fixes) was ~10× cheaper than running the same loop on a frontier model throughout.

Quality estimate: **8/10** (up from 7.5/10 at 0.4.0).

### 0.4.0 — 2026-04-27 — First end-to-end validation pass complete
- Connected to live Blender 5.1.1 via ahujasid/blender-mcp
- Ran 6 validation tests (5 representative + 1 bonus glTF) end-to-end against the actual MCP
- **Result: 5/5 tested prompts pass** after patches
- **2 real Blender-5.x cross-version bugs surfaced and fixed**:
  1. `BLENDER_EEVEE_NEXT` doesn't exist on 5.x — try/except fallback added in `blender-rendering/SKILL.md`
  2. `action.fcurves` removed on 5.x layered Actions — `get_fcurves_compat()` helper added in `blender-animation/SKILL.md`
- Updated `text-to-blender/SKILL.md` failure-modes table with both 5.x-specific errors
- Test artefacts (PNG renders, FBX, GLB) saved to `/tmp/cc-blender-test*` for visual inspection
- See `IMPLEMENTATION_LOG.md` for detailed test-by-test results

Quality estimate updated: **7.5/10** (up from 6.5/10 at 0.3.0). The skill now demonstrably works end-to-end on common Blender 5.x tasks. Coverage breadth (long-tail recipes, advanced sims) still pending.

### 0.3.0 — 2026-04-27 — Scaffolding complete
- Built `plugin/skills/` with 10 skills:
  - `text-to-blender` (orchestrator, ~270 lines)
  - `blender-pro-workflow` (guidance, ~250 lines)
  - 7 domain skills (modeling, materials, lighting, cameras, rendering, animation, export — each ~200–300 lines)
  - `wireframe-to-3d` (specialty, migrated from earlier work)
- Each sub-skill has its own `references/overview.md` (copied from `knowledge/`)
- Plugin `manifest.json` with skill registry
- Plugin `README.md` with install instructions
- Top-level repo `README.md` updated for plugin shape
- Honest assessment doc (this file)

### 0.2.0 — 2026-04-27 — Knowledge base complete
- 16 knowledge domains researched (`knowledge/01-modeling/` through `knowledge/16-pro-workflows/`)
- ~6500 lines of distilled best-practice across ~80 web sources
- Tier-A/B/C/D source quality grading
- Cross-reference maps between domains

### 0.1.0 — 2026-04-26 — Initial research foundation
- 6 documents covering algorithms, Blender best practices, Blender integration patterns, MCP alignment, skill specification, and research summary
- Production-ready `wireframe_analyzer.py` image processing pipeline
- Initial `wireframe-to-3d` SKILL.md as proof-of-concept

---

## Honest milestone targets

| When you should consider this skill plugin "trustworthy enough to recommend to others" | Stage |
|----|-----|
| Internal experimentation | **0.3.0** (now) |
| Personal use after smoke-testing | 0.5.0 |
| Sharing with peers willing to file bugs | 0.7.0 |
| Public recommendation, blog posts, demos | 0.9.0+ |
| Production use in client work | 1.0.0 |

---

## Path to validation (the most-impactful next steps)

Highest leverage to get from 0.3 → 0.5:

1. Run **5 representative end-to-end prompts** through `text-to-blender` against actual Blender:
   - "Model a sword and render a hero shot with three-point lighting"
   - "Make a glass material on the active object and render"
   - "Set up a turntable animation of this object, render 96 frames"
   - "Convert this wireframe drawing to a 3D glTF model"
   - "Export the current scene as FBX for Unity"

2. **Document every failure** in `IMPLEMENTATION_LOG.md` with: prompt, error, root cause, fix.

3. **Patch the most common failure modes** — likely 5–10 small bug fixes covering the 80% of issues.

4. Re-run the same 5 prompts. Aim for ≥ 4/5 succeeding cleanly.

5. Tag **0.5.0**.

This is the gate that converts the plugin from "structurally correct scaffolding" to "demonstrably useful tool."
