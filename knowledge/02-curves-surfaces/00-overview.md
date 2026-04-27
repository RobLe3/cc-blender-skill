# Curves + Surfaces — Pro Knowledge Overview

**Domain**: 02 — Curves, NURBS, Lofting  
**Status**: Initial pass complete  
**Last update**: 2026-04-27

---

## When to use curves vs meshes

| Use case | Curves | Meshes |
|----------|--------|--------|
| Smooth, organic shapes (lenses, cables, frames) | ✅ Best | ❌ Hard |
| Hard-surface, faceted | ❌ Awkward | ✅ Best |
| Animated paths, motion guides | ✅ Best | ❌ Use empty as alternative |
| Boolean ops, sculpting | ❌ Convert first | ✅ Best |
| Procedural pattern (curve-driven) | ✅ Best with Geometry Nodes | ⚠️ Possible |
| Game engine export | ❌ Convert first | ✅ Best |

**Rule**: Use curves to *define* the shape, then convert to mesh for *production*. Curves are the design tool; meshes are the asset.

---

## Curve type decision tree

```
Need exact mathematical shape (true circle, parametric)?
├── YES → NURBS (Non-Uniform Rational B-Spline)
│         Pros: Mathematically exact (a NURBS circle IS a circle)
│         Cons: Less intuitive UI; control points only, no handles
│
└── NO  → Bezier
          Pros: Intuitive control points + handles; easy to edit
          Cons: Approximation only (Bezier circle ≈ circle, never exact)
          ✅ Default for almost everything
```

For lofting: **always use Bezier**. Loft tools and most modifiers expect Bezier.

---

## Bezier handle types

| Type | Behavior | Continuity | Use case |
|------|----------|------------|----------|
| **Aligned** (default) | Handles collinear, can scale independently | C¹ smooth | General smooth curves |
| **Auto** | Blender auto-calculates for smoothness | C² smooth | Truly organic, no kinks |
| **Vector** | Handle points to next control point | Sharp corner | Polyline-style hard angles |
| **Free** | Handles fully independent | C⁰ only | Special cases (kinks, custom flow) |

**Pro tip**: Vector handles **don't add tessellation** between segments. For straight-line sections of a curve, use Vector handles to skip resolution_u multiplication and save polys.

---

## Sweep along path (the workhorse for hardware modeling)

The single most-used curve technique. Recipe:

```python
import bpy

# 1. Create the path (the curve the cross-section will sweep along)
path = bpy.data.curves.new('GEO-cable-path', 'CURVE')
path_obj = bpy.data.objects.new('GEO-cable-path', path)
bpy.context.collection.objects.link(path_obj)
# ... define path control points ...

# 2. Create the cross-section (Bezier circle is most common)
profile = bpy.data.curves.new('GEO-cable-profile', 'CURVE')
profile_obj = bpy.data.objects.new('GEO-cable-profile', profile)
bpy.context.collection.objects.link(profile_obj)
# ... typically a small Bezier circle ...

# 3. Tell the path to use the profile as its bevel
path.bevel_mode = 'OBJECT'
path.bevel_object = profile_obj

# 4. Optional: taper along path
# path.taper_object = some_taper_curve

# 5. Convert to mesh when ready for production
bpy.context.view_layer.objects.active = path_obj
bpy.ops.object.convert(target='MESH')
```

**Use cases**: cables, ropes, pipes, frames, hairpins, decorative trim, ornamental brackets, glasses arms.

**Built-in alternative**: `bevel_depth` + `bevel_resolution` for a circular cross-section without a separate profile object. Simpler but less flexible.

---

## Surface revolution (lathe-like)

For axially symmetric objects (vases, lenses, columns, lamp shades):

```python
# Quick way using Screw modifier
import bpy

# Create the profile (a 2D Bezier curve)
curve_data = bpy.data.curves.new('lens-profile', 'CURVE')
curve_data.dimensions = '2D'
# ... define profile points ...

obj = bpy.data.objects.new('GEO-lens', curve_data)
bpy.context.collection.objects.link(obj)

# Convert to mesh first
bpy.context.view_layer.objects.active = obj
bpy.ops.object.convert(target='MESH')

# Apply Screw modifier for revolution
mod = obj.modifiers.new('Revolve', type='SCREW')
mod.axis = 'Z'
mod.angle = 6.283185  # 2π radians = full revolution
mod.steps = 32         # smoothness
mod.use_smooth_shade = True
bpy.ops.object.modifier_apply(modifier=mod.name)
```

For non-symmetric near-revolution shapes, **Spin** operator (Edit Mode) is faster: `bpy.ops.mesh.spin(steps=32, angle=6.283185, axis=(0, 0, 1))`.

