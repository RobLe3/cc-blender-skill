---
name: blender-export
description: Export Blender scenes to glTF/GLB (web/AR), FBX (game engines), OBJ (universal), USD (VFX pipelines), STL (3D printing). Includes Unreal collision hulls and Multires normal-map baking for low-poly export, per-format settings, embed/unpack textures, axis conversion, polygon optimization (Decimate), and target-platform validation. Use whenever the user asks to "export this", "save as glTF / FBX / OBJ / STL / USD", "package for Unity / Unreal / Three.js / web / AR / 3D print", or any output format conversion. Make sure to use this skill even if the user does not say "export" — also covers "package this for the web", "make it work in Unity", "send to Unreal", "save for 3D printing".
allowed-tools: Read Bash mcp__blender__execute_blender_code mcp__blender__get_scene_info mcp__blender__get_object_info mcp__blender__get_objects_summary mcp__blender__get_object_detail_summary mcp__blender__render_viewport_to_path mcp__blender__search_api_docs mcp__blender_official__execute_blender_code mcp__blender_official__get_objects_summary mcp__blender_official__get_object_detail_summary mcp__blender_official__render_viewport_to_path mcp__blender_official__search_api_docs
---


## MCP backend

Use when: Any export to a non-.blend format, packaging for game engines, web, AR, or 3D printing.

Before the first Blender call, read [../text-to-blender/references/mcp-backends.md](../text-to-blender/references/mcp-backends.md). Prefer official MCP for shared capabilities; preserve the selected backend for the whole task. Tool names in recipes are client/legacy examples: map them through that reference and its agent-host guide.
# Blender Export

Export to the right format with the right settings. Wrong format choice = days of debugging in the target platform.

## Format decision tree

```
Where is this going?
├── Web (Three.js, Babylon.js, model-viewer, AR Quick Look) → glTF / GLB
├── Game engine (Unity, Unreal, Godot)
│   ├── Animated/rigged → FBX (or glTF for modern engines)
│   └── Static → OBJ or FBX or glTF
├── Apple AR (USDZ) → USDZ (special, see Recipe 6)
├── 3D printing → STL (geometry only, must be watertight)
├── VFX pipeline (Maya, Houdini, Nuke) → USD
└── DCC roundtrip → FBX (industry standard)
```

**Quick rule for unknown target**: glTF / GLB. Open standard, modern, universally supported.

## Recipes

### Recipe 1 — glTF / GLB export (web / AR / general)

```python
import bpy

bpy.ops.export_scene.gltf(
    filepath='/tmp/output.glb',
    export_format='GLB',                 # single-file binary; preferred
    export_apply=True,                   # apply modifiers before export
    export_materials='EXPORT',
    export_image_format='AUTO',          # PNG; AUTO falls back to JPEG for opaque images
    export_yup=True,                     # Y-up convention (most engines / web expect this)
    export_animations=True,              # toggle off for static models
    export_morph=True,                   # shape keys
    export_skins=True,                   # armatures + weights
    export_normals=True,
    export_tangents=False,               # skip unless target uses tangent-space normals beyond standard
)

# Verify
import os
size_mb = os.path.getsize('/tmp/output.glb') / (1024 * 1024)
print(f"export:gltf {size_mb:.2f} MB")
```

**glTF caveats**:
- Only Principled BSDF materials export cleanly. Procedural shaders are dropped or simplified.
- Hard cap: 15 MB; soft target: 8 MB.
- No KTX2 / Draco compression (unless target supports those loaders).
- PNG textures only (max 1024×1024 typical).

### Recipe 2 — Decimate before export (if too large)

```python
import bpy

obj = bpy.data.objects['GEO-target']
if obj.type != 'MESH':
    raise ValueError('Decimation requires a mesh')
selected = list(bpy.context.selected_objects)
active = bpy.context.view_layer.objects.active
mode = active.mode if active else 'OBJECT'
try:
    if mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    mod = obj.modifiers.new('Decimate', type='DECIMATE')
    mod.decimate_type = 'COLLAPSE'
    mod.ratio = 0.7    # keep 70% of faces; lower = more reduction
    bpy.ops.object.modifier_apply(modifier=mod.name)
finally:
    bpy.ops.object.select_all(action='DESELECT')
    for item in selected:
        item.select_set(True)
    bpy.context.view_layer.objects.active = active
    if mode != 'OBJECT':
        bpy.ops.object.mode_set(mode=mode)

print(f"decimated:{obj.name} verts:{len(obj.data.vertices)}")
```

Then re-export. Iterate ratio until file size fits target.

### Recipe 3 — FBX export (game engines)

