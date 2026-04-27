---
name: text-to-blender
description: Drive Blender from natural language. Converts plain-English requests ("model a sword and render it with cinematic lighting", "make this glass look frosted", "set up three-point lighting", "export this scene as glTF for the web") into Blender Python code executed via the Blender MCP server. Acts as the orchestrator that picks and chain-loads specialised sub-skills (blender-modeling, blender-materials, blender-lighting, blender-cameras, blender-rendering, blender-animation, blender-export, wireframe-to-3d, blender-pro-workflow). Use this skill whenever the user wants Claude to do anything in Blender, including creating geometry, applying materials, lighting a scene, framing a camera, rendering, animating, or exporting. Make sure to invoke this skill even if the user does not say "Blender" — also covers requests like "create a 3D model of...", "render this...", "make a glTF from...", "set up a scene with...", or any 3D-creation task. Requires the Blender MCP addon (ahujasid/blender-mcp) running on port 9876.
when_to_use: User asks for any 3D creation, modification, lighting, rendering, animation, or export task. Anything involving Blender or that should reasonably be done in Blender.
allowed-tools: Read Bash Glob Grep mcp__blender__execute_blender_code mcp__blender__get_scene_info mcp__blender__get_object_info mcp__blender__get_viewport_screenshot
---

# Text-to-Blender Orchestrator

Turn plain-English requests into Blender work. You are the conductor: read the request, decide which sub-skills to chain-load, sequence them in the right order, and execute via the Blender MCP.

## How this skill works

The user speaks in tasks ("render a hero shot of a sword on a stone"); you:

1. **Identify intent** → which capabilities are needed (modeling? materials? lighting? rendering? export?).
2. **Check prerequisites** → MCP server reachable, scene state.
3. **Route to sub-skills** → load the relevant ones via `Read` and follow their instructions.
4. **Sequence** the work in the order pros use (see `references/assembly-order.md`).
5. **Execute** generated Python via `mcp__blender__execute_blender_code`.
6. **Validate** with `mcp__blender__get_scene_info` and `get_object_info`.
7. **Report** results to the user with concrete numbers (object names, polycounts, file paths, render time).

## Prerequisites — always check first

Before any work, verify:

1. **Blender MCP is reachable**. Call `mcp__blender__get_scene_info`. If it errors with "Could not connect to Blender":
   > "Blender's MCP addon isn't running. Start Blender, enable the BlenderMCP addon (port 9876 default), then re-run."
   
   Stop and ask the user to fix this.

2. **Scene state**. `get_scene_info` returns the current objects. Decide:
   - **Empty scene?** → Start fresh; build from primitives.
   - **Existing objects?** → Operate on them; do NOT delete unless asked.
   - **Default cube only?** → Probably safe to delete (`bpy.ops.object.delete()`).

3. **The user's actual request**. If ambiguous, ask one question. Otherwise proceed with sensible defaults.

## Intent → sub-skill routing table

For each intent the user expresses, load (via `Read`) the matching sub-skill's `SKILL.md` and follow its patterns. Multiple intents = chain multiple sub-skills.

| User intent (paraphrased) | Load these sub-skills | Order |
|--------------------------|----------------------|-------|
| "Make a 3D model of X" | `blender-modeling` | 1st |
| "From this wireframe drawing" | `wireframe-to-3d` | 1st |
| "Use these materials / make it look like X" | `blender-materials` | After modeling |
| "Light it / studio setup / cinematic" | `blender-lighting` | After geometry exists |
| "Hero shot / camera angle / DoF" | `blender-cameras` | After lighting |
| "Render it / produce an image" | `blender-rendering` | Last visual step |
| "Animate / move / rotate over time" | `blender-animation` | After geometry |
| "Export as glTF / FBX / OBJ / for web / for Unity" | `blender-export` | Final step |
| "Set up a scene / production-quality result" | `blender-pro-workflow` | First — guides everything |
| "I'm new / not sure where to start" | `blender-pro-workflow` | First |

**Multi-intent example**: "Model a sword with materials, light it dramatically, and export as glTF" →
1. `blender-pro-workflow` (sequencing strategy)
2. `blender-modeling` (sword geometry)
3. `blender-materials` (steel + leather grip)
4. `blender-lighting` (dramatic 1-point or rim setup)
5. `blender-export` (glTF settings)

## Pro assembly order (when in doubt)

This order minimizes rework. When the user gives a multi-step request, follow it:

1. **Reference + plan** — note the goal.
2. **Block-out** — primitives + camera + composition. Cheapest to iterate.
3. **Camera lock** — pick focal length, frame the shot.
4. **Light v1** — three-point (key/fill/rim) before any material work. Light defines mood.
5. **Refine geometry** — replace primitives with real models.
6. **Materials v1** — flat colors first, get values right.
7. **Light v2** — color + ratios.
8. **Detail pass** — only after the above is right.
9. **Final render** — production samples + denoise.
10. **Composite** — color grade, glare, vignette.
11. **Export** — for the target platform.

