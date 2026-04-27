# Blender Knowledge Base — Raw Research Aggregation

**Purpose**: Aggregate maximum useful knowledge about using Blender like a pro from authoritative web sources, before distilling it into Claude Code skills.

**Workflow**:
1. **Accumulate** raw knowledge here (this folder), organized by domain.
2. **Cross-reference** sources, compare conflicting advice, flag consensus.
3. **Distill** into skill `references/` and `SKILL.md` decision logic in `plugin/skills/`.

This folder is the *raw materials warehouse*. The `plugin/skills/` folder is the *finished products*.

---

## 16 Knowledge Domains

| # | Domain | Lead skill it feeds | Status |
|---|--------|--------------------|--------|
| 01 | Modeling — primitives, mesh ops | `blender-modeling-recipes` | empty |
| 02 | Curves + surfaces | `wireframe-to-3d`, `blender-modeling-recipes` | partial (existing) |
| 03 | Sculpting + retopology | `blender-modeling-recipes` | empty |
| 04 | Geometry nodes (procedural) | `blender-geometry-nodes-recipes` | empty |
| 05 | Materials + shading (PBR, procedural) | `blender-material-recipes` | empty |
| 06 | UV unwrapping + texturing + baking | `blender-material-recipes` | empty |
| 07 | Lighting (3-point, HDRI, studio) | `blender-lighting-recipes` | empty |
| 08 | Cameras + composition | `blender-camera-composition` | empty |
| 09 | Animation (keyframes, F-curves, drivers) | `blender-animation-basics` | empty |
| 10 | Rigging (armatures, IK/FK, weight paint) | `blender-rigging-basics` | empty |
| 11 | Rendering (Cycles, EEVEE, samples, denoising) | `blender-rendering` | empty |
| 12 | Compositing + post-processing | `blender-compositing-recipes` | empty |
| 13 | Physics + particles (rigid body, cloth, fluid, hair) | future | empty |
| 14 | Import/export (glTF, FBX, OBJ, USD) | `blender-export-optimization` | partial (existing) |
| 15 | Cross-cutting: naming, organization, performance | every skill | partial (existing) |
| 16 | Pro workflows: actual production patterns | `text-to-blender` orchestrator | empty |

## Knowledge file format

Each domain folder collects research files:

```
05-materials-shading/
├── 00-overview.md              ← canonical summary, distilled
├── canonical-sources.md        ← URLs we trust, with rationale
├── recipes/
│   ├── steel-brushed.md        ← one recipe per file: PBR values + Python code
│   ├── copper-verdigris.md
│   └── glass-frosted.md
├── decision-trees/
│   └── which-material-for-X.md ← intent → recipe mapping
└── raw-research/
    ├── 2026-04-27-search-pbr-recipes.md   ← timestamped raw search dumps
    └── 2026-04-27-search-procedural.md
```

**Why this layout?**
- `raw-research/` keeps original web findings, dated, so we can verify claims later.
- `recipes/` are atomic, copy-pasteable, with full code.
- `decision-trees/` capture the "when to use which" logic that pros internalize.
- `00-overview.md` is the distilled-but-not-yet-skill version — feeds `SKILL.md`.

## Source quality tiers

| Tier | Examples | Trust |
|------|----------|-------|
| **A** — Official | docs.blender.org, developer.blender.org, Khronos glTF spec, ISO standards | Authoritative |
| **B** — Studio/Foundation | studio.blender.org, Blender Cloud, Blender Foundation | Authoritative |
| **C** — Established educators | Blender Guru, CG Cookie, Grant Abbitt, FlippedNormals, Polygon Runway | High-trust |
| **D** — Community + Q&A | Blender StackExchange, Blender Artists, /r/blender, devtalk.blender.org | Useful but verify |
| **E** — Tutorials, blogs | Medium articles, individual YouTubers | Use for patterns, verify claims |

We weight Tier A/B over D/E. Where authoritative sources disagree, we record both.

## Search batching strategy

To avoid burning API budget, we research in batches of related queries. A batch hits one domain with 4–8 searches covering:
1. Authoritative documentation (Tier A/B)
2. Pro-level best practices (Tier C/D)
3. Common pitfalls / anti-patterns
4. Recipe / pattern collections
5. Performance optimization
6. Recent changes / version-specific notes

Then we read the most-cited specific resources via WebFetch.

## Distillation gates

Before research becomes a skill recipe:

1. **Verified by ≥2 sources** at Tier B+ or **1 source** at Tier A.
2. **Has working Python code** (or convertible to one).
3. **Tested in Blender 5.x** (or flagged as untested).
4. **Documented decision criteria** (when to use this vs alternatives).
5. **Sized correctly** — recipe stays under ~50 lines or it's split.

Recipes that don't pass all 5 gates stay in `raw-research/` until they do.
