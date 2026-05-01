# cc-blender-skill

A Claude Code skill plugin that lets Claude use Blender like a senior 3D artist via natural language.

**Version**: **1.3.0** ([CHANGELOG](./CHANGELOG.md)) · adds a generic quality-refinement autoloop, closed-surface texture coverage gates, layered texture/HUD animation QA, and source-locked reconstruction workflows on top of the stable Blender 5.x workflow. The core has been validated end-to-end on Blender 5.1.1 across **6 scene classes** (sword, bottle, chair, aviator, desk lamp, broadcaster avatar) plus wireframe-to-3d closure. Validation proof renders are committed in [`plugin/skills/text-to-blender/assets/`](./plugin/skills/text-to-blender/assets/) (failure-state renders included for honesty — no cherry-picking).

**Quick links**: [Install](#quick-install) · [What works (honestly)](#what-works-honestly) · [What doesn't](#what-doesnt-work-yet-honestly) · [Architecture](#architecture-in-one-paragraph) · [Contributing](.github/CONTRIBUTING.md) · [Releases](https://github.com/RobLe3/cc-blender-skill/releases)

---

## What this is

Thirty chain-loadable Claude Code skills that turn requests like *"model a sword and render a hero shot with three-point lighting"* into Blender Python executed via the [Blender MCP](https://github.com/ahujasid/blender-mcp).

```
User prompt
    ↓
Claude detects intent → loads text-to-blender (orchestrator)
    ↓
Orchestrator chain-loads relevant sub-skills
    ↓ ↓ ↓
modeling, materials, lighting, cameras, rendering, animation, export, wireframe-to-3d, pro-workflow, reference-to-3d, UV/atlas fitting, validation, fit repair, look calibration
    ↓
Generated Python → mcp__blender__execute_blender_code → Blender → output
```

The plugin is the actual installable thing. It lives at [`plugin/`](./plugin/). Knowledge research that produced it lives at [`knowledge/`](./knowledge/) and [`docs/`](./docs/).

---


## What's new in v1.3.0

This release adds a generic self-refinement layer for cases where output quality is below expectation. Instead of blindly retrying, the stack now freezes the artifact, diagnoses the failure dimension, decides whether existing skills are sufficient, sanitizes the lesson into publishable generic guidance, validates the skill graph, and only then repairs the product.

### Added

- `quality-refinement-autoloop` — a RALPH-style loop for subpar outputs, repeated failures, skill-gap diagnosis, sanitization, docs/version prep, and release handoff.
- `closed-surface-uv-coverage` — a hard gate for closed/extruded assets so front caps, back caps, and sidewalls each have real surface coverage rather than overlay-only detail.
- Animation/look motion skills: `texture-state-animation`, `orbital-hud-motion`, and `animation-quality-gate` for registered texture states, source-derived HUD motion, and contact-sheet QA.
- Additional source-driven repair skills: `source-part-segmentation`, `texture-driven-mesh-fitting`, `landmark-fit-repair`, and `multiview-constraint-solver`.

### Changed

- `blender-skill-harmonizer` now routes rejected/subpar outputs through the quality-refinement autoloop before further artifact work.
- UV/texturing guidance now includes closed-surface front/back/side coverage validation.
- README/plugin docs now describe the expanded 30-skill stack and the publishable self-refinement workflow.

---

## What's new in v1.2.9

This release adds a generic, source-driven reconstruction layer on top of the existing natural-language Blender workflow. The important changes are:

### Added

- `blender-skill-harmonizer` — a meta-orchestrator for multi-skill precedence, source-of-truth policy, handoff artifacts, and source-conflict gates.
- `reference-to-3d` — a source-locked reconstruction workflow for templates, reference sheets, texture packs, and orthographic views.
- `reference-analysis-validator` — source manifests, part-count gates, masks, overlays, IoU/SSIM/bbox/centroid validation, and fail-before-export checks.
- `contour-to-mesh` and `orthographic-registration` — silhouette-first mesh construction plus front/side/back/top coordinate contracts.
- `blender-uv-texturing` and `atlas-uv-fitting` — UV projection, atlas-region mapping, decals, lightmaps, and supplemental-map sanity checks.
- `multiview-fit-loop` and `fit-repair-optimizer` — render/compare/adjust loops and dependency-aware repair queues.
- `reference-look-calibration` — measurable source-image look matching for crop, brightness, saturation, hue, accent/glow, materials, lights, and render settings.
- `mascot-logo-reconstruction` — generic brand mascot/logo orchestration driven by `reference_manifest.json`, not hardcoded project assumptions.

### Changed

- Existing production skills now hand off to the reference-locked stack when the user provides source templates, texture packs, or repeated visual mismatch feedback.
- The wireframe workflow now has a correction mode for source/texture-driven subjects instead of continuing primitive-first rebuilds.
- Lighting, material, and rendering skills now defer source-image look matching to `reference-look-calibration` when exact visual match matters.
- Examples and scripts were sanitized so structural counts, accent hues, guide masks, and validation gates are manifest/report-driven and reusable across projects.

---

## What works (honestly)

| Capability | Status | Validation |
|------------|--------|------------|
| End-to-end scene build from natural language | ✅ Works first-try on most common subjects | 6 validated scene classes: sword, bottle, chair, aviator, desk lamp, broadcaster avatar |
| Real-world dimension lookup | ✅ Reference covers 7 categories | swords, chairs, bottles, mugs, tables, lamps, eyewear, characters — `references/common-object-dimensions.md` |
| Multi-skill chaining | ✅ Validated | wireframe-to-3d → modeling → materials → lighting → camera → render → export |
| Blender 5.x compat | ✅ Live-validated on 5.1.1 | All known cross-version quirks have try/except or helpers |
| Blender 4.x compat | ⚠️ Compat code present, not directly tested | See `plugin/skills/text-to-blender/references/blender-version-compat.md` |
| Subject-class lighting (metal / glass / wood / fabric / skin / product) | ✅ Subject-aware profiles | Recipe 0a in `blender-lighting/SKILL.md` |
| Emission material + practical lighting | ✅ Lamp scene validated | Recipe 11b in `blender-materials`, Recipe 0c in `blender-lighting` |
| Volume-absorption coloured glass | ✅ 5 colour types tuned | Recipe 6b in `blender-materials/SKILL.md` |
| Trigger-eval description tuning | ✅ 200 starter queries shipped | Each skill has `evals/evals.json`; aggregate 100% TP / 4% FP |
| Wireframe-to-3d auto-extraction | ⚠️ Works for simple line-art; now has reference-locked correction handoff | Aviator validated; complex designed objects should use the reference-to-3d / contour / registration / validation stack |
| Reference-locked reconstruction | ✅ Workflow added | Source manifest, contour-to-mesh, orthographic registration, multiview fit loop, repair queue, and overlay validation |
| Texture-pack / atlas fitting | ✅ Workflow added | UV projection, per-region atlas mapping, alpha decals, supplemental-map sanity checks, lightmap handling |
| Reference look calibration | ✅ Workflow added | Camera crop, brightness/saturation/hue, accent/glow masks, material/light/render handoff |
| Skill harmonization | ✅ Workflow added | Meta-orchestrator defines precedence, handoff artifacts, source-conflict gates, and sequential/parallel repair lanes |

## What doesn't work yet (honestly)

- **Design quality ≠ build correctness.** Plugin produces functionally correct objects. Aesthetic refinement (curved chair backs, profile-cut legs, consciously-composed silhouettes) is human-driven — out of scope for automatic generation.
- **Human faces from primitives.** A sphere + nose + ears + mouth + brows reads as "abstract avatar," not "human." Real human faces require subtractive sculpting. v1.2.1 documents three escape paths: import via `download_polyhaven_asset` / `download_sketchfab_model` / `generate_hyper3d_model_via_text` (then chain), sculpt mode, or commission an artist (`docs/avatar-design-kit/prompts/04-blender-workflow.md`).
- **Thin-metal specular flare.** Hero shots of thin metal (eyewear arms, jewellery) catch side lighting as bright streaks. Workaround: top-down softbox lighting or crop temple arms out of the frame.
- **Subjective quality.** Numerical validation passing ≠ render looks right. The orchestrator's mandatory visual-validation checkpoint exists, but the user remains the final oracle.
- **External user feedback.** Core validation is internal; the newer reference-locked stack still needs broader external examples, and real-use feedback drives v1.x patches.

---

## Quick install

Prerequisites: Blender ≥ 4.0 with [BlenderMCP addon](https://github.com/ahujasid/blender-mcp) running on port 9876, Claude Code, Python 3.9+ with `opencv-python numpy scipy Pillow`.

```bash
git clone git@github.com:RobLe3/cc-blender-skill.git
cd cc-blender-skill

# Symlink all 30 skills into ~/.claude/skills/
for skill in plugin/skills/*/; do
    name=$(basename "$skill")
    ln -sfn "$(pwd)/$skill" "$HOME/.claude/skills/$name"
done

# Restart Claude Code to pick up the new top-level skills directory entries.
```

Then ask Claude something like:

```
Make a 3D model of a teapot and render it with three-point lighting.
```

Or invoke a specific skill:

```
/wireframe-to-3d ./glasses_front.png
```

Full install + verification: [`plugin/README.md`](./plugin/README.md).

---

## Repository structure

```
cc-blender-skill/
├── README.md                         # this file
├── CHANGELOG.md                      # release notes per version
├── VERSIONING.md                     # full per-version rationale
├── LICENSE                           # MIT
├── requirements.txt
├── .github/                          # CONTRIBUTING + issue templates
│
├── plugin/                           # ← the installable skill plugin
│   ├── README.md
│   ├── manifest.json
│   └── skills/
│       ├── text-to-blender/          # orchestrator
│       ├── blender-skill-harmonizer/ # multi-skill precedence + handoff contracts
│       ├── quality-refinement-autoloop/ # RALPH-style quality loop + release prep
│       ├── blender-pro-workflow/     # multi-phase guidance
│       ├── blender-modeling/         # geometry creation
│       ├── blender-materials/        # PBR via Principled BSDF
│       ├── blender-lighting/         # 3-point, HDRI, studio
│       ├── blender-cameras/          # framing, DoF, animated cameras
│       ├── blender-rendering/        # Cycles/EEVEE
│       ├── blender-animation/        # keyframes, F-curves, shape keys
│       ├── blender-export/           # glTF/FBX/OBJ/USD/STL
│       ├── wireframe-to-3d/          # specialty: 2D wireframe → 3D
│       ├── reference-to-3d/          # source-locked reconstruction
│       ├── reference-analysis-validator/ # masks, metrics, overlays
│       ├── contour-to-mesh/          # contour-derived mesh generation
│       ├── orthographic-registration/ # front/side/back/top coordinate contract
│       ├── blender-uv-texturing/     # UV, projection, baking, lightmaps
│       ├── atlas-uv-fitting/         # per-part atlas/decal mapping
│       ├── closed-surface-uv-coverage/ # front/back/side surface coverage audits
│       ├── mascot-logo-reconstruction/ # generic brand mascot/logo workflow
│       ├── multiview-fit-loop/       # render/compare/adjust validation loop
│       ├── fit-repair-optimizer/     # dependency-aware repair queues
│       ├── reference-look-calibration/ # source-image look matching
│       ├── source-part-segmentation/ # per-part source masks
│       ├── texture-driven-mesh-fitting/ # mesh boundaries fit texture/source contours
│       ├── landmark-fit-repair/      # named feature repair gates
│       ├── texture-state-animation/  # layered registered texture motion
│       ├── orbital-hud-motion/       # source-derived HUD/circle motion
│       └── animation-quality-gate/   # contact-sheet animation QA
│
├── knowledge/                        # raw research aggregation (16 domains)
│   ├── README.md
│   ├── 01-modeling/00-overview.md
│   ├── 02-curves-surfaces/00-overview.md
│   ├── 03-sculpting-retopo/00-overview.md
│   ├── 04-geometry-nodes/00-overview.md
│   ├── 05-materials-shading/00-overview.md
│   ├── 06-uv-texturing/00-overview.md
│   ├── 07-lighting/00-overview.md
│   ├── 08-cameras-composition/00-overview.md
│   ├── 09-animation/00-overview.md
│   ├── 10-rigging/00-overview.md
│   ├── 11-rendering/00-overview.md
│   ├── 12-compositing/00-overview.md
│   ├── 13-physics-particles/00-overview.md
│   ├── 14-import-export/00-overview.md
│   ├── 15-cross-cutting/00-overview.md
│   └── 16-pro-workflows/00-overview.md
│
├── docs/                             # documentation
│   ├── SKILL_FOUNDATION.md           # original research
│   ├── BLENDER_BEST_PRACTICES.md
│   ├── BLENDER_INTEGRATION_GUIDE.md
│   ├── BLENDER_MCP_ALIGNMENT.md
│   ├── WIREFRAME_SKILL.md
│   ├── SKILL_RESEARCH_SUMMARY.md
│   ├── process/                      # dev journals (planning, tests, mcp coverage)
│   │   ├── PLAN.md
│   │   ├── DEVELOPMENT.md
│   │   ├── TESTING_PLAN.md
│   │   ├── IMPLEMENTATION_LOG.md
│   │   ├── VERIFICATION_REPORT.md
│   │   ├── MCP_COVERAGE_ASSESSMENT.md
│   │   ├── BLENDER_TOOLKIT_COMPARISON.md
│   │   └── INSTALL_BLENDER_MCP.md
│   └── test-results/                 # per-round eval logs
│       ├── test.md                   # round 1: 30-test smoke
│       ├── test_round2.md            # round 2: scene-build feedback loop
│       └── test_round3.md            # round 3: trigger-eval self-assessment
│
├── src/                              # original wireframe analyzer (still used by skill)
│   └── wireframe_analyzer.py
│
└── skill/                            # initial single-skill prototype (now superseded by plugin/)
    └── wireframe-to-3d/
```

---

## Architecture in one paragraph

Pure-skill design — no Python wrapper class, no custom MCP. Claude itself orchestrates: reads the user's intent, loads sub-skills via `Read`, generates Blender Python, calls `mcp__blender__execute_blender_code` (the synchronous socket on port 9876), parses stdout, and reports results. State lives in `bpy.data` (Blender's global state, persists between calls); Python variables don't (each `execute_blender_code` is a fresh namespace, so we identify objects by stable name like `bpy.data.objects['GEO-sword']`). Naming follows Blender Studio conventions (`GEO-`, `MAT-`, `LGT-` prefixes). Each sub-skill stays under 500 lines (the Anthropic skills cap) and points to a deeper `references/overview.md` for the long tail.

---

## Why this exists

There are already two Claude+Blender skills:

- **[ra100/blender-claude-plugin](https://github.com/ra100/blender-claude-plugin)** — 8 generalist Blender API reference skills (geometry nodes, shader nodes, compositor, etc.). Teaches Claude *how* Blender works.
- **[Dev-GOM/blender-toolkit](https://mcpmarket.com/tools/skills/blender-toolkit)** — Mixamo retargeting via custom WebSocket addon.

Neither tackles the **task-level orchestration**: "given a natural-language request, produce a finished 3D output." That's what this plugin does. It depends on `ahujasid/blender-mcp` (the same MCP both other skills can also work with) and adds:

- Pro-workflow sequencing (block-out → camera → lighting → forms → materials → detail → render → composite → export)
- Recipe libraries per domain with copy-paste-ready Python
- Decision trees mapped to natural-language intent
- Naming and validation conventions throughout

See [`docs/process/BLENDER_TOOLKIT_COMPARISON.md`](./docs/process/BLENDER_TOOLKIT_COMPARISON.md) for the full landscape comparison.

---

## Honest status

The plugin shipped through **15+ versions of validation and patches** since the v0.3.0 scaffolding, then expanded with a generic reference-locked reconstruction stack for source/template/texture-driven work. Each version's commit summary in [`CHANGELOG.md`](./CHANGELOG.md) records concrete bugs found and fixed; each user-driven feedback iteration is in [`VERSIONING.md`](./VERSIONING.md) with the patch it produced. The proof renders in [`plugin/skills/text-to-blender/assets/v0.X.0-validation/`](./plugin/skills/text-to-blender/assets/) are honest evidence — no cherry-picking, including failure-state renders.

The validation pattern is documented in [`docs/process/TESTING_PLAN.md`](./docs/process/TESTING_PLAN.md): cheap-Haiku tester runs deterministic tests + writes structured results, expensive-Opus patcher reads them and applies fixes. ~10× cheaper than running the full loop on a frontier model throughout. Three round logs live in [`docs/test-results/`](./docs/test-results/).

### What v1.2.9 adds

- Generic `blender-skill-harmonizer` meta-layer for multi-skill precedence, source-of-truth policy, and handoff artifacts.
- Source-locked reconstruction stack: `reference-to-3d`, `reference-analysis-validator`, `orthographic-registration`, `contour-to-mesh`, `multiview-fit-loop`, and `fit-repair-optimizer`.
- Texture workflow expansion: `blender-uv-texturing` plus `atlas-uv-fitting` for texture packs, decals, UV regions, and supplemental map sanity checks.
- `reference-look-calibration` for measurable source-image look matching after geometry/UV gates pass.
- Generic mascot/logo workflow that derives structural counts and visual constraints from `reference_manifest.json` instead of hardcoded project assumptions.

What v1.2.9 means here: **the stable core remains intact**, scope boundaries (design quality, human faces, thin-metal flare) are documented with escape paths, and the new reference-locked stack is generic, manifest-driven, and ready for broader examples. Real external use will surface edge cases that incremental v1.x patches will address.

---

## Contributing

Open issues / PRs at https://github.com/RobLe3/cc-blender-skill — especially welcome:

- Validation runs ("I tried prompt X, got error Y")
- Recipe contributions for the long tail (specific materials, lighting setups, camera moves)
- Trigger-eval JSON files for any sub-skill (helps tune description triggering)
- Worked example scenes with proof-renders

---

## License

MIT.

## Author

[RobLe3](https://github.com/RobLe3) with extensive collaboration with Claude (Sonnet 4.6, Opus 4.7, Haiku 4.5).
