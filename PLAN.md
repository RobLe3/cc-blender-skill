# Plan — Text-to-Blender Skill Plugin

**Date**: 2026-04-27
**Vision**: Let Claude use Blender like a senior 3D artist, driven entirely by natural language.

---

## What "use Blender like a Pro" actually means

A pro doesn't just call API functions — they make hundreds of small expert decisions:

| Decision | Pro answer | Amateur answer |
|----------|-----------|----------------|
| Modifier order? | Bevel before SubSurf, Mirror before Array, Subsurf last on most stacks | Whatever the tutorial said |
| Topology for animation? | Edge loops around joints; quad-dominant; minimal poles | Triangulated soup |
| PBR for brushed steel? | Metallic 1.0, Roughness 0.25, anisotropy on tangent | Diffuse + specular guess |
| Lighting for product shot? | Three-point + HDRI fill, key:fill ratio 4:1, rim from behind | One sun lamp |
| Cycles or EEVEE? | EEVEE for previews/cartoon, Cycles for hero shots/physically accurate | Whichever is faster today |
| Topology for subdivision? | Quads only, edge crease for sharp features | N-gons everywhere |
| UV unwrap strategy? | Pelt for organics, project-from-view for hard-surface | Auto-unwrap and pray |
| Render samples? | 256 + denoise for indoor, 64 + denoise for outdoor | 4096 always |
| File organization? | `GEO-`, `MAT-`, `LGT-` prefixes, suffixes for symmetry | `Cube.001`, `Material.012` |

A useful skill encodes these decisions as **patterns + decision trees**, not API documentation.

---

## Scope of a "text-to-Blender" plugin

### 12 capability domains

| # | Domain | Example natural-language input |
|---|--------|-------------------------------|
| 1 | **Modeling — primitives + edits** | "Create a 6-sided dice with rounded corners and inset numbers" |
| 2 | **Modeling — curves + lofting** | "Build aviator sunglasses from these wireframes" *(our existing skill)* |
| 3 | **Modeling — sculpting + retopo** | "Sculpt a stylized rock, then retopologize for animation" |
| 4 | **Modeling — geometry nodes** | "Procedurally generate a forest of pine trees on this terrain" |
| 5 | **Materials + shading** | "Make it brushed copper with verdigris in the recesses" |
| 6 | **UV unwrapping + texturing** | "Unwrap this mesh and bake a 2K diffuse map" |
| 7 | **Lighting** | "Three-point studio setup with an HDRI fill, magenta rim" |
| 8 | **Cameras + composition** | "Hero shot, 85mm lens, slight Dutch angle, depth of field on the focal point" |
| 9 | **Animation** | "Spin the object slowly with a 6-second loop" |
| 10 | **Rigging** | "Rig this character with IK arms and FK spine" |
| 11 | **Rendering + compositing** | "Render at 1080p with 256 samples, color-grade for a sunset mood" |
| 12 | **Import/export + optimization** | "Export this scene as glTF, polycount under 30k, textures 1024×1024" |

### Cross-cutting concerns

- **Naming conventions** (Blender Studio standards: `GEO-`, `MAT-`, `.L`/.R)
- **Non-destructive workflow** (modifiers stay editable, isolated collections)
- **Performance** (`foreach_set`, batch ops, modifier order)
- **File organization** (collections, libraries, linking)

---

## Architecture options — pick one

### Option A — Single mega-skill `text-to-blender`
Everything in one `SKILL.md` with progressive disclosure.

- ✅ One install, one entrypoint, one slash command
- ❌ SKILL.md will easily blow past the 500-line cap; cramming 12 domains into one decision tree gets unwieldy
- ❌ Hard for Claude to know which domain to focus on
- ❌ Slow to evolve (every change touches one big file)

### Option B — Plugin of N domain skills (mirrors ra100/blender-claude-plugin)
One skill per domain, each with its own `SKILL.md` + `references/` + `scripts/`.

- ✅ Each skill stays under 500 lines and stays focused
- ✅ Claude auto-loads only the relevant ones based on user intent
- ✅ Easy to add/remove/update one domain without touching others
- ✅ Aligns with how the existing ra100 plugin is structured (proven pattern)
- ❌ More files, more maintenance
- ❌ User has to install/update 12 things (mitigated by packaging as one plugin)

