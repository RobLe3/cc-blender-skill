# Skill Directory — `wireframe-to-3d`

This folder contains the actual Claude Code skill, structured per the [official Claude Skills spec](https://code.claude.com/docs/en/skills).

## Layout

```
skill/
└── wireframe-to-3d/
    ├── SKILL.md              ← entrypoint (262 lines, ≤500 cap)
    ├── scripts/
    │   └── wireframe_analyzer.py   (image processing pipeline)
    ├── references/
    │   ├── algorithms.md           (theory — load when tuning analyzer)
    │   ├── blender-patterns.md     (Blender Python patterns — load for edge cases)
    │   └── best-practices.md       (performance + standards — load when output is poor)
    └── assets/
        └── (test wireframes — to be added)
```

## How it gets loaded by Claude Code

| Where you place this | Who can use it |
|---------------------|----------------|
| `~/.claude/skills/wireframe-to-3d/` | Personal — across all your projects |
| `<project>/.claude/skills/wireframe-to-3d/` | Project-only |
| Distributed via plugin | Whoever installs the plugin |

### Quick install (personal)

```bash
ln -s "$(pwd)/skill/wireframe-to-3d" ~/.claude/skills/wireframe-to-3d
```

Or copy:
```bash
cp -r skill/wireframe-to-3d ~/.claude/skills/
```

Claude Code watches `~/.claude/skills/` for changes and reloads within the session.

### Invocation

Two ways:
- **Explicit**: `/wireframe-to-3d path/to/wireframe.png`
- **Implicit**: ask "convert this wireframe to 3D" or any phrase matching the description; Claude auto-loads the skill.

## Progressive disclosure

`SKILL.md` is loaded into context when the skill triggers (and stays for the session). The three `references/*.md` files only enter context when Claude reads them via the `Read` tool — typically only when handling edge cases the main body doesn't cover.

This keeps the context cost low: ~262 lines of skill instructions vs ~2 200 lines of supporting reference material that loads only when needed.

## Dependencies

**Outside the skill** (must be installed by the user):
- Blender ≥ 4.0 with [BlenderMCP addon](https://github.com/ahujasid/blender-mcp) running on port 9876
- Python 3.9+ with `opencv-python`, `numpy`, `scipy`, `Pillow`

**The skill itself** has no Python package — `wireframe_analyzer.py` runs as a script, invoked via `Bash`.

## Related skills

This skill is **specialized** to wireframe → 3D conversion. For general Blender expertise (geometry nodes, shaders, animation, modifiers), pair this with the complementary [`ra100/blender-claude-plugin`](https://github.com/ra100/blender-claude-plugin) which provides 8 generalist Blender skills.
