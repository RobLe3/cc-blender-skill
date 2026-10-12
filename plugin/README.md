# cc-blender-skill — Plugin

A portable skill pack that lets Codex, Claude Code, and compatible agent hosts use Blender like a senior 3D artist through natural language.

**Version**: 1.4.0 (quality-refinement autoloop, closed-surface coverage, animation QA, source-locked reconstruction, UV/atlas fitting, validation, repair optimization, and look calibration — see [VERSIONING.md](../VERSIONING.md))

---

## What's in this plugin

30 chain-loadable skills:

| Skill | Role | What it does |
|-------|------|--------------|
| `text-to-blender` | Orchestrator | Top-level entry; routes natural-language to sub-skills |
| `blender-pro-workflow` | Guidance | Multi-phase pipeline guidance (assembly order, critique) |
| `blender-modeling` | Domain | Mesh creation, hard-surface, modifier stacks |
| `blender-materials` | Domain | PBR materials, Principled BSDF, procedural |
| `blender-lighting` | Domain | Three-point, HDRI, studio/cinematic |
| `blender-cameras` | Domain | Focal length, DoF, composition, animated cameras |
| `blender-rendering` | Domain | Cycles/EEVEE, samples, denoising, color management |
| `blender-animation` | Domain | Keyframes, F-curves, shape keys, drivers, NLA |
| `blender-export` | Domain | glTF/FBX/OBJ/USD/STL with target settings |
| `wireframe-to-3d` | Specialty | Convert 2D wireframe images to parametric 3D models |
| `blender-skill-harmonizer` | Orchestrator | Resolve multi-skill precedence, handoff contracts, and source-of-truth conflicts |
| `quality-refinement-autoloop` | Orchestrator | RALPH-style failure loop: diagnose, sanitize, patch skills, validate, and prep release |
| `reference-to-3d` | Specialty | Source/template/texture-locked reconstruction workflow |
| `reference-analysis-validator` | Specialty | Source manifests, masks, overlays, IoU/SSIM/bbox/centroid gates |
| `contour-to-mesh` | Specialty | Build mesh surfaces directly from extracted contours/masks |
| `orthographic-registration` | Specialty | Register front/side/back/top references into one coordinate contract |
| `blender-uv-texturing` | Domain | UV unwrap/projection, baking, decals, lightmaps, GLB texture setup |
| `atlas-uv-fitting` | Specialty | Detect atlas/decal regions and map each part to correct UV rectangles |
| `mascot-logo-reconstruction` | Orchestrator | Generic fail-gated brand mascot/logo reconstruction from references/textures |
| `multiview-fit-loop` | Specialty | Render/compare/adjust/re-render validation across orthographic templates |
| `fit-repair-optimizer` | Specialty | Convert failed validation reports into dependency-aware repair queues |
| `reference-look-calibration` | Specialty | Match material/light/render/glow look to source images with measurable metrics |
| `multiview-constraint-solver` | Specialty | Resolve front/side/back/top feasibility and canonical view policy |
| `closed-surface-uv-coverage` | Specialty | Audit and enforce front/back/side surface texture coverage on closed assets |
| `source-part-segmentation` | Specialty | Segment overlapping source/template/atlas parts into structural masks |
| `texture-driven-mesh-fitting` | Specialty | Fit mesh boundaries to source/texture contours before UV/material work |
| `landmark-fit-repair` | Specialty | Validate and repair named tips, corners, face features, and depth markers |
| `texture-state-animation` | Specialty | Registered layered texture/material state animation without bad whole-image crossfades |
| `orbital-hud-motion` | Specialty | Source-derived circular/HUD/aura motion design |
| `animation-quality-gate` | Specialty | Contact-sheet QA for motion, morph, texture coherence, and export truth |

---

## Install

### Prerequisites