---

## Lofting (skinning between profiles)

Native Blender doesn't have a "Loft" operator out-of-the-box, but three approaches:

### A. Geometry Nodes "Curve to Mesh"
Modern, non-destructive:
```
Curve → Curve to Mesh (with Profile Curve input) → Mesh output
```

### B. Bridge Edge Loops (Edit Mode mesh op)
1. Convert both profile curves to mesh (each becomes a closed loop).
2. Join into one object (Ctrl+J).
3. Edit mode → select both edge loops → `Edge → Bridge Edge Loops`.

### C. Loft Curves addon
Paid addon (Superhive market). Worth it for repeat work; not for one-offs.

**Pro tip**: For variable cross-section sweeps (a profile that changes shape along the path), Geometry Nodes is the right tool. Build a `Curve to Mesh` node group that accepts both path and animated profile.

---

## Curve modifiers (key ones)

| Modifier | Purpose | Notes |
|----------|---------|-------|
| **Curve** | Deform a mesh along a curve | Mesh follows curve like a train on tracks |
| **Array + Curve** | Repeat object along curve | Chain links, fence posts, beads |
| **Hook** | Bind control points to empties | For animated/parametric curves |
| **Subdivide (curve)** | Increase resolution | Smoother render at cost of polygon count |

**Curve modifier classic recipe** (a snake that follows a path):
1. Create curve (path).
2. Create snake mesh (long cylinder).
3. Add Curve modifier to mesh, point it at the curve.
4. Move mesh along the curve's local axis to "slide" along.

---

## Resolution settings (controls polygon output)

```python
curve_data.resolution_u = 12      # viewport resolution along curve
curve_data.render_resolution_u = 24  # render-time resolution; 0 = same as preview
curve_data.bevel_resolution = 8   # segments around the bevel/cross-section
```

**Polygon count formula** for a curve with bevel:
- segments_along_curve × (bevel_resolution × 2) faces, approximately
- A 4-control-point Bezier curve with `resolution_u=12` and `bevel_resolution=8` = ~768 faces

For the wireframe-to-3D skill: `resolution_u=16, bevel_resolution=6` is a good baseline.

---

## Curve-to-mesh conversion checklist

After `bpy.ops.object.convert(target='MESH')`:

```python
# 1. Remove duplicate vertices (often created at curve closures)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.remove_doubles(threshold=0.0001)

# 2. Recompute normals (curve normals can be inconsistent)
bpy.ops.mesh.normals_make_consistent(inside=False)

# 3. Smooth shading
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.shade_smooth()

# 4. Optional: Add subdivision for organic look
mod = obj.modifiers.new('Subdiv', type='SUBSURF')
mod.levels = 1
mod.render_levels = 2
```

---

## Common pitfalls

| Mistake | Fix |
|---------|-----|
| Curve looks "pinched" | Check for handle type mismatch (Free instead of Aligned); also re-evaluate control point spacing |
| Bevel object renders as solid block | The bevel object must be a **2D closed curve** (e.g., Bezier circle); 3D curves don't bevel |
| Convert to mesh produces n-gons | Increase `resolution_u`; ensure bevel_resolution > 4 |
| Path direction is wrong (object moves backward) | In Edit Mode, select all → Curve → Switch Direction |
| Curve has no thickness (invisible) | Either set `bevel_depth` > 0 or assign a `bevel_object` |

---

## Sources

- [Blender 5.1 Curves Manual](https://docs.blender.org/manual/en/latest/modeling/curves/index.html)
- [Artisticrender — Curves: Bezier, NURBS, paths, modifiers](https://artisticrender.com/blender-curve-object-bezier-nurbs-paths-modifiers-and-profiles/)
- [Wikibooks — Bezier intro](https://en.wikibooks.org/wiki/Blender_3D:_Noob_to_Pro/Intro_to_Bezier_Curves)
- [Wikibooks — Curve modifier deformations](https://en.wikibooks.org/wiki/Blender_3D:_Noob_to_Pro/Deforming_Meshes_using_the_Curve_Modifier)
- [Stony Brook CS — Sweeping a cross-section along a path (theory)](https://www3.cs.stonybrook.edu/~tony/intromm/Modeling/Sweep_Path.html)
- [Loft Curves addon (Superhive)](https://superhivemarket.com/products/loft-curves)

## Already covered in `wireframe-to-3d/references/`

The wireframe-to-3D skill already has detailed Bezier curve patterns specific to wireframe-conversion. This domain knowledge **complements** that with broader curve work (paths, lofting, surface revolution) for general-purpose modeling.