```python
import bpy

bpy.ops.export_scene.fbx(
    filepath='/tmp/output.fbx',
    use_selection=False,
    apply_unit_scale=True,
    apply_scale_options='FBX_SCALE_ALL',
    bake_space_transform=True,        # critical: applies rotation to mesh
    object_types={'MESH', 'ARMATURE', 'EMPTY'},
    use_mesh_modifiers=True,
    mesh_smooth_type='FACE',
    use_armature_deform_only=True,
    bake_anim=True,
    bake_anim_use_all_bones=True,
    bake_anim_use_nla_strips=True,
    bake_anim_use_all_actions=True,
    bake_anim_force_startend_keying=True,
    embed_textures=True,              # critical: embed textures into FBX
    path_mode='COPY',
    axis_forward='-Z',
    axis_up='Y',
)
print('export:fbx')
```

**Common FBX gotchas**:
- Model rotated 90° in target → check `axis_up='Y', axis_forward='-Z'`
- Model 100× too large → Apply Transform on the object before export
- Textures missing → `embed_textures=True, path_mode='COPY'`
- Animation only plays one action → use NLA + bake all actions

### Recipe 4 — OBJ export (simple / universal)

```python
import bpy

bpy.ops.wm.obj_export(
    filepath='/tmp/output.obj',
    export_animation=False,
    apply_modifiers=True,
    export_eval_mode='DAG_EVAL_VIEWPORT',
    export_uv=True,
    export_normals=True,
    export_materials=True,
    export_triangulated_mesh=False,
    forward_axis='NEGATIVE_Z',
    up_axis='Y',
)
print('export:obj')
```

OBJ has no animation, no rigging, basic material support only. Use for simple geometry exchange.

### Recipe 5 — STL export (3D printing)

```python
import bpy

bpy.ops.wm.stl_export(
    filepath='/tmp/output.stl',
    ascii_format=False,    # binary STL (smaller, faster)
    apply_modifiers=True,
)
print('export:stl')
```

**Critical for STL**:
- Mesh must be **watertight** (no holes, no flipped normals, no internal faces).
- Pre-export: in Edit Mode, run `Mesh → Clean Up → Make Manifold`.
- STL has NO units — most slicers assume mm. Set Blender scene units to mm before modeling.
- STL has NO color/material — single-color grey only.

### Recipe 6 — USD export (VFX pipeline)

```python
import bpy

bpy.ops.wm.usd_export(
    filepath='/tmp/scene.usdc',
    export_animation=True,
    export_uvmaps=True,
    export_normals=True,
    export_materials=True,
    use_instancing=True,
    export_textures=True,
    overwrite_textures=True,
)
print('export:usd')
```

USD variants:
- `.usd` — text-based (debuggable, large)
- `.usdc` — binary (compact, fast — **default choice**)
- `.usda` — ASCII (human-readable, larger)
- `.usdz` — zipped USD with all assets (Apple AR / iOS)

### Recipe 7 — Pre-export checklist (run before any export)

```python
import bpy

# 1. Apply transforms (rotation + scale baked into geometry)
obj = bpy.data.objects['GEO-target']
bpy.context.view_layer.objects.active = obj
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

# 2. Recompute normals
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.mesh.remove_doubles(threshold=0.0001)
bpy.ops.object.mode_set(mode='OBJECT')

# 3. Apply modifiers (some exporters keep them, but for portability apply before export)
# Already done via export_apply=True / use_mesh_modifiers=True flags

# 4. Verify mesh stats
mesh = obj.data
print(f"export_check:{obj.name} verts:{len(mesh.vertices)} faces:{len(mesh.polygons)}")
```

### Recipe 8 — Verify exported file

```python
import os

filepath = '/tmp/output.glb'
if not os.path.exists(filepath):
    print(f"ERROR:not_found {filepath}")
else:
    size_mb = os.path.getsize(filepath) / (1024 * 1024)
    print(f"verified:{filepath} {size_mb:.2f}MB")
```

Always verify after export. Use the host's shell tool: `ls -la /tmp/output.glb`.

### Recipe 9 — Unreal collision meshes

Export a separate collider with the render mesh in the **same FBX**. Its name must
match the render mesh exactly: `SM_Chair` → `UCX_SM_Chair_01`, `_02`, and so on.
For existing `GEO-` names, derive the collider name from that actual name; do not
rename the render mesh just to fit an example.

| Prefix | Required shape |
|--------|----------------|
| `UCX_` | One closed, outward-wound convex hull |
| `UBX_` | Rectangular box, not deformed geometry |
| `USP_` | Sphere, not a stretched ellipsoid |
| `UCP_` | Cylinder with hemispherical ends |

Use several simple hulls for concave props: one hull around a table blocks the
space underneath. Derive positions from geometry, not hand-entered guesses.
A face-plane convexity test alone accepts open or empty meshes; it is not an export
gate. Use `scripts/collision_preflight.py` to inspect the **evaluated** collider,
check names/closedness/winding/volume/convexity, and export only the intended objects.
It rejects rather than repairs invalid geometry and preserves selection/mode.

