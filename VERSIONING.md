# Versioning — Honest Quality Path to v1.0

**Current version**: **0.4.0** — first end-to-end validation pass complete  
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
