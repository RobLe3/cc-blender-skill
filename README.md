# cc-blender-skill

A Claude Code skill plugin that lets Claude use Blender like a senior 3D artist via natural language.

**Version**: **1.0.0** — first stable release. Validated end-to-end on Blender 5.1.1 across three scene classes (sword, bottle, chair) plus wireframe-to-3d closure. See [`CHANGELOG.md`](./CHANGELOG.md) for what landed at each version, [`VERSIONING.md`](./VERSIONING.md) for full rationale, and the validation proof renders in [`plugin/skills/text-to-blender/assets/`](./plugin/skills/text-to-blender/assets/).

---

## What this is

Ten chain-loadable Claude Code skills that turn requests like *"model a sword and render a hero shot with three-point lighting"* into Blender Python executed via the [Blender MCP](https://github.com/ahujasid/blender-mcp).

```
User prompt
    ↓
Claude detects intent → loads text-to-blender (orchestrator)
    ↓
Orchestrator chain-loads relevant sub-skills
    ↓ ↓ ↓
modeling, materials, lighting, cameras, rendering, animation, export, wireframe-to-3d, pro-workflow
    ↓
Generated Python → mcp__blender__execute_blender_code → Blender → output
```

The plugin is the actual installable thing. It lives at [`plugin/`](./plugin/). Knowledge research that produced it lives at [`knowledge/`](./knowledge/) and [`docs/`](./docs/).

---

## What works (honestly)

| Capability | Status | Validation |
|------------|--------|------------|
| End-to-end scene build from natural language | ✅ Works first-try on common subjects | sword, bottle, chair scenes (proof renders in `plugin/skills/text-to-blender/assets/`) |
| Real-world dimension lookup | ✅ Reference covers swords, chairs, bottles, mugs, tables, lamps, eyewear | `references/common-object-dimensions.md` |
| Multi-skill chaining | ✅ Validated | wireframe-to-3d → modeling → materials → lighting → camera → render |
| Blender 5.x compat | ✅ Live-validated on 5.1.1 | All known cross-version quirks have try/except or helpers |
| Blender 4.x compat | ⚠️ Compat code present, not directly tested | See `plugin/skills/text-to-blender/references/blender-version-compat.md` |
| Coloured glass / metal / wood / fabric / skin / product subject classes | ✅ Subject-aware lighting profiles | Recipe 0a in `blender-lighting/SKILL.md` |
| Trigger-eval description tuning | ✅ 200 starter queries shipped | Each skill has `evals/evals.json` |
| Wireframe-to-3d auto-extraction | ⚠️ Works for simple line-art (foundation only) | Aviator validated; complex named-design objects need hand-crafted layer on top |

## What doesn't work yet (honestly)

- **Design quality ≠ build correctness.** Plugin produces functionally correct objects. Aesthetic refinement (curved chair backs, profile-cut legs, consciously-composed silhouettes) is human-driven — out of scope for automatic generation.
- **Thin-metal specular flare.** Hero shots of thin metal (eyewear arms, jewellery) catch side lighting as bright streaks. Workaround: top-down softbox lighting or crop temple arms out of the frame.
- **Subjective quality.** Numerical validation passing ≠ render looks right. The orchestrator's mandatory visual-validation checkpoint exists, but the user remains the final oracle.
- **External user feedback.** v1.0.0 is internally-validated only.

---

## Quick install

Prerequisites: Blender ≥ 4.0 with [BlenderMCP addon](https://github.com/ahujasid/blender-mcp) running on port 9876, Claude Code, Python 3.9+ with `opencv-python numpy scipy Pillow`.

```bash
git clone git@github.com:RobLe3/cc-blender-skill.git
cd cc-blender-skill

# Symlink all 10 skills into ~/.claude/skills/
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
│       ├── blender-pro-workflow/     # multi-phase guidance
│       ├── blender-modeling/         # geometry creation
│       ├── blender-materials/        # PBR via Principled BSDF
│       ├── blender-lighting/         # 3-point, HDRI, studio
│       ├── blender-cameras/          # framing, DoF, animated cameras
│       ├── blender-rendering/        # Cycles/EEVEE
│       ├── blender-animation/        # keyframes, F-curves, shape keys
│       ├── blender-export/           # glTF/FBX/OBJ/USD/STL
│       └── wireframe-to-3d/          # specialty: 2D wireframe → 3D
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

## Honest status (v1.0.0)

The plugin shipped through **9 versions of validation and patches** since the v0.3.0 scaffolding. Each version's commit summary in `CHANGELOG.md` records concrete bugs found and fixed; each user-driven feedback iteration is in `VERSIONING.md` with the patch it produced. The proof renders in `plugin/skills/text-to-blender/assets/v0.X.0-validation/` are honest evidence — no cherry-picking, including failure-state renders.

What v1.0.0 means here: **stable enough that the patches won't churn day-to-day**, the recipe vocabulary is settled, and the trigger-evals exist for description tuning. Real external use will surface edge cases that v1.x patches will address.

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
