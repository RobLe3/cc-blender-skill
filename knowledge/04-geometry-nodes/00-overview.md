# Geometry Nodes — Pro Knowledge Overview

**Domain**: 04 — Geometry Nodes (procedural modeling)  
**Status**: Initial pass complete  
**Last update**: 2026-04-27

---

## What Geometry Nodes are (and aren't)

**Are**: A visual programming system inside Blender that builds, modifies, and instances geometry parametrically. Replaces older particle systems and many modifier stacks for procedural work.

**Aren't**: A full procedural language like Houdini's VEX. Some operations are awkward or impossible (deep recursion, complex string ops). For 80% of procedural needs, GN is more than enough.

**When to use vs alternatives**:
| Need | Use |
|------|-----|
| Scatter trees on terrain | ✅ Geometry Nodes |
| Animate parametric building | ✅ Geometry Nodes |
| Instance variations of one model | ✅ Geometry Nodes |
| Complex character rigging | ❌ Use armatures |
| Cloth/fluid sim | ❌ Use physics modifiers |
| Boolean cuts | ⚠️ Possible but slower than Boolean modifier |
| Hard-surface modeling from scratch | ❌ Use mesh edit mode (faster, more control) |

---

## Core concepts (the 4 things to internalize)

### 1. Geometry
A bag of *attributes* attached to *domains* (point, edge, face, corner, curve, instance).

- **Mesh** — vertices (point domain), edges (edge domain), polygons (face domain)
- **Curve** — control points (point domain), splines (curve domain)
- **Point cloud** — just points
- **Volume** — 3D voxel grid
- **Instances** — references to other geometry (efficient duplication)

### 2. Attributes
Named data attached to a domain. Built-in: `position`, `normal`, `uv_map`, `material_index`. Custom: anything you create.

```
position (Vector, Point domain)   → coordinates per vertex
radius (Float, Point domain)      → e.g., per-point thickness for curves
material_index (Int, Face domain) → which material slot per face
```

### 3. Fields
Lazy expressions evaluated per-element on a domain. The "secret sauce" of GN.

```
[Position] → [Separate XYZ] → [Z output]
       This is a field: "for each point, return its Z coordinate"
       
[Z] → [Compare > 0] → mask of points above ground
```

You don't compute the value once and store it. The field re-evaluates per element when consumed.

### 4. Instances
Lightweight references to geometry. 10,000 instanced trees ≠ 10,000 copies; it's 1 tree + 10,000 transform matrices. Fast.

---

## Essential node patterns (the 80% of recipes)

### Scatter on surface
```
Mesh Input → Distribute Points on Faces (density=10) → Instance on Points (Object Info: Tree)
                                                              ↑
                                              optional: Random rotation/scale
```

The classic forest. `Distribute Points on Faces` has Poisson Disk for natural-looking spacing.

### Instance variations
```
Distribute Points → Instance on Points → Pick Instance (Random Value index)
                                                              ↑
                            Object Info ×3 (3 different trees) → Combine into Collection
```

Pick from a collection of meshes randomly per-point.

### Capture an attribute
```
Position → Capture Attribute (point domain) → ... use in shader
```

`Capture Attribute` realizes a field into a stored attribute, accessible to shaders via `Attribute` node.

### Procedural terrain (from research)
```
Grid → Set Position (offset Z by Noise Texture sampled at xy)
     → Set Material
     → Output
```

Modify the `position` attribute by adding height from a noise texture. Live, parametric, editable.

### Curve to instances
```
Curve → Resample Curve (count=20) → Instance on Points (mesh: rivet)
                                                              ↑
                                            align to curve tangent
```

Useful for fence posts along a path, hair strands, conveyor belt items.

### Boolean-ish via volume
```
Mesh A → Mesh to Volume → Boolean (Difference) ← Mesh to Volume ← Mesh B
                                ↓
                        Volume to Mesh
```

Slower than the Boolean modifier but fully procedural and animatable.

---

## Building a node group via Python

```python
import bpy

# 1. Add Geometry Nodes modifier
obj = bpy.data.objects['GEO-terrain']
mod = obj.modifiers.new('GeometryNodes', type='NODES')

# 2. Create a new node tree
node_tree = bpy.data.node_groups.new('TerrainNodes', 'GeometryNodeTree')
mod.node_group = node_tree

# 3. Set up interface (inputs/outputs)
node_tree.interface.new_socket('Geometry', socket_type='NodeSocketGeometry', in_out='INPUT')
node_tree.interface.new_socket('Geometry', socket_type='NodeSocketGeometry', in_out='OUTPUT')
node_tree.interface.new_socket('Height', socket_type='NodeSocketFloat', in_out='INPUT')

# 4. Add nodes
input_node = node_tree.nodes.new('NodeGroupInput')
output_node = node_tree.nodes.new('NodeGroupOutput')
input_node.location = (-400, 0)
output_node.location = (400, 0)

set_pos = node_tree.nodes.new('GeometryNodeSetPosition')
set_pos.location = (0, 0)

noise = node_tree.nodes.new('ShaderNodeTexNoise')   # Texture nodes work in GN too!
noise.location = (-200, -200)

# 5. Wire connections
links = node_tree.links
links.new(input_node.outputs[0], set_pos.inputs['Geometry'])
links.new(noise.outputs['Fac'], set_pos.inputs['Offset'])  # Note: needs combine_xyz to make a vector
links.new(set_pos.outputs['Geometry'], output_node.inputs[0])

print('node_group:created')
```

