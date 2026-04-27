# Cross-Cutting Concerns — Pro Knowledge Overview

**Domain**: 15 — Naming, organization, performance, version control, scripting patterns  
**Status**: Initial pass complete  
**Last update**: 2026-04-27

---

## Naming conventions (Blender Studio standard)

Format: `PREFIX-base_name.SUFFIX`

| Prefix | What it marks |
|--------|--------------|
| **`GEO-`** | Geometry / mesh objects |
| **`MAT-`** | Materials |
| **`LGT-`** | Lights |
| **`CAM-`** | Cameras |
| **`ARM-`** | Armatures (rigs) |
| **`ENV-`** | Environment / matte painting |
| **`COL-`** | Collections |
| **`WGT-`** | Widgets (custom bone shapes, helper meshes) |
| **`EFF-`** | Effects / particles / volumes |
| **`PROP-`** | Props (small interactive items) |

**Suffixes for symmetry/variants**:
- `.L` / `.R` — left/right (for paired objects)
- `.001`, `.002` — auto-generated duplicate (rename these!)
- `.HI` / `.LO` — high-poly / low-poly versions
- `.PROXY` — placeholder for heavy asset

**Examples**:
```
GEO-character_body.HI
GEO-character_body.LO       (low-poly retopo)
MAT-character_skin
ARM-character
LGT-key
LGT-fill
LGT-rim
CAM-hero
COL-hero_character          (collection grouping all hero parts)
```

**Rule**: never ship a file with `Cube.027` or `Material.012`. Always rename.

---

## Collection hierarchy