### Option C — Orchestrator skill + N domain skills (recommended)
A top-level `text-to-blender` skill is the entrypoint. It:
1. Parses user intent.
2. Decides which domain skill(s) to invoke.
3. Sequences them (e.g., model → material → light → render).
4. Falls back to direct `execute_blender_code` for one-off needs.

The 12 domain skills do the deep work; the orchestrator owns the cross-domain workflow.

- ✅ Best of both: focused sub-skills + unified text entrypoint
- ✅ Allows multi-step pipelines ("model AND material AND render this")
- ✅ Each sub-skill is independently testable
- ❌ More design work upfront

**Recommendation: Option C.** It's how senior artists actually work — they don't think "I'm using the modeling skill"; they think "I'm building a scene" and switch between modeling/lighting/rendering as the task dictates. The orchestrator mirrors that.

---

## Should we build on top of ra100/blender-claude-plugin or start fresh?

| Question | Build on ra100 | Start fresh |
|----------|---------------|-------------|
| Reference material (how nodes/modifiers work) | Already done by ra100 | Have to write ourselves |
| Task-level recipes ("make brushed copper") | Mostly missing | Have to write ourselves |
| Naming/structure control | Inherited | Ours |
| Skill we want to ship: text-to-Blender orchestrator + task recipes | Layered on top | Bundled together |
| Risk of upstream breaking changes | Real | None |

**Recommendation: depend on ra100/blender-claude-plugin for reference material, build our own orchestrator + task-recipe skills on top.** Don't rewrite ~600 nodes of geometry-nodes documentation that already exists. Focus our effort on the layer that's missing: pro-level task recipes and the text-driven orchestrator.

If ra100's plugin proves unstable or directionally wrong over time, we can fork their references into our repo. Until then, we layer.

---

## Phased delivery — what to build first

Build the skills with the **highest leverage per line of effort**, not the encyclopedic ones:

### Phase 1 — Foundation (1 week)
- [x] `wireframe-to-3d` (existing) — specialized image→model task
- [ ] `text-to-blender` (orchestrator) — entrypoint, intent parsing, routing
- [ ] `blender-modeling-recipes` — primitives, common shapes, hard-surface patterns
- [ ] `blender-material-recipes` — 30 ready-to-use PBR recipes (steel, copper, glass, plastic, etc.)

These four cover ~60% of "make me a 3D model of X" requests.

### Phase 2 — Look development (1 week)
- [ ] `blender-lighting-recipes` — 3-point, HDRI, studio, outdoor, dramatic
- [ ] `blender-camera-composition` — focal lengths, framing, DoF
- [ ] `blender-rendering` — Cycles vs EEVEE decision tree, sample counts, denoising

After Phase 2: "make me a render of X" works end-to-end.

### Phase 3 — Animation & optimization (1 week)
- [ ] `blender-animation-basics` — keyframes, F-curves, easing, drivers
- [ ] `blender-export-optimization` — glTF, FBX, Decimate strategy, texture baking

### Phase 4 — Advanced procedural (optional, 1+ weeks)
- [ ] `blender-geometry-nodes-recipes` — common procedural patterns (scatter, instancing, parametric)
- [ ] `blender-rigging-basics` — armatures, weight paint, IK
- [ ] `blender-compositing-recipes` — post-processing presets

### Phase 5 — Specialized verticals (as needed)
- [ ] `blender-architectural-viz`
- [ ] `blender-character-design`
- [ ] `blender-product-rendering`
- [ ] `blender-game-asset-export`

The goal of Phases 1–3 is a usable text-to-Blender skill that handles the 80% of common requests. Phases 4–5 chase the long tail.

---

## The skill recipe — what each domain skill should contain

Every domain skill follows the same template. Concrete shape:

```
blender-material-recipes/
├── SKILL.md (≤ 500 lines)
│   ├── Frontmatter: name, description (pushy), allowed-tools
│   ├── When to use this skill
│   ├── Decision tree (which recipe for which intent)
│   ├── 5–10 most common recipes inline (with full code)
│   └── Pointers to references/ for the long tail
├── scripts/
│   └── (optional helpers — e.g., bake.py)
└── references/
    ├── recipes-metals.md       (15 metal recipes: steel, copper, gold, …)
    ├── recipes-organics.md     (skin, leaf, fabric, leather)
    ├── recipes-glass.md        (clear, frosted, tinted, mirror)
    └── recipes-plastics.md     (matte, glossy, translucent, rubber)
```

**Each recipe is a self-contained Python block** that Claude can paste into `mcp__blender__execute_blender_code`. No abstraction layer, no template engine — just copy-paste-able expert code with clear parameters at the top.

---

## Repo restructure proposal

```
cc-blender-skill/                       (the user's GitHub repo)
├── README.md                           (top-level: what's the plugin, how to install)
├── PLAN.md                             (this file)
├── docs/
│   ├── architecture/                   (decisions, rationale)
│   ├── skill-development/              (how to add a new domain skill)
│   └── archive/                        (original wireframe-only research)
└── plugin/                             (the actual plugin — what users install)
    ├── README.md                       (skills inside this plugin)
    ├── manifest.json                   (Claude plugin metadata)
    └── skills/
        ├── text-to-blender/            (orchestrator)
        ├── wireframe-to-3d/            (existing — already good)
        ├── blender-modeling-recipes/   (Phase 1)
        ├── blender-material-recipes/   (Phase 1)
        ├── blender-lighting-recipes/   (Phase 2)
        ├── blender-camera-composition/ (Phase 2)
        ├── blender-rendering/          (Phase 2)
        ├── blender-animation-basics/   (Phase 3)
        └── blender-export-optimization/(Phase 3)
```

The current `skill/wireframe-to-3d/` becomes `plugin/skills/wireframe-to-3d/` and remains untouched. We add siblings.

---

## What I need from you to proceed

Three decision points that change the work:

**1. Architecture: A, B, or C?**
Default recommendation: **C** (orchestrator + sub-skills).

**2. Build on ra100 or start fresh?**
Default recommendation: **build on top** — depend on ra100 for reference material; we own orchestrator + task recipes. Skip if you'd rather own everything.

**3. Which Phase 1 skills should I write first?**
The four in Phase 1 are: `text-to-blender` orchestrator, `blender-modeling-recipes`, `blender-material-recipes`, plus the existing `wireframe-to-3d`. If you want a different starting set, say so.

If you say "go", I'll build Phase 1 (~1 week of work, ~3-4 commits) starting with the orchestrator and material recipes (highest leverage).

---

## Honest scope estimate

| Phase | Skills | Effort | Capability after |
|-------|--------|--------|------------------|
| 1 | 4 | ~1 week | "Model a thing, give it materials" works |
| 2 | +3 | ~1 week | Full render pipeline works |
| 3 | +2 | ~1 week | Animation + clean export works |
| 4 | +3 | ~1+ weeks | Procedural + rigging + post |
| 5 | varies | open-ended | Vertical specialties |

**To be a credible "text-to-Blender pro" skill: complete Phases 1–3 (~3 weeks).** That's a usable, real skill.

Anything less than Phase 2 leaves big gaps (no lighting, no render). Anything past Phase 3 is incremental polish.

This is honest. The original wireframe-to-3D was a 2-day project. The full ambition is closer to 3 weeks of focused work, possibly more if recipes need tuning per Blender version.

---

## What stays from the existing work

Nothing wasted. Everything we've built either:
- **Stays as-is** — `wireframe-to-3d` is one specialized skill in the new plugin
- **Becomes the foundation for `blender-modeling-recipes`** — `BLENDER_BEST_PRACTICES.md` and `BLENDER_INTEGRATION_GUIDE.md` already cover modeling patterns
- **Informs the orchestrator** — `VERIFICATION_REPORT.md` and `MCP_COVERAGE_ASSESSMENT.md` document hard architectural facts that shape every sub-skill

The shift is from "ship one skill" to "ship a plugin with this skill as one of N." The work to date is not redone; it's reframed.