1. **A configured MCP backend:** official Blender Lab MCP with Blender ≥5.1, or the existing [ahujasid add-on/server](https://github.com/ahujasid/blender-mcp) with Blender ≥4.0. Both require an add-on socket and a separate client MCP process.
2. **A compatible agent host** with SKILL.md discovery, file and shell tools, image inspection, and MCP support. Codex and Claude Code have documented setups below.
3. **Python 3.9+** with `opencv-python`, `numpy`, `scipy`, `Pillow` (only needed for `wireframe-to-3d` — install with `pip install -r ../requirements.txt`).

### Choose a backend

Read [the backend setup/mapping reference](skills/text-to-blender/references/mcp-backends.md)
before configuring the client. A single backend uses server name `blender`.
For both, keep ahujasid as `blender` on port 9876 and add official MCP as
`blender_official` on port 9877. Keep their Python environments separate because
both upstream packages install an executable named `blender-mcp`.

Official MCP is preferred for common operations. Legacy-only asset tools select
ahujasid for the whole task; an explicit user backend choice takes precedence.
These instructions do not authorize changing an existing client configuration.

### Install in Codex

Codex discovers personal skills in `~/.agents/skills/` and project skills in `.agents/skills/`. Symlink the pack without replacing an existing skill:

```bash
cd /path/to/cc-blender-skill
mkdir -p "$HOME/.agents/skills"
for skill in plugin/skills/*/; do
    name=$(basename "$skill")
    test ! -e "$HOME/.agents/skills/$name" && test ! -L "$HOME/.agents/skills/$name" || {
        echo "Refusing to replace $name" >&2; exit 1;
    }
done
for skill in plugin/skills/*/; do
    name=$(basename "$skill")
    ln -s "$(pwd)/$skill" "$HOME/.agents/skills/$name"
done
```

For one project, run the same loop with the destination set to
`/path/to/project/.agents/skills`. In Codex, inspect `/skills`, invoke the
orchestrator as `$text-to-blender`, or describe the Blender task directly.

### Install in Claude Code

Claude Code uses `~/.claude/skills/` for personal scope and `.claude/skills/` for
project scope:

```bash
mkdir -p "$HOME/.claude/skills"
for skill in plugin/skills/*/; do
    name=$(basename "$skill")
    test ! -e "$HOME/.claude/skills/$name" && test ! -L "$HOME/.claude/skills/$name" || {
        echo "Refusing to replace $name" >&2; exit 1;
    }
done
for skill in plugin/skills/*/; do
    name=$(basename "$skill")
    ln -s "$(pwd)/$skill" "$HOME/.claude/skills/$name"
done
```

The optional `allowed-tools` frontmatter is a Claude-specific advisory. Other
hosts must use their own permissions and tool names. See the full
[agent-host guide](skills/text-to-blender/references/agent-hosts.md), including
Codex TOML examples and project-scoped installation.

### Verify installation

List the host's available skills (`/skills` in Codex) and confirm all 30 appear.
Then confirm Blender is running with the selected MCP add-on enabled and that the
host exposes that server's tools.

Do not treat successful discovery as an MCP connection test; exercise a harmless
scene query before modifying a real file.

---

## Use

### Auto-invocation (preferred)

Just describe what you want in natural language:

```
Make a 3D model of a teapot and render it with three-point lighting.
```

The agent detects the intent, loads `text-to-blender`, then loads `blender-modeling` + `blender-materials` + `blender-lighting` + `blender-rendering` and executes the pipeline through the selected Blender MCP.

### Explicit invocation

In Codex, use `$<skill-name>` directly:

```
$wireframe-to-3d ./glasses_front.png
$blender-lighting set up dramatic three-point for the active subject
$blender-export glb /tmp/output.glb
```

Claude Code uses its corresponding skill invocation syntax.

---

## How the skills compose

The orchestrator `text-to-blender` reads the user's intent and decides which sub-skills to chain-load. Each sub-skill uses progressive disclosure and points to its own `references/overview.md` for depth on edge cases.

```
User: "Hero shot of a sword on a stone pedestal, exported as glTF"
                              │
                              ▼
                       text-to-blender (orchestrator)
                              │
              ┌───────────────┼─────────────┬─────────────┬────────────────┐
              ▼               ▼             ▼             ▼                ▼
     blender-pro-workflow   blender-     blender-     blender-       blender-
     (sequencing)           modeling     materials    lighting       rendering
                              │             │             │             │
                              └─────► blender-cameras ◄─────────────────┘
                                          │
                                          ▼
                                  blender-export (glTF)
                                          │
                                          ▼
                                   /tmp/sword_hero.glb
```

---

## Architecture

- **Pure-skill design**: no Python wrapper and no custom MCP. The host agent orchestrates markdown decision trees and inline code recipes.
- **Generated Python via `mcp__blender__execute_blender_code`**: each call is a fresh namespace. Objects identified by `bpy.data.objects['name']`, never by Python variables.
- **Naming convention**: `GEO-`, `MAT-`, `LGT-`, `CAM-`, `ARM-`, `COL-` prefixes (Blender Studio standard).
- **MCP transport**: selected backend's MCP process → add-on TCP socket. Keep backend selection fixed for the task; consult the shared mapping for signatures, response status, timeouts, and render paths.

See `../docs/` for full architecture notes, MCP coverage assessment, and verification report.

---

## Coexistence with other Blender skills

This plugin coexists peacefully with:

- [`ra100/blender-claude-plugin`](https://github.com/ra100/blender-claude-plugin) — generalist Blender API reference skills (geometry nodes, shader nodes, compositor). Install both for the broadest coverage.
- [`Dev-GOM/blender-toolkit`](https://mcpmarket.com/tools/skills/blender-toolkit) — specialty Mixamo retargeting via a separate WebSocket addon (port 9400+, different from ahujasid's :9876). Both can run simultaneously.

---

## Status & honest version

**1.4.0** — additive dual-backend/collision/Multires support on top of the stable core plus generic quality-refinement autoloop, closed-surface coverage, animation QA, and reference-locked reconstruction workflows. The skill structure follows the skills spec, the architecture is verified against Blender MCP usage, and the new source-driven stack avoids hardcoded project assumptions by deriving counts, masks, hues, and validation gates from manifests/reports.

What's NOT done yet:
- Full 225-query and ten-scenario native routing matrices in both Codex and Claude Code
- More external validation on diverse non-mascot source sheets
- Trigger-eval expansion for the newly added skills
- Recipe library expansion in long-tail areas (geometry nodes recipes, sculpting, complex sims)
- More worked example scenes with proof-renders in `assets/`

See [VERSIONING.md](../VERSIONING.md) for release history and validation rationale.

---

## Reporting issues

Open issues at: https://github.com/RobLe3/cc-blender-skill/issues

Include:
- Which skill triggered (or didn't)
- Agent/client and version, especially Codex or Claude Code
- Your Blender version
- Your selected MCP backend/server/add-on versions
- Whether the skill was selected automatically or invoked explicitly
- Whether the skills were installed at personal or project scope
- The full prompt + agent response (or refusal), with the host/client named
- Sanitized error output and a render when the failure is visual

For v1.4.0, Claude Code discovery/routing, the complete trigger/backend scenario
matrix, Unreal imports, and Blender versions outside 5.1.1 remain open validation
areas. Reports and focused PRs covering those gaps are welcome. Do not attach
credentials, private paths, paid-provider tokens, or proprietary scene files.

## v1.4.0 validation

See [the integration report](../docs/test-results/v1.4.0-integration.md). Unreal import
behavior and Blender 4.x live behavior remain unverified. Runtime recipe checks are
not skill-trigger evaluations. Both MCP routes pass the 35 core checks, and bounded
native Codex workflows pass, but the full Codex/Claude Code routing matrix remains
incomplete and is a documented validation gap for follow-up contributors.