**Pro tip**: building GN node trees in Python is verbose but enables programmatic procedural systems. For one-offs, use the UI; for tools, use Python.

---

## The Fields system (advanced but powerful)

A **field** is a function that produces a value per element of a domain. Conceptually like a lazy NumPy expression.

```
Position (Field, Vector, on Point domain)
    │
    ▼
Separate XYZ (Field, splits into 3 floats)
    │
    ▼
Z (Field, Float)
    │
    ▼
Compare > 0 (Field, Bool)
    │
    ▼
Used as input to Set Material (one material above ground, one below)
```

**Realizing a field**:
- `Capture Attribute` — store the field as a permanent attribute (named or anonymous).
- `Sample Index` / `Sample Nearest` — fetch values from the field at specific indices.

**Common fields**:
| Field | Domain | Use |
|-------|--------|-----|
| Position | Point | Per-vertex location |
| Normal | Face/Point | Surface normal |
| Index | All | Element index (0, 1, 2, ...) |
| Random Value | All | Per-element pseudo-random |
| ID | Point on instances | Unique per-instance ID |

---

## Performance tips

| Tip | Why |
|-----|-----|
| Prefer Instances over Realized Geometry | 1M trees = 1M transforms (cheap) vs 1M meshes (heavy) |
| Realize Instances only when needed | Mesh booleans / sculpting / export sometimes need real geometry |
| Use `Distribute Points on Faces (Poisson)` over `(Random)` | Better spacing, similar speed |
| Avoid per-element loops via `For Each` | Unless really needed; field math is much faster |
| Put expensive nodes (textures) early in stack | Cached results, less re-eval |
| Bake to attributes for export | glTF doesn't carry GN; bake to mesh first |

---

## Geometry Nodes for animation

Procedural animation by feeding `Time` (in seconds via the `Scene Time` node) into:
- **Mapping translation** — moving a noise pattern over time (waves, scrolling)
- **Curve evaluation** — instance position along a path animated by time
- **Compare to threshold** — mask appears/disappears based on time

```
Scene Time → Multiply by 0.5 → feed into Noise scale
                         ↓
                   Wave-like animation
```

---

## Export limitations (critical to know)

| Target | Geometry Nodes export |
|--------|----------------------|
| **glTF / GLB** | ❌ Not exported — must "Apply" the modifier first to bake to mesh |
| **FBX** | ❌ Same as glTF |
| **USD** | ⚠️ Limited; instances export but field evaluation does not |
| **Alembic** | ⚠️ Per-frame mesh cache only; no procedural recovery |

**Rule**: Before any export to a game engine or web, apply the Geometry Nodes modifier (or instance-realize, then apply). The procedural recipe stays in the .blend; the exported file gets the realized geometry.

---

## Recommended learning path (Tier C resources)

1. **Blender Studio "Geometry Nodes from Scratch"** — official, structured course covering attributes, fields, instances. [studio.blender.org/training/geometry-nodes-from-scratch/](https://studio.blender.org/training/geometry-nodes-from-scratch/)
2. **CGWire's "Beginner's Guide to Geometry Nodes 2026"** — focuses on Python/scripting integration. [blog.cg-wire.com](https://blog.cg-wire.com/blender-scripting-geometry-nodes/)
3. **80.lv "Introduction to Blender's Geometry Nodes"** — short read, conceptual model. [80.lv](https://80.lv/articles/introduction-to-blender-s-geometry-nodes-understanding-proceduralism)
4. **CG Cookie ASSEMBLE course** — paid, project-based. [cgcookie.com](https://cgcookie.com/courses/assemble-introduction-to-procedural-modeling-with-geometry-nodes-in-blender)

---

## Sources

- [Geometry Nodes — Blender 5.1 Manual](https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/index.html)
- [Blender Studio — Geometry Nodes from Scratch](https://studio.blender.org/training/geometry-nodes-from-scratch/)
- [80.lv — Introduction to Blender's Geometry Nodes](https://80.lv/articles/introduction-to-blender-s-geometry-nodes-understanding-proceduralism)
- [CGWire — Beginner's Guide to Geometry Nodes (Blender 2026)](https://blog.cg-wire.com/blender-scripting-geometry-nodes/)
- [BlenderJob — Geometry Nodes: Beginner to Advanced](https://www.blenderjob.com/geometry-nodes-in-blender)
- [Curve Support in Geometry Nodes (Blender Devtalk #86243)](https://developer.blender.org/T86243)
- [SIGGRAPH 2022 Labs — Procedural Modeling with Geometry Nodes (paper)](https://dl.acm.org/doi/10.1145/3532725.3538516)

---

## Outstanding for next pass

- [ ] Specific recipes: terrain with biomes, parametric building, scatter with masks
- [ ] Custom node groups for reusable patterns
- [ ] Performance benchmarks (instances vs realized) at million-element scale
- [ ] Geometry-to-shader attribute passing
