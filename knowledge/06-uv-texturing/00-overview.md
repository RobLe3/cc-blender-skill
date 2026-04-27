# UV Unwrapping + Texturing + Baking — Pro Knowledge Overview

**Domain**: 06 — UV unwrap, texel density, texture painting, baking maps  
**Status**: Initial pass complete  
**Last update**: 2026-04-27

---

## What UV unwrapping actually is

Mapping a 3D surface to 2D coordinates so a 2D image (texture) can be applied without distortion. Think of unfolding a cardboard box into its flat net.

**Why it matters**: every texture (diffuse, normal, ORM, baked AO) lives in 2D. Bad UVs = stretched textures, visible seams, wasted texture space.

---

## Unwrap method decision tree

```
What kind of mesh?
├── Hard-surface, mostly flat panels (boxes, weapons, vehicles)
│   → Smart UV Project (angle limit ~66°), then manual seam fixup
│
├── Organic / character (head, body, creatures)
│   → Manual seams + Unwrap (Conformal or Angle Based)
│   Place seams: hairline, behind ears, sole of foot, inside of arms
│
├── Architectural (walls, floors, repeated tiles)
│   → Cube Project or Project from View
│   Often combined with tiled textures and Texture Coordinate "Generated"
│
├── Cylindrical / spherical primitives
│   → Cylinder Project or Sphere Project
│
├── Subdivision Surface mesh (modeled at low poly with SubSurf)
│   → Unwrap the *base* (low poly) mesh; SubSurf interpolates the UVs
│
└── Quick prototype, doesn't need quality
    → Smart UV Project, accept defaults
```

---

## Seam placement strategy

**Rule from Blender Studio**: "It's generally better to place more seams rather than less. Stretching and uneven texel density is much more of an issue than what seams might cause."

**Where to place seams**:
- ✅ Hidden areas (back of head, inside legs, underside of objects)
- ✅ Existing edges that already break (corners of a box)
- ✅ Where color/material changes (boundary between leather and metal on a holster)
- ✅ Where high curvature meets low curvature

**Where NOT**:
- ❌ Across smooth surfaces visible from key angles (forehead, hood of a car)
- ❌ Right on silhouettes (they show up as visible cracks)
- ❌ In high-detail areas (eyes, mouth, intricate trim)

---

## Texel density (the most-overlooked concept)

**Texel density** = pixels per world unit. Uniform texel density = uniform texture quality across the model.

**Standard targets** (for game-ready assets):
| Asset type | Texel density | Texture sizing |
|------------|--------------|----------------|
| Hero character (close-up) | 1024–2048 px/m | 4K texture for body, 2K for accessories |
| NPC | 512–1024 px/m | 2K texture |
| Environment props | 256–512 px/m | 1K-2K texture |
| Background scenery | 128–256 px/m | 512–1K texture |
| Mobile / lightweight | 64–128 px/m | 512 texture |

**Achieving uniform density**:
1. Unwrap → all islands fill UV space organically.
2. `UV → Average Islands Scale` (Edit Mode UV editor) — equalizes texel density across all islands.
3. `UV → Pack Islands` — efficient layout in 0–1 UV square.
4. **Verify with checker texture**: load a checkerboard image, all squares should look ≈ same size on the surface.

```python
# Set up checker texture for visual verification
import bpy

obj = bpy.data.objects['GEO-character']
mat = bpy.data.materials.new('MAT-checker')
mat.use_nodes = True
nodes = mat.node_tree.nodes
checker = nodes.new('ShaderNodeTexChecker')
links = mat.node_tree.links
bsdf = nodes['Principled BSDF']
links.new(checker.outputs['Color'], bsdf.inputs['Base Color'])
checker.inputs['Scale'].default_value = 50  # tune by eye
obj.data.materials.append(mat)
```

---

## Pro unwrap workflow (step-by-step)

```python
import bpy

obj = bpy.data.objects['GEO-character']
bpy.context.view_layer.objects.active = obj
bpy.ops.object.mode_set(mode='EDIT')

# 1. Mark seams (manually selected edges)
bpy.ops.mesh.select_all(action='DESELECT')
# ... user selects edge loops ...
bpy.ops.mesh.mark_seam(clear=False)

# 2. Select all faces
bpy.ops.mesh.select_all(action='SELECT')

# 3. Unwrap (Angle Based or Conformal)
bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)

# 4. Equalize texel density
bpy.ops.uv.average_islands_scale()

# 5. Pack into 0–1 square
bpy.ops.uv.pack_islands(margin=0.005)

bpy.ops.object.mode_set(mode='OBJECT')
```

**Margins matter**: `margin=0.005` (0.5%) prevents bleed between islands at low texture resolutions. Higher margins waste UV space; lower margins risk bleed.

---

## Baking maps (what to bake, when)

| Map type | Bakes from | Bakes to | Used for |
|----------|-----------|----------|----------|
| **Diffuse** | Painted/procedural color | Image texture | Albedo |
| **Normal (tangent)** | High-poly mesh | Normal map | Surface detail without polys |
| **AO (Ambient Occlusion)** | Geometry self-occlusion | Greyscale image | Crevice darkening |
| **Roughness** | Procedural roughness shader | Greyscale | PBR roughness input |
| **Metallic** | Procedural metallic mask | Greyscale | PBR metallic input |
| **Emit** | Emission shader | Color image | Glow effects |
| **Combined** | Final cycles render | Image | Lightmap baking |