Use Collections (Blender's modern grouping system) to organize scenes:

```
Scene Collection
├── COL-character
│   ├── GEO-character_body
│   ├── ARM-character
│   └── COL-character_props
│       └── GEO-sword
├── COL-environment
│   ├── GEO-ground
│   ├── GEO-trees
│   └── LGT-environment_lights
├── COL-lighting
│   ├── LGT-key
│   ├── LGT-fill
│   └── LGT-rim
└── COL-cameras
    ├── CAM-hero
    └── CAM-wide
```

```python
import bpy

# Create nested collections programmatically
character_col = bpy.data.collections.new('COL-character')
bpy.context.scene.collection.children.link(character_col)

body = bpy.data.objects['GEO-character_body']
character_col.objects.link(body)
bpy.context.scene.collection.objects.unlink(body)   # remove from parent
```

---

## File organization

### Single-project structure
```
project_root/
├── project.blend
├── assets/
│   ├── characters/
│   ├── environments/
│   └── props/
├── textures/
│   ├── diffuse/
│   ├── normal/
│   └── roughness/
├── hdri/
├── render/
│   ├── stills/
│   └── animation/
└── reference/
    └── concept_art/
```

### Studio multi-project
```
studio_root/
├── library/                # shared assets (linked from projects)
│   ├── characters/
│   ├── materials/
│   └── hdri/
├── projects/
│   ├── film_a/
│   │   ├── shots/
│   │   ├── assets/
│   │   └── render/
│   └── film_b/
└── tools/                  # studio scripts, addons
```

---

## Python performance (already covered in `wireframe-to-3d/references/best-practices.md`)

Key reminders:

### Use foreach_set / foreach_get
```python
# ❌ Slow: Python loop
for i, vert in enumerate(mesh.vertices):
    vert.co = positions[i]

# ✅ Fast: foreach_set (10–100× faster)
import numpy as np
flat = np.array(positions, dtype=np.float32).flatten()
mesh.vertices.foreach_set('co', flat)
```

### Cache context
```python
# ❌ Slow: API call each iteration
for _ in range(1000):
    bpy.context.view_layer.objects.active = obj

# ✅ Fast: cached reference
view_layer = bpy.context.view_layer
for _ in range(1000):
    view_layer.objects.active = obj
```

### Prefer bpy.data over bpy.ops
```python
# ❌ Slower: operator (UI updates, validation)
bpy.ops.object.shade_smooth()

# ✅ Faster: direct property
mesh.use_smooth = True
```

### Batch deletes
```python
# Build list first; delete after iteration finishes
to_delete = [obj for obj in bpy.data.objects if obj.name.startswith('Old_')]
for obj in to_delete:
    bpy.data.objects.remove(obj, do_unlink=True)
```

---

## Version control (Git)

Blender files are binary — Git LFS recommended for `.blend` files >10 MB.

### .gitignore essentials for Blender
```
# Auto-saves and backups
*.blend1
*.blend2
*.blend3
*.blend@

# Render output
render/
*.png
*.jpg
*.exr
!reference/**/*.png       # but keep reference images

# Temp files
*.tmp
*.swp

# Mac
.DS_Store

# Linux
.blender_history

# Blender packed files (these go IN .blend, not separately)
textures/
```

### Git LFS setup
```bash
git lfs install
git lfs track "*.blend"
git lfs track "*.exr"
git lfs track "*.psd"
```

### Commit message conventions for asset commits
```
asset: add hero character mesh
fix(rig): correct knee IK pole orientation
sim: bake fluid simulation 240 frames
render: golden hour lighting pass v3
docs: add character rig documentation
```

---

## Common scripting pitfalls

### Mode-aware operations
Many `bpy.ops.mesh.*` operations only work in Edit Mode:
```python
# ❌ Will error
bpy.ops.mesh.remove_doubles()

# ✅ Switch mode first
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.remove_doubles()
bpy.ops.object.mode_set(mode='OBJECT')
```

### Active object requirement
Some ops require an active object:
```python
# ❌ Active not set; ops may fail
bpy.ops.object.shade_smooth()

# ✅ Set active explicitly
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.shade_smooth()
```

### Headless (no UI) limitations
When running Blender in `--background` mode:
- `bpy.context.screen` doesn't exist
- Some operators fail (those that need GUI)
- Use `bpy.context.evaluated_depsgraph_get()` for rendered state

```python
# Headless rendering
import bpy

# Configure
bpy.context.scene.render.filepath = '/tmp/output_'
bpy.context.scene.render.image_settings.file_format = 'PNG'

# Render
bpy.ops.render.render(write_still=True)
```

### Override context for cross-area operators
Some operators run in a specific area context (Image Editor, Graph Editor):
```python
# Need to operate in the Compositor area
for window in bpy.context.window_manager.windows:
    for area in window.screen.areas:
        if area.type == 'NODE_EDITOR':
            with bpy.context.temp_override(window=window, area=area):
                bpy.ops.node.select_all(action='SELECT')
            break
```

---

## Pro habits to internalize

| Habit | Why |
|-------|-----|
| Always rename `Cube` to `GEO-meaningful_name` immediately after creation | Avoids "Cube.027" hell later |
| Apply rotation+scale before exporting | Avoids transform issues in target apps |
| Use Collections, not parenting, for grouping | More flexible, doesn't affect transforms |
| Save incremental versions (`scene_v01.blend`, `_v02`, ...) | Recovery from corruption / mistake rollback |
| Pack textures into .blend for sharing | `File → External Data → Pack All Into .blend` |
| Delete unused data (`File → Clean Up → Purge Unused`) | Keeps .blend files small |
| Comment Python scripts | Future-you will thank you |
| Use the Outliner search (`Find:`) | Faster than scrolling for items |

### Pack/unpack textures
```python
# Pack all external resources into .blend (for sharing)
bpy.ops.file.pack_all()

# Unpack to disk (when reorganizing)
bpy.ops.file.unpack_all(method='WRITE_LOCAL')
```

### Purge unused data
```python
# Remove orphan datablocks (unused materials, meshes, images, etc.)
bpy.ops.outliner.orphans_purge(do_recursive=True)
```

---

## Debugging tools

### Show Python tooltips
```
Preferences → Interface → Display → Python Tooltips: ON
```
Hover any UI element to see its Python path.

### Info Editor (operator history)
Window → Info Editor. Shows every operator you ran, with exact parameters. Copy-paste these into a script.

### Console
Window → Toggle System Console (Windows) or run Blender from terminal (Mac/Linux). All Python errors print here.

### `print()` and `breakpoint()`
Standard Python tools work in Blender's Python:
```python
import bpy
print(bpy.context.scene.objects.keys())   # logs to console
# breakpoint()    # only useful when running headless via PDB
```

### Driver debugging
Drivers can fail silently. Show driver errors:
```
Preferences → Editing → Allow Driver Python Expression: ON
```

---

## Sources

- [Asset Browser — Blender 5.1 Manual](https://docs.blender.org/manual/en/latest/editors/asset_browser.html)
- [Library Overrides — Blender Developer Docs](https://developer.blender.org/docs/features/core/overrides/library/functional_design/)
- [Blender Studio — Naming conventions](https://studio.blender.org/tools/naming-conventions/introduction)
- [Wikibooks — Blending Into Python: Optimize](https://en.wikibooks.org/wiki/Blender_3D:_Blending_Into_Python/Optimize)
- [Vagon — Using Python in Blender](https://vagon.io/blog/using-python-in-blender)

---

## Outstanding

- [ ] Distributed rendering setup (Cycles render farm)
- [ ] Custom Blender addon packaging
- [ ] Specific scripts: batch processing, automated thumbnails, asset validation
- [ ] Logging best practices for tool development