Source: `references/assembly-order.md` (deeper rationale).

## Code-execution rules — non-negotiable

When emitting Python for `mcp__blender__execute_blender_code`:

- **Each call is a fresh namespace.** Only `bpy` is pre-imported; re-import `math`, `bmesh`, `numpy`, etc. each call.
- **Identify objects by stable name**, never by Python variable. `bpy.data.objects['GEO-sword']` works across calls; a `sword = ...` assignment does not.
- **Print structured output** so you can parse it back. End each chunk with `print(f"...")` reporting what changed (object names, vertex counts, file paths).
- **Chunk the work.** 180-second timeout per call. Don't dump 500 lines in one call — split into ~5–20-line chunks.
- **Use Blender Studio naming conventions** for everything you create: `GEO-`, `MAT-`, `LGT-`, `CAM-`, `ARM-`, `COL-`. Never leave anything as `Cube.027`.

## Standard skeleton for every operation

```python
import bpy
# (re-import other modules here as needed)

# 1. Scope: identify or create objects by NAME
obj = bpy.data.objects.get('GEO-target') or bpy.data.objects.new('GEO-target', None)

# 2. Do the work
# ...

# 3. Report
print(f"done:GEO-target {len(obj.data.vertices) if obj.data else 0}")
```

## Naming conventions (apply to everything you create)

| Prefix | Meaning |
|--------|---------|
| `GEO-` | Geometry / mesh objects |
| `MAT-` | Materials |
| `LGT-` | Lights |
| `CAM-` | Cameras |
| `ARM-` | Armatures (rigs) |
| `COL-` | Collections |
| `WGT-` | Custom bone shapes / widgets |

Suffix `.L` / `.R` for left/right. Examples: `GEO-sword_blade`, `MAT-steel_brushed`, `LGT-key`.

## Validation rule of thumb

After significant work, call `mcp__blender__get_scene_info` and verify:
- Expected objects exist with correct names.
- Object counts make sense (no runaway duplication).
- Polycount roughly matches target.

Before reporting success on a render or export, confirm the file actually exists (use `Bash`: `ls -la /path/to/output`).

## When to load deeper references

- **`references/assembly-order.md`** — the canonical scene-assembly sequence, time budgets, recovery patterns. Load when planning a multi-step pipeline or when the user asks "what's the right order?".
- **`references/intent-routing.md`** — fuller intent-to-skill mapping with edge cases. Load when the request is ambiguous and you need to disambiguate.
- **`references/code-execution-rules.md`** — detailed rules for `execute_blender_code` (namespace, timeouts, stdout capture). Load when tracking down execution errors.

## Reporting back to the user

When work is done, report concretely:

- ✅ **Created**: list objects + polycounts.
- ✅ **Lit**: list lights + their roles.
- ✅ **Rendered**: file path + size + dimensions + render time.
- ⚠️ **Warnings**: any auto-decimation, naming conflicts, fallback materials.

Example:
> Created `GEO-sword_blade` (1 240 verts), `GEO-sword_grip` (320 verts).  
> Materials: `MAT-steel_brushed`, `MAT-leather_dark`.  
> Lit with `LGT-key` (warm 3200K), `LGT-fill` (cool 5500K), `LGT-rim` (cool blue).  
> Rendered to `/tmp/sword_hero.png` (1920×1080, 2.3 MB, 38 s with 256 samples + OptiX denoise).

## Failure modes — what to do when…

| Problem | Action |
|---------|--------|
| MCP timeout | Break the failing chunk into smaller pieces |
| `Code execution error: <line>` | Read the error; fix that one line; retry |
| Object not found in next call | You used a Python var instead of `bpy.data.objects['name']` |
| Render took too long | Reduce samples, enable adaptive sampling, lower resolution |
| File not at expected path | Use absolute paths; verify with Bash `ls` |
| Material looks wrong after export | You used non-Principled-BSDF nodes; rebuild material with Principled only |
| `'Action' object has no attribute 'fcurves'` | Blender 5.x layered Actions; walk `action.layers[].strips[].channelbags[].fcurves` instead. See `blender-animation` Recipe 3 for the compat helper. |
| `BLENDER_EEVEE_NEXT` rejected | Blender 5.x renamed it back to `BLENDER_EEVEE`. See `blender-rendering` Recipe 3 for the try/except fallback. |

## What this skill is NOT for

- Heavy custom GPU work / writing a render engine (use Blender's existing engines)
- Real-time game logic (use Unity / Unreal directly)
- Sculpting strokes from natural language (sculpting is gestural; use brushes interactively)
- Things outside Blender's capabilities (CAD precision modeling — use FreeCAD; CFD simulation — use Blender's Mantaflow only for VFX-quality, not engineering)

When the user asks for these, redirect them politely and explain.
