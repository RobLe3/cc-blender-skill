# cc-blender-skill — Plugin

A Claude Code skill plugin that lets Claude use Blender like a senior 3D artist via natural language.

**Version**: 0.3.0 (scaffolding complete; not yet validated against a real Blender instance — see [VERSIONING.md](../VERSIONING.md))

---

## What's in this plugin

10 chain-loadable skills:

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

---

## Install

### Prerequisites

1. **Blender ≥ 4.0** with the [BlenderMCP addon](https://github.com/ahujasid/blender-mcp) installed and running on port 9876.
2. **Claude Code** ≥ 1.0 with skills support.
3. **Python 3.9+** with `opencv-python`, `numpy`, `scipy`, `Pillow` (only needed for `wireframe-to-3d` — install with `pip install -r ../requirements.txt`).

### Install all skills (personal scope)

Each skill goes into `~/.claude/skills/<skill-name>/`. Easiest is to symlink the entire `plugin/skills/` contents:

```bash
cd /path/to/cc-blender-skill
for skill in plugin/skills/*/; do
    name=$(basename "$skill")
    ln -sfn "$(pwd)/$skill" "$HOME/.claude/skills/$name"
done
ls -la ~/.claude/skills/ | grep blender
```

Or copy (no live updates from the repo):

```bash
cp -r plugin/skills/* ~/.claude/skills/
```

### Install for a single project

```bash
cd /path/to/your/project
mkdir -p .claude/skills
ln -s /path/to/cc-blender-skill/plugin/skills/text-to-blender .claude/skills/text-to-blender
# Repeat for each skill you want available in this project
```

### Verify install

In Claude Code, type:

```
What skills are available?
```

You should see the 10 skills listed. If not:
- Restart Claude Code (top-level skills directories are watched on startup; new directories require a restart)
- Check `ls ~/.claude/skills/` to confirm the symlinks are present
- Check Blender is running with the MCP addon enabled

---

## Use

### Auto-invocation (preferred)

Just describe what you want in natural language:

```
Make a 3D model of a teapot and render it with three-point lighting.
```

Claude detects the intent, loads `text-to-blender`, which chain-loads `blender-modeling` + `blender-materials` + `blender-lighting` + `blender-rendering`, and executes the pipeline via the Blender MCP.

### Explicit invocation

Type `/<skill-name>` directly:

```
/wireframe-to-3d ./glasses_front.png
/blender-lighting set up dramatic three-point for the active subject
/blender-export glb /tmp/output.glb
```

---

## How the skills compose

The orchestrator `text-to-blender` reads the user's intent and decides which sub-skills to chain-load. Each sub-skill stays under 500 lines (the Anthropic recommended cap) and points to its own `references/overview.md` for depth on edge cases.

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

- **Pure-skill design**: no Python wrapper, no custom MCP. Claude is the orchestrator. Sub-skills are markdown decision trees + inline code recipes.
- **Generated Python via `mcp__blender__execute_blender_code`**: each call is a fresh namespace. Objects identified by `bpy.data.objects['name']`, never by Python variables.
- **Naming convention**: `GEO-`, `MAT-`, `LGT-`, `CAM-`, `ARM-`, `COL-` prefixes (Blender Studio standard).
- **MCP transport**: `ahujasid/blender-mcp` socket on :9876 (synchronous, 180 s timeout per call).

See `../docs/` for full architecture notes, MCP coverage assessment, and verification report.

---

## Coexistence with other Blender skills

This plugin coexists peacefully with:

- [`ra100/blender-claude-plugin`](https://github.com/ra100/blender-claude-plugin) — generalist Blender API reference skills (geometry nodes, shader nodes, compositor). Install both for the broadest coverage.
- [`Dev-GOM/blender-toolkit`](https://mcpmarket.com/tools/skills/blender-toolkit) — specialty Mixamo retargeting via a separate WebSocket addon (port 9400+, different from ahujasid's :9876). Both can run simultaneously.

---

## Status & honest version

**0.3.0** — scaffolding complete. The skill structure follows Anthropic's official skills spec, the architecture is verified against the actual Blender MCP source, and the recipe library covers ~80% of common requests.

What's NOT done yet:
- End-to-end validation against a running Blender instance
- Trigger-eval test cases per skill (recommended 20 trigger / 20 no-trigger queries each)
- Recipe library expansion in long-tail areas (geometry nodes recipes, sculpting, complex sims)
- Worked example scenes with proof-renders in `assets/`

See [VERSIONING.md](../VERSIONING.md) for the path to v1.0.

---

## Reporting issues

Open issues at: https://github.com/RobLe3/cc-blender-skill/issues

Include:
- Which skill triggered (or didn't)
- Your Blender version
- Your `ahujasid/blender-mcp` version
- The full prompt + Claude's response (or refusal)
