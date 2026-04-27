---
name: blender-modeling
description: Create and edit 3D meshes in Blender — primitives, hard-surface modeling, mesh operators, modifier stacks (Bevel, Subdivision, Boolean, Mirror, Array, Solidify), bmesh-level edits, retopology basics. Use whenever the user asks to "make/model/create/build a 3D object", "shape/sculpt this", "add a cube/sphere/cylinder/etc.", "extrude/inset/bevel this face", "add a modifier", or any geometry-creation request that isn't a wireframe trace. Make sure to use this skill even if the user does not say "model" — also covers "make a sword", "build a chair", "add a door", "carve out a hole". Pairs with blender-materials for look-dev and blender-pro-workflow for full pipelines.
when_to_use: Any geometry creation, mesh edit, or modifier stack work in Blender. Not for wireframe → 3D conversion (use wireframe-to-3d) and not for sculpting strokes (Blender's sculpt mode is gestural, not text-driven).
allowed-tools: Read Bash mcp__blender__execute_blender_code mcp__blender__get_scene_info mcp__blender__get_object_info
---

# Blender Modeling

Create geometry in Blender via natural language. You emit Python code that the Blender MCP executes; the patterns below cover the common 80%.

## Decision tree

```
What kind of geometry?
├── Hard-surface (vehicles, weapons, architecture, props)
│   → Cube primitive + Bevel + SubSurf modifier stack
│   → See "Hard-surface stack" recipe
│
├── Organic (characters, creatures, plants — block-out only)
│   → Ico Sphere + sculpting (or Voxel Remesh for shape)
│   → For sculpting strokes, redirect: it's gestural, not text-driven
│
├── Architectural / repeating (fences, columns, tile)
│   → Plane/Cube + Array modifier (+ Curve modifier for paths)
│   → See "Array along curve" recipe
│
├── Cylindrical (pipes, columns, bottles)
│   → Cylinder primitive, or Curve + bevel_object
│   → See "Sweep along path" — covered in wireframe-to-3d if needed
│
├── Holes / cuts in existing geometry
│   → Boolean modifier (DIFFERENCE)
│   → See "Boolean cut" recipe
│
└── Quick block-out from primitives only
    → Multiple primitive_*_add calls
    → See "Block-out scene" recipe
```

## Code-execution rules (recap)

- Each `mcp__blender__execute_blender_code` call gets a fresh Python namespace. Re-import everything; identify objects by `bpy.data.objects['name']`.
- Always name objects with `GEO-` prefix. Never leave `Cube.027`.
- Print structured output back so you can parse results.
- Chunk long sequences into multiple calls.

## Recipes

### Recipe 1 — Add a primitive with a clean name

```python
import bpy

# Add cube
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 1))
obj = bpy.context.active_object
obj.name = 'GEO-base_box'
print(f"created:{obj.name} verts:{len(obj.data.vertices)}")
```

Replace `primitive_cube_add` with: `_plane_`, `_uv_sphere_`, `_ico_sphere_`, `_cylinder_`, `_cone_`, `_torus_`, `_monkey_`. Each takes appropriate arguments (`radius`, `depth`, `vertices`, `segments`, `subdivisions`).

### Recipe 2 — Hard-surface stack (the "Bevel + SubSurf" pattern)

```python
import bpy

obj = bpy.data.objects['GEO-base_box']

# 1. Bevel modifier — round the sharp edges
bevel = obj.modifiers.new('Bevel', type='BEVEL')
bevel.width = 0.02              # 2 cm round-over
bevel.segments = 3              # smoothness
bevel.limit_method = 'ANGLE'    # only bevel edges sharper than threshold
bevel.angle_limit = 0.523599    # 30° in radians

# 2. Subdivision Surface AFTER bevel (critical order)
subsurf = obj.modifiers.new('SubSurf', type='SUBSURF')
subsurf.levels = 2
subsurf.render_levels = 3

# 3. Smooth shading
bpy.context.view_layer.objects.active = obj
bpy.ops.object.shade_smooth()
print(f"hardsurface:{obj.name}")
```

**Critical**: Bevel before SubSurf. Reverse this and you get pinching artifacts.

### Recipe 3 — Edit-mode operations (extrude, inset, loop cut)

```python
import bpy

obj = bpy.data.objects['GEO-base_box']
bpy.context.view_layer.objects.active = obj
bpy.ops.object.mode_set(mode='EDIT')

# Select all faces, then extrude up by 1m
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.extrude_region_move(
    TRANSFORM_OT_translate={'value': (0, 0, 1.0)}
)

# Inset all selected faces by 0.1m
bpy.ops.mesh.inset(thickness=0.1, depth=0)

# Add a loop cut around the middle
bpy.ops.mesh.loopcut_slide(
    MESH_OT_loopcut={'number_cuts': 1, 'edge_index': 0},
    TRANSFORM_OT_edge_slide={'value': 0.0},
)

bpy.ops.object.mode_set(mode='OBJECT')
print(f"edited:{obj.name} verts:{len(obj.data.vertices)}")
```

### Recipe 4 — Boolean cut (drilling a hole)

```python
import bpy

target = bpy.data.objects['GEO-base_box']
cutter = bpy.data.objects.get('GEO-cutter')

if cutter is None:
    bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=3.0, location=(0, 0, 1))
    cutter = bpy.context.active_object
    cutter.name = 'GEO-cutter'

# Apply boolean
mod = target.modifiers.new('Boolean', type='BOOLEAN')
mod.operation = 'DIFFERENCE'
mod.object = cutter
mod.solver = 'EXACT'

bpy.context.view_layer.objects.active = target
bpy.ops.object.modifier_apply(modifier=mod.name)

# Hide cutter from render
cutter.hide_viewport = True
cutter.hide_render = True
print(f"booleaned:{target.name}")
```

### Recipe 5 — Mirror modifier (only model half)

```python
import bpy

obj = bpy.data.objects['GEO-character_half']
mod = obj.modifiers.new('Mirror', type='MIRROR')
mod.use_axis[0] = True   # mirror across X
mod.use_clip = True       # snap vertices on axis
mod.use_mirror_merge = True
mod.merge_threshold = 0.001
print(f"mirrored:{obj.name}")
```

Place Mirror **first** in the stack (before Bevel/SubSurf).

### Recipe 6 — Array along curve (chains, fences, beads)

```python
import bpy

# 1. The base unit
bpy.ops.mesh.primitive_cube_add(size=0.2, location=(0, 0, 0))
unit = bpy.context.active_object
unit.name = 'GEO-bead'

# 2. The path (assume it exists; user provides or we add a Bezier)
path = bpy.data.objects.get('GEO-path')
if path is None:
    bpy.ops.curve.primitive_bezier_curve_add()
    path = bpy.context.active_object
    path.name = 'GEO-path'

# 3. Array modifier (count or fit to length)
arr = unit.modifiers.new('Array', type='ARRAY')
arr.fit_type = 'FIT_CURVE'
arr.curve = path
arr.relative_offset_displace = (1.0, 0, 0)

# 4. Curve modifier — bends the array along the path
crv = unit.modifiers.new('Curve', type='CURVE')
crv.object = path
crv.deform_axis = 'POS_X'
print(f"arrayed:{unit.name}")
```

### Recipe 7 — Block-out (rapid composition test)

```python
import bpy

# Floor
bpy.ops.mesh.primitive_plane_add(size=10)
bpy.context.active_object.name = 'GEO-floor'

# Hero subject
bpy.ops.mesh.primitive_cube_add(size=1.5, location=(0, 0, 0.75))
bpy.context.active_object.name = 'GEO-subject'

# Background prop
bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=2, location=(2, 1.5, 1))
bpy.context.active_object.name = 'GEO-prop_pillar'

print('blockout:done')
```

### Recipe 8 — Cleanup after curve→mesh or boolean

```python
import bpy

obj = bpy.data.objects['GEO-target']
bpy.context.view_layer.objects.active = obj

bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.remove_doubles(threshold=0.0001)
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode='OBJECT')

bpy.ops.object.shade_smooth()
print(f"cleanup:{obj.name} verts:{len(obj.data.vertices)}")
```

## Modifier stack order (memorize this)

```
Mirror → Array → Solidify → Bevel → Subdivision Surface → (Boolean if needed)
```

Wrong order = artifacts. The single most common amateur mistake is SubSurf before Bevel.

## Common pitfalls

| Symptom | Fix |
|---------|-----|
| Default-cube look | Add Bevel (0.02m, 3 segments) and SubSurf |
| Sharp pinch on round shapes | Bevel before SubSurf, not after |
| Black faces in render | Recompute normals (`mesh.normals_make_consistent`) |
| Boolean creates n-gons | Apply Bool, switch to Edit, fix to quads, then SubSurf |
| Symmetry breaks | Use Mirror modifier, not duplicate-and-flip |
| Mesh has hidden interior faces | `Mesh → Clean Up → Delete Loose` |

## When to load `references/overview.md`

Load when:
- The recipes here don't match the request (need bmesh-level precision, custom ops)
- Topology requirements are stricter than usual (animation-ready, game LODs)
- Performance matters (foreach_set, batch ops needed)
- The user references operators not in the recipes

The reference covers: bmesh.ops cookbook, all `bpy.ops.mesh.*` operators worth knowing, hard-surface workflow with MESHmachine-style chamfering, retopology guidelines, mesh-clean checklist.

## What this skill is NOT for

- Wireframe drawing → 3D model: use `wireframe-to-3d`
- Sculpting strokes: Blender's sculpt mode is gestural; can't be driven well from text
- Sweep-along-path / lofting / curve-driven shapes: covered in `wireframe-to-3d/references/blender-patterns.md`
- Materials / lighting / rendering: redirect to those skills