```python
import bpy, runpy
# Substitute the installed helper path; load inside Blender, not ordinary Python.
helpers = runpy.run_path('/absolute/path/to/blender-export/scripts/collision_preflight.py')
mesh = bpy.data.objects['SM_Chair']
colliders = [bpy.data.objects['UCX_SM_Chair_01']]
result = helpers['export_collision_fbx'](mesh, colliders, '/tmp/chair_collision.fbx')
print(result)
```

The primitive checks cover local-axis authored boxes/spheres/capsules; use `UCX_`
for shapes outside those constraints. Boxes/spheres are unsuitable for a
non-uniformly scaled render object. Use a new output path rather than overwriting.
Only one render mesh per collision FBX is supported by this helper.

**Engine-side behavior is not yet validated.** Epic documents these conventions,
but an Unreal import must verify hull count, openings, scale, and collision before
claiming engine acceptance. Missing custom collision may instead trigger automatic
collision generation; do not assume every importer configuration behaves alike.

### Recipe 10 — Multires: bake to the cage, then export

A live Multires modifier may export every evaluated subdivided face or omit sculpt
geometry, depending on exporter settings. For a low-poly asset, bake the detailed
surface to a normal map and export level 0. A 30-face cage at level 8 is approximately
2 million faces.

Use `scripts/multires_bake_export.py` for a single-material target with UVs, an active
Image Texture holding a **Non-Color** bake image, and exactly one enabled Multires
modifier **last in the stack**. The helper sets viewport level **0 before baking**,
keeps it there through FBX export, saves/connects the normal map, and then restores
selection, active object, mode, bake settings, engine, and subdivision levels.
Use a single-user material and bake image. It does not overwrite an existing normal
connection or accepted output files.

```python
import bpy, runpy
helpers = runpy.run_path('/absolute/path/to/blender-export/scripts/multires_bake_export.py')
result = helpers['bake_export_cage'](
    bpy.data.objects['GEO-target'], '/tmp/target_normal.png', '/tmp/target_cage.fbx')
print(result)
```

A saved normal map/material connection is the intended change. On failure,
generated files remain failure evidence; the helper restores temporary state and
removes its new normal connection. Use new paths for a retry. To include colliders,
pass an `export_fbx` callback that calls `export_collision_fbx` **inside** this helper's
level-0 context; see [references/unreal-export.md](references/unreal-export.md).
Do not re-export after subdivision levels have been restored, or add ordinary meshes
to the bake selection.

The helper detects the installed 5.x/4.x bake-property layout rather than assuming
a spelling. **Live validation is on Blender 5.1.1; Blender 4.x and Unreal imports
remain unverified.** Normal maps preserve surface shading, not silhouette changes.

## Polycount targets per platform

| Platform | Target | Notes |
|----------|--------|-------|
| Web (glTF) | ≤ 30 000 tris | Mobile-safe |
| Hero web asset | ≤ 60 000 tris | Desktop OK |
| Unity / Unreal hero | 50 000–100 000 tris | High-end |
| Mobile game | ≤ 10 000 tris | Per asset |
| AR USDZ | ≤ 50 000 tris | iOS recommendation |
| 3D print | unlimited | But export size matters |

## Common pitfalls

| Symptom | Fix |
|---------|-----|
| FBX has no textures | Set `embed_textures=True, path_mode='COPY'` |
| Procedural material missing in glTF | Bake to image textures first; use only Principled BSDF |
| Game engine: model rotated 90° | FBX: `axis_up='Y', axis_forward='-Z'`; glTF: `export_yup=True` |
| Game engine: model 100× too large | Apply Transform; check unit scale |
| OBJ won't import elsewhere | Stick to ASCII filenames |
| STL won't print | Make Manifold; recompute normals |
| GLB > 15 MB | Apply Decimate (Recipe 2); reduce textures to 1024×1024 |
| Bone count exceeded | Limit weights to 4 per vertex; reduce bone count |
| Animation didn't export | glTF: `export_animations=True`; FBX: `bake_anim=True` |
| Unreal: missing/wrong custom collision | Check names, convex closed hulls, and same-file selection (Recipe 9); inspect the import in Unreal |
| Multires bake fails with a misleading multi-resolution error | Keep Multires last and isolate the target selection (Recipe 10) |
| Baked normals disagree with exported cage | Set viewport level 0 **before** baking, not just before export |
| FBX unexpectedly contains millions of faces | Viewport `levels` controls evaluated Multires export, not `total_levels` |
| Unreal: no smoothing-group information | Use `mesh_smooth_type='FACE'`; then verify inside Unreal |

## When to load `references/overview.md`

Load when:
- Multi-format batch export needed
- Asset Browser / library override workflow
- USDZ for Apple AR specifics
- Game engine roundtrip troubleshooting (Unity/Unreal-specific quirks)
- LOD generation strategy

The reference covers: per-format pitfalls, asset browser workflow, library overrides for production, USD composition, polycount targets per platform.
