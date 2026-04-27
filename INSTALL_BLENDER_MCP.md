# Installing Blender MCP — Prerequisite for cc-blender-skill

This plugin sits on top of [`ahujasid/blender-mcp`](https://github.com/ahujasid/blender-mcp). You need both pieces installed and **the addon socket actively listening** before any skill in `plugin/skills/` will work.

---

## 1. Install Blender (≥ 4.0)

[blender.org/download](https://www.blender.org/download/)

Confirm:
```bash
/Applications/Blender.app/Contents/MacOS/Blender --version
# Blender 4.x.x or 5.x.x
```

---

## 2. Install the Blender MCP server

The MCP server is a Python process Claude talks to over the MCP protocol. It in turn talks to Blender over a socket.

```bash
git clone https://github.com/ahujasid/blender-mcp.git ~/.tools/blender-mcp
cd ~/.tools/blender-mcp
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Confirm the executable exists:
```bash
ls ~/.tools/blender-mcp/.venv/bin/blender-mcp
```

---

## 3. Wire the MCP server into Claude Code

Add to `~/.claude.json` (or your project's MCP config):

```json
{
  "mcpServers": {
    "blender": {
      "command": "/Users/<you>/.tools/blender-mcp/.venv/bin/blender-mcp"
    }
  }
}
```

Restart Claude Code. After restart, the deferred tools `mcp__blender__*` should be available.

---

## 4. Install the Blender addon

The addon is the **other half** — the part that actually runs inside Blender, listening on a socket.

1. Open Blender.
2. `Edit → Preferences → Add-ons → Install...`
3. Pick `~/.tools/blender-mcp/addon.py`
4. Enable the checkbox next to `Interface: Blender MCP`.
5. Save preferences.

---

## 5. ⚠ Activate the addon — this is the step everyone misses

The addon enable does **NOT** start the socket. You have to click a button:

1. In the 3D viewport, press `N` to open the side panel.
2. Find the **BlenderMCP** tab.
3. Click **`Connect to MCP server`**.
4. The button should now show as connected, and Blender's terminal will print:
   ```
   BlenderMCP server started on localhost:9876
   ```

### Verify the socket is actually listening

```bash
lsof -iTCP:9876 -sTCP:LISTEN
# Should show a python process (Blender's embedded Python)
```

If empty: the button wasn't clicked, or you clicked Disconnect.

### Verify Claude can talk to Blender

In Claude Code:
```
What is in the current Blender scene?
```

Claude should call `mcp__blender__get_scene_info` and report the default cube + camera + light.

---

## 6. Now install cc-blender-skill

```bash
git clone git@github.com:RobLe3/cc-blender-skill.git
cd cc-blender-skill
for skill in plugin/skills/*/; do
    name=$(basename "$skill")
    ln -sfn "$(pwd)/$skill" "$HOME/.claude/skills/$name"
done
```

Restart Claude Code (top-level skills directories are watched on startup; new directories require a restart).

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Could not connect to Blender` | Addon socket not listening | Click `Connect to MCP server` in N-panel |
| `mcp__blender__*` tools missing | MCP server not registered with Claude | Check `~/.claude.json`; restart Claude Code |
| `lsof -iTCP:9876` empty | Same as #1 | Click the button |
| Click connect → "address in use" | Old socket dangling | Quit Blender, kill stale `python` processes, restart Blender, click connect |
| Click connect → silent fail | Port conflict with another tool | Change port in addon preferences (and update `BLENDER_PORT` env if used) |
| Skill triggers but Blender doesn't change | Verify with `get_scene_info` | If unchanged, the code Claude generated may have errored silently — check Blender's console |

---

## What "actively listening" looks like

A successful setup passes all three:

```bash
# 1. Blender process running
ps aux | grep -i blender | grep -v grep
# /Applications/Blender.app/Contents/MacOS/Blender

# 2. blender-mcp Python process running
ps aux | grep blender-mcp | grep -v grep
# .tools/blender-mcp/.venv/bin/python ...blender-mcp

# 3. Socket listening on 9876
lsof -iTCP:9876 -sTCP:LISTEN
# Python  (PID)  ...  TCP localhost:9876 (LISTEN)
```

If all three are true, every skill in `plugin/skills/` should be able to execute.

---

## Why this manual button-click step exists

The BlenderMCP addon is conservative: it doesn't open a network socket on Blender startup because that's a security/privacy decision the user should make explicitly. Many users keep the addon installed but only "Connect" when they actually want Claude or another MCP client to drive Blender. We respect that choice; this plugin's prerequisite check (in `text-to-blender/SKILL.md`) detects the disconnected state and asks the user clearly.
