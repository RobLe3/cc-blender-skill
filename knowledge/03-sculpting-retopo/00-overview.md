# Sculpting + Retopology — Pro Knowledge Overview

**Domain**: 03 — Sculpting, Dyntopo, Multires, Retopology  
**Status**: Initial pass complete  
**Last update**: 2026-04-27

---

## The pro sculpting workflow (five stages)

A senior 3D artist's typical sculpting pipeline:

```
1. Block out                      →  Coarse silhouette in low poly mesh or Voxel Remesh
                                     Goal: nail the proportions and big shapes
                                     Tool: Grab brush, Move brush, basic sculpting

2. Voxel Remesh refinement        →  Increase resolution gradually (1.5× max per step)
                                     Tool: Voxel Remesh (Ctrl+R)
                                     Avoid Dyntopo here — it's too unstructured

3. Detail with Dyntopo            →  Once big shapes are locked, add surface detail
                                     Tool: Dyntopo (D, default subdivide-collapse)
                                     This is for skin pores, scratches, cracks

4. Retopology                     →  Build clean low-poly mesh over high-poly sculpt
                                     Tool: Manual + Shrinkwrap, or QuadRemesh, or
                                           Auto-retopo addons (RetopoFlow paid)

5. Multires + bake                →  Apply Multiresolution modifier on retopo mesh
                                     Sculpt back details on subdivision levels
                                     Bake normal map from sculpt level to base level
```

This sequence — block → remesh → dyntopo → retopo → multires bake — is **the** standard for production characters and creatures.

---

## Dynamic Topology (Dyntopo) — what it is, when to use

**What it does**: Subdivides geometry on-the-fly under the brush, creating new triangles where you sculpt. Mesh density adapts automatically.

**When to use**:
- ✅ Adding fine surface detail (pores, scratches, wrinkles, scales)
- ✅ Free-form blocking when you don't yet know the topology you want
- ✅ Quick concept sculpts not destined for animation
- ❌ Building base shapes that will be retopologized — use Voxel Remesh instead
- ❌ Multires-style detail editing — incompatible with Multires modifier
- ❌ When you need clean quads (Dyntopo creates triangle soup)

**Key settings**:
| Setting | Default | What it does |
|---------|---------|--------------|
| **Detail Mode** | Subdivide-Collapse | Adds AND removes geometry as you sculpt |
| **Detail Type** | Constant Detail | Triangle size relative to world scale (best for production) |
| **Detail Size** | 12 px (relative) | Lower = denser; ~5 px for fine detail |
| **Refine Method** | Subdivide Edges | What happens to existing edges under the brush |
| **Smooth Shading** | On | Smooth normals on new triangles |

**Pro pitfall**: Dyntopo creates triangles, not quads. You **cannot** animate or rig a Dyntopo sculpt directly. Always retopologize first.

---

## Multiresolution (Multires) Modifier

**What it is**: A non-destructive modifier that stores multiple subdivision levels, allowing you to sculpt at high res and edit topology at low res.

**Key advantage over Dyntopo**: Preserves clean quad topology while adding sculptable detail. The base mesh stays animation-ready.

```python
import bpy

obj = bpy.data.objects['GEO-character']
mod = obj.modifiers.new('Multires', type='MULTIRES')

# Subdivide twice
bpy.context.view_layer.objects.active = obj
bpy.ops.object.multires_subdivide(modifier='Multires')
bpy.ops.object.multires_subdivide(modifier='Multires')

# Now in Sculpt Mode, you can sculpt at full detail
# Switch back to level 0 to edit base topology
```

**Workflow with Multires**:
1. Build clean retopo mesh (quads, edge loops in right places).
2. Add Multires modifier.
3. Subdivide 2-3 levels (each ×4 polycount).
4. Sculpt at the highest level.
5. Switch to lower levels for fixing big-shape mistakes (changes propagate up).
6. Bake normal map from highest to lowest level for game/realtime export.

**Pitfall**: Sculpting at multires level 5+ on a 10K base mesh = 10M+ polys. Performance degrades fast. For game characters, base mesh ≤ 5K, multires ≤ 4 levels.

---

## Voxel Remesh (the rough-shape sculptor's tool)

**What it does**: Recreates the mesh as a uniform grid of cubes (voxels), discarding original topology. Result: triangle-uniform density everywhere.

**When to use**:
- Block-out stage: don't worry about topology yet
- Joining sculpts (boolean-like)
- Resetting bad topology

**Key control**: **Voxel Size** (in scene units). Smaller = denser. Increase or decrease in 1.5× steps to avoid faceting.

```python
import bpy

obj = bpy.data.objects['GEO-blockout']
obj.data.remesh_voxel_size = 0.05  # 5 cm at 1m scale
bpy.context.view_layer.objects.active = obj
bpy.ops.object.voxel_remesh()
```

**Pro tip from production**: "Use very large voxel size, decrease it only when all the shapes at current resolution are done. Don't decrease voxel size by more than 1.5x at a time, or you will get faceting." (Sofia Pahaoja, Medium)

---

## Retopology (the boring but critical step)

**Why retopology is necessary**: Dyntopo and Voxel Remesh both create messy topology — uneven, all-triangle, no edge flow. This is **unusable** for animation, rigging, or efficient texturing.

