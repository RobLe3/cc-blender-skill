# Comparison: Dev-GOM blender-toolkit vs cc-blender-skill

**Date**: 2026-04-27  
**Subject**: Should we depend on, replace, or coexist with `blender-toolkit`?

---

## What blender-toolkit is

A Claude Code skill (and bundled Blender addon) by **Dev-GOM**, listed at:
- [mcpmarket.com/tools/skills/blender-toolkit](https://mcpmarket.com/tools/skills/blender-toolkit)
- [smithery.ai/skills/Dev-GOM/blender-toolkit](https://smithery.ai/skills/Dev-GOM/blender-toolkit)

**Core capabilities**:
- Geometry creation
- Material + modifier management
- **Mixamo animation retargeting with intelligent bone mapping** (its standout feature)

**Architecture**:
- TypeScript client (separate from Claude Code's MCP)
- Custom Blender addon
- WebSocket protocol on **port 9400+** (not the same port as ahujasid/blender-mcp's :9876)

---

## How it differs from `cc-blender-skill`

| Dimension | Dev-GOM blender-toolkit | cc-blender-skill (ours) |
|-----------|-------------------------|--------------------------|
| **MCP transport** | Custom WebSocket :9400+ | ahujasid/blender-mcp socket :9876 |
| **Blender addon required?** | Yes (custom one) | Yes (ahujasid's BlenderMCP addon) |
| **Scope** | Geometry + materials + Mixamo retargeting | 16 capability domains (modeling, materials, lighting, rendering, animation, rigging, simulation, etc.) |
| **Distinctive feature** | Mixamo retargeting with fuzzy bone matching | Comprehensive task coverage + orchestration |
| **Implementation language** | TypeScript client + Python addon | Pure Skill (markdown + scripts) using existing MCP |
| **Open source?** | Distribution unclear (mcpmarket / smithery) | Yes (GitHub: RobLe3/cc-blender-skill) |

---

## Should we use it?

### Use it as a dependency? **No.**

It runs on its own protocol/addon (port 9400+), parallel to ahujasid/blender-mcp. Depending on it would force users to install two addons and run two services. Our skill is designed around the standard ahujasid/blender-mcp.

### Replace what we're building? **No.**

It covers ~3 narrow capabilities. Our scope is 16 domains. Different ambitions.

### Take inspiration / reference it? **Yes, partially.**

Three things worth borrowing:

1. **Mixamo retargeting recipe**. We don't have this domain at all. We can write a recipe that uses standard `bpy.ops` (no custom addon needed) for Mixamo → Rigify retargeting. Our Phase 4 rigging skill is the natural home.

2. **Fuzzy bone-name matching algorithm**. Their idea of auto-matching source bones to target bones via name similarity (e.g., "mixamorig:LeftArm" → "upper_arm.L") is a genuinely useful pattern. We can implement it as a Python helper script in our scripts/.

3. **Quality-rating UX pattern**. Their "Excellent / Good / Fair / Poor" rating with safe-auto-apply thresholds is a smart UX. We should adopt this in our error-handling and confidence-reporting language (e.g., "matched 8/9 critical bones — auto-applying").

### Coexist? **Yes.**

A user who needs Mixamo retargeting at scale should install blender-toolkit. A user who wants Claude to use Blender broadly across modeling/lighting/rendering should install cc-blender-skill. No conflict — they listen on different ports and target different use cases.

We'll mention this in our README:
> "For specialized Mixamo retargeting workflows, also consider [Dev-GOM/blender-toolkit](https://mcpmarket.com/tools/skills/blender-toolkit)."

---

## Net impact on our plan

**No changes** to the planned Phase 1–3 build. We continue with:
- text-to-blender (orchestrator)
- blender-modeling, blender-materials, blender-lighting (Phase 1)
- blender-cameras, blender-rendering (Phase 2)
- blender-animation, blender-export (Phase 3)

**Optional Phase 4 addition**:
- A `blender-mixamo-retargeting` recipe-style sub-skill that achieves their core feature using the standard ahujasid/blender-mcp + our pure-skill architecture. Lower ambition than Dev-GOM's interactive UI, but fits our architecture better and removes the second-addon requirement.

---

## Sources

- [mcpmarket — blender-toolkit page](https://mcpmarket.com/tools/skills/blender-toolkit)
- [Smithery — Dev-GOM/blender-toolkit](https://smithery.ai/skills/Dev-GOM/blender-toolkit)
- [mcp.directory — blender-toolkit](https://mcp.directory/skills/blender-toolkit)