### Bake setup recipe
```python
import bpy

# 1. Set Cycles as render engine (baking primarily uses Cycles)
bpy.context.scene.render.engine = 'CYCLES'

# 2. Configure bake type
scene = bpy.context.scene
scene.cycles.bake_type = 'NORMAL'   # or 'DIFFUSE', 'AO', etc.

# 3. Setup target image
target_img = bpy.data.images.new('GEO-character_normal', 2048, 2048, alpha=False, float_buffer=True)

# 4. Add Image Texture node to material, point at target
mat = bpy.data.materials['MAT-character']
nodes = mat.node_tree.nodes
img_node = nodes.new('ShaderNodeTexImage')
img_node.image = target_img
nodes.active = img_node     # bake target = active image node

# 5. For high → low bake: select high, then low (active is bake target)
# bpy.context.view_layer.objects.active = low_poly  # active = target
# high_poly.select_set(True)
# low_poly.select_set(True)

# 6. Bake
bpy.ops.object.bake(
    type='NORMAL',
    use_selected_to_active=True,  # high → low
    cage_extrusion=0.05,
    margin=16,
    save_mode='EXTERNAL',
)

# 7. Save
target_img.filepath_raw = '/tmp/GEO-character_normal.png'
target_img.file_format = 'PNG'
target_img.save()
```

### Cage explained
A "cage" is an inflated copy of the low-poly mesh that defines how far each ray travels when sampling the high-poly. Without a cage, baking from concave or thin areas creates artifacts (rays miss the high-poly surface).

`cage_extrusion = thickest detail size` is a good rule. For most characters, 0.05–0.1m works.

---

## ORM packed map (industry standard for game export)

Pack three greyscale maps into one RGB image:
- **R** = Ambient Occlusion
- **G** = Roughness
- **B** = Metallic

This is what the glTF 2.0 spec expects for `metallicRoughnessTexture`. Single texture, three values, smaller export.

**To pack**: bake AO, Roughness, Metallic separately, then combine in compositor or external (Photoshop/GIMP/ImageMagick).

```bash
# ImageMagick one-liner
magick AO.png Roughness.png Metallic.png -channel-fx '[0]->R, [1]->G, [2]->B' ORM.png
```

---

## Live Unwrap (the time-saver)

**What it does**: while you edit the 3D mesh, the UV map updates in real time. Pin UV vertices in 2D, then tweak 3D mesh — UVs adjust to maintain pinned positions.

```python
# Toggle live unwrap
bpy.context.scene.tool_settings.use_uv_select_sync = True
# Then: Edit Mode → UV menu → Live Unwrap
```

Useful for: aligning a UV island to a grid, straightening rows of vertices on a face for clean texture lay-down.

---

## Texture painting basics

Blender has built-in texture painting (Edit Mode → switch to Texture Paint tab):

```python
# Quick setup for paint mode
import bpy

obj = bpy.data.objects['GEO-character']
bpy.context.view_layer.objects.active = obj

# Add an empty image to paint on
img = bpy.data.images.new('paint_layer', 2048, 2048)
mat = bpy.data.materials.new('MAT-paint')
mat.use_nodes = True
img_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
img_node.image = img
mat.node_tree.links.new(
    img_node.outputs['Color'],
    mat.node_tree.nodes['Principled BSDF'].inputs['Base Color']
)
obj.data.materials.append(mat)

# Switch to Texture Paint mode
bpy.ops.object.mode_set(mode='TEXTURE_PAINT')
```

**Pro tip**: For serious texturing work, **Substance Painter** or **Mari** are industry standard. Blender's painting works for prototyping and stylized art.

---

## Common pitfalls

| Mistake | Fix |
|---------|-----|
| Stretched textures on parts of mesh | Better seams, then `Average Islands Scale` |
| Visible seams as bright/dark lines | Increase bake `margin`, check normals consistency |
| Wasted UV space (small islands floating) | Pack with appropriate `margin` |
| Texel density wildly uneven | Always run `Average Islands Scale` after unwrap |
| Subdivision Surface UVs look bad | Unwrap base mesh BEFORE applying SubSurf, not after |
| Normal map looks inverted | Texture is sRGB; must be set to "Non-Color" |
| Bake fails with "no active image" | Add Image Texture node to material, mark it active |
| Bake from high to low has cage artifacts | Increase `cage_extrusion` or use a manual cage object |

---

## Sources

- [A UV Unwrapping Guide — Blender Studio](https://studio.blender.org/blog/a-uv-unwrapping-guide/)
- [Seams — Blender 5.1 Manual](https://docs.blender.org/manual/en/latest/modeling/meshes/uv/unwrapping/seams.html)
- [CG Cookie — 26 UV Unwrapping Tips for Subdivision Surfaces](https://cgcookie.com/posts/essential-blender-tips-for-uv-unwrapping-subdivision-surfaces)
- [Blender Studio — Fundamentals 4.5 LTS: UV Unwrapping](https://studio.blender.org/training/blender-fundamentals-45-lts/blender_4-5_lts_what-is-unwrapping/)
- [Polycount — Smart UV Tool addon discussion](https://polycount.com/discussion/238062/blender-add-on-smart-uv-tool-fast-clean-uvs-for-dense-meshes)
- [Khronos glTF 2.0 spec — metallicRoughnessTexture (ORM)](https://github.com/KhronosGroup/glTF/tree/master/specification/2.0)

---

## Outstanding

- [ ] Tile-based UV layouts (UDIM)
- [ ] Box-mapping for hard-surface and architecture
- [ ] Bake-with-AO-included workflow for stylized look
- [ ] UV layout export for hand-painting in Photoshop/Krita
