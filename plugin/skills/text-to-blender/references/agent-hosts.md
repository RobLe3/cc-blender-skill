# Agent host capabilities and installation

These 30 `SKILL.md` folders are one shared source for Codex, Claude Code, and other
skill-capable agents. Blender operations depend on the selected MCP backend, not on
the model provider. Client compatibility still needs actual discovery and workflow
tests; a generic MCP connection alone does not verify agent behavior.

## Required capabilities

The host must be able to discover/read skills and their relative resources, run local
shell/Python helpers, call MCP tools, and inspect images for visual acceptance.
Without image inspection it can report numerical/file checks, but must not claim
visual acceptance. A remote Blender host needs an explicit file-transfer mechanism.
Without access to local Blender or its MCP endpoint, stop rather than fake execution.

Use the host's actual tools for these operations:

| Logical operation | Example in Codex | Example in Claude Code |
|---|---|---|
| Read a skill/reference/JSON file | File tool or shell `cat`, through the available executor | `Read` |
| Execute a local helper | Shell execution tool, such as `exec_command` | `Bash` |
| Search local files | File search or shell `rg` | `Glob` / `Grep` |
| Inspect a render | Image-viewing tool, such as `view_image` | Image-capable `Read` |
| Blender operation | Advertised MCP tool and its schema | Advertised MCP tool and its schema |

Examples are not mandatory tool names. Use the current inventory; some hosts expose
tools through an execution bridge. The `mcp__<server>__<tool>` names in old recipes
are client spellings, not a portable MCP API requirement. Resolve logical operations
through `mcp-backends.md` and the tools actually available in the session.

`allowed-tools` is optional Claude-specific guidance retained for existing users.
It does not create tools, grant permissions, or enforce policy in another host.
Respect the host's configured approvals, filesystem scope, and tool restrictions.
Activation information is in each skill's name/description and its instruction body,
not in an unsupported `when_to_use` frontmatter extension.

## Codex

Install all skill folders together so sibling references work. From the repository:

```bash
mkdir -p "$HOME/.agents/skills"
for skill in plugin/skills/*/; do
    name=$(basename "$skill")
    # Review an existing destination before replacing it.
    test ! -e "$HOME/.agents/skills/$name" && test ! -L "$HOME/.agents/skills/$name" &&
        ln -s "$(pwd)/$skill" "$HOME/.agents/skills/$name"
done
```

For a project, use `<project>/.agents/skills` instead. Codex follows skill-folder
symlinks; verify all 30 skills are visible without duplicating existing installations.
Invoke `$text-to-blender` or let a matching request activate it implicitly. Codex CLI
and the IDE extension also offer `/skills`. Restart if discovery has not refreshed.

MCP setup is separate. The following is a **configuration example**, not a command
to change the user's settings. Use separate upstream server environments and actual
absolute executable paths. Match each add-on's host/port to its client process:

```toml
# Single legacy backend, preserving an existing server named blender:
[mcp_servers.blender]
command = "/absolute/legacy-env/bin/python"
args = ["-m", "blender_mcp.server"]
[mcp_servers.blender.env]
BLENDER_HOST = "127.0.0.1"
BLENDER_PORT = "9876"
BLENDER_MCP_DISABLE_TELEMETRY = "true"

# Add only when official MCP's add-on is installed and listening on 9877:
[mcp_servers.blender_official]
command = "/absolute/official-env/bin/python"
args = ["-m", "blmcp"]
[mcp_servers.blender_official.env]
BLENDER_MCP_HOST = "127.0.0.1"
BLENDER_MCP_PORT = "9877"
```

Codex uses `~/.codex/config.toml`, or `.codex/config.toml` in a trusted project.
For official-only installation, register official MCP as `blender` instead; the
selected backend is determined by capabilities, not by the server's display name.
Do not put credentials in this repository. Verify the read-only scene query before
authorizing changes. See [Codex skills](https://learn.chatgpt.com/docs/build-skills)
and [Codex MCP](https://learn.chatgpt.com/docs/extend/mcp?surface=cli).

## Claude Code

Keep the existing `~/.claude/skills/<name>` or project `.claude/skills/<name>` setup.
The same shared directories and scripts are used; no generated Claude/Codex fork is
needed. Invoke `/text-to-blender` or make a matching natural-language request.
Configure the MCP processes in the client's own settings, using the same backend
and port policy. Optional `allowed-tools` entries cover the documented server aliases;
different Claude aliases require matching optional entries, not changing core recipes.

## Other hosts

Use the common instruction files and backend schemas with equivalent file/shell/image
and MCP capabilities. Host-specific setup and approval behavior must be verified
separately. Agent-neutral design is not a claim of validation on every agent or of
availability in a browser-only/cloud client without local Blender access.