**Retopology** = manually (or with tools) creating a new low-poly quad mesh that conforms to the sculpt's surface.

### Manual retopology pattern
```python
# 1. Use sculpt as reference; hide everything else.
# 2. Add a plane (the start of the new low-poly mesh).
# 3. Add Shrinkwrap modifier on the plane.
mod = new_mesh.modifiers.new('Shrinkwrap', type='SHRINKWRAP')
mod.target = sculpt_obj
mod.wrap_method = 'NEAREST_SURFACEPOINT'
# 4. In Edit Mode, extrude the plane outwards.
#    Each new vertex auto-snaps to the sculpt surface.
# 5. Build edge loops following the natural muscle/feature flow.
```

### Auto-retopology options
- **QuadRemesh** (Blender Manual: `bpy.ops.object.quadriflow_remesh`) — quad-dominant remesh, decent for most cases
- **RetopoFlow** (paid Superhive addon) — best-in-class manual retopo tools
- **Instant Meshes** (free external tool) — algorithmic quad-dominant retopo
- **Built-in Remesh modifier (Quads mode)** — fastest, but less clean

```python
import bpy

obj = bpy.data.objects['GEO-sculpt']
bpy.ops.object.quadriflow_remesh(
    target_faces=5000,
    use_paint_symmetry=True,
)
```

### Retopology rules of thumb
- **Edge loops follow muscle / fold lines** (around eyes, mouth, knee, elbow joints)
- **Quad-dominant**: triangles only where unavoidable; n-gons (>4 sides) banned
- **Density matches deformation needs**: dense around joints and the face; sparse on flats
- **Even spacing** when possible: long thin quads create stretching artifacts

---

## Bake high → low

After retopology, bake the sculpt's detail into a normal map for the low-poly mesh:

```python
import bpy

bpy.context.view_layer.objects.active = low_poly
low_poly.select_set(True)
high_poly.select_set(True)  # selected as source

# Set bake type
bpy.context.scene.cycles.bake_type = 'NORMAL'

# Bake settings
bpy.ops.object.bake(
    type='NORMAL',
    use_selected_to_active=True,
    cage_extrusion=0.05,
    margin=16,
)
# Normal map saved to active image texture node on the low-poly material
```

**Cage** is critical for accurate baking on complex shapes. A "cage" is an inflated copy of the low-poly mesh that defines the sample distance from the high-poly. `cage_extrusion=0.05` works for most characters.

---

## Sculpting brush families (high-impact subset)

| Brush | Hotkey | What it does | Use for |
|-------|--------|--------------|---------|
| **Grab** | G | Move geometry without sculpting detail | Big shapes, posing |
| **Draw** | X | Push/pull surface | General sculpting |
| **Clay Strips** | C | Build up flat strokes (like sculpting clay) | Building muscle, rough detail |
| **Smooth** | Shift | Average vertices | Cleanup, removing pinches |
| **Crease** | Shift+C | Sharpen edges | Hair flow, hard creases |
| **Inflate** | I | Push along normals | Adding mass, fattening |
| **Pinch** | P | Pull vertices toward stroke center | Sharpening edges, creasing |
| **Snake Hook** | K | Pull mesh into long shapes | Tentacles, hair strands |
| **Mask** | M | Restrict sculpting to area | Isolation; can convert to mesh |

**Pressure sensitivity**: Tablet recommended; mouse works but slower for fine work.

---

## Common pitfalls

| Mistake | Why it's wrong | Fix |
|---------|---------------|-----|
| Sculpting before retopo | Triangles ruin animation | Retopologize first or use Multires |
| Constant Detail too low (< 3 px) | Performance crawls; mesh blows past memory | 5-12 px for most work |
| No symmetry on character sculpting | Asymmetric face from start | Toggle `Sculpt → Symmetry → X` |
| Voxel Remesh at fine voxel size on first attempt | Mesh becomes unworkable | Start big (0.1m), reduce in 1.5× steps |
| Bake normal map without cage | Artifacts on edges | Use cage; `cage_extrusion ≈ thickest detail size` |
| Ignoring Dyntopo's triangulation | Production pipeline breaks | Plan retopology from day 1 |

---

## Sources

- [Dyntopo — Blender 5.1 Manual](https://docs.blender.org/manual/en/latest/sculpt_paint/sculpting/tool_settings/dyntopo.html)
- [Sofia Pahaoja — Remesh + Multires Workflow on Medium](https://medium.com/@skarkkai/remesh-multires-workflow-in-blender-2ae97ae5176d)
- [CGAxis — Sculpting Tools in Blender 5: Complete Guide](https://cgaxis.com/sculpting-tools-in-blender-5/)
- [Artisticrender — Dynamic topology problem-solving](https://artisticrender.com/blender-dynamic-topology-what-where-how-and-problem-solving/)
- [Cookwithrome — What is Multiresolution in Blender](https://cookwithrome.com/blender/what-is-multiresolution-in-blender/)
- [Blender Base Camp — Dyntopo demystified](https://www.blenderbasecamp.com/dyntopo-demystified-blender-sculpting-guide/)

---

## What's still needed

- [ ] Specific brush settings for skin/clothing/organic types
- [ ] Symmetry workflows (radial, mirror, planar)
- [ ] Mask-as-stencil for projection sculpting
- [ ] Multires + Cycles bake exact settings tuned per material type
