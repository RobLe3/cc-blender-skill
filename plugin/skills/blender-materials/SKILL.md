---
name: blender-materials
description: Create and assign PBR materials in Blender via Principled BSDF — metals, glass, plastic, fabric, skin, organics. Covers physically-based material recipes with real-world values, Coat layer (varnish/car paint), Sheen (cloth), Subsurface scattering (skin/wax), Transmission (glass), and procedural patterns (wood grain, marble, fabric weave). Use whenever the user asks to "make it look like X material", "give it a metallic finish", "apply a wood texture", "make this glass / plastic / brushed steel / leather / skin", or any look-development request. Make sure to use this skill even if the user does not say "material" — also covers "make it shiny", "matte finish", "looks like copper", "rough surface". Works with any geometry; pairs with blender-lighting (materials only look right under proper lighting).
when_to_use: Any material assignment, PBR setup, shader work, or look-dev request in Blender.
allowed-tools: Read Bash mcp__blender__execute_blender_code mcp__blender__get_scene_info mcp__blender__get_object_info
---

# Blender Materials

Apply physically-based materials to objects. Use **only Principled BSDF** — it's the only shader that exports cleanly to glTF and matches what other DCC tools expect.

## The metallic switch — never an in-between

The single most-important rule: **Metallic is a switch, not a slider.** Set it to `0.0` (dielectric: plastic, wood, glass, skin) or `1.0` (metal: steel, gold, copper). Values between 0.2 and 0.8 are almost always wrong; they produce energy-non-conservative renders that look "plasticky."

Exception: dark mirror lenses (sunglasses) use ~0.8 to combine strong reflection with slight tint — that's a stylistic choice, not strict PBR.

## Decision tree

```
What is it made of?
├── Raw metal (steel, gold, copper, etc.)
│   → Metallic=1.0, Base Color = F0 reflectance from physicallybased.info
│   → Roughness controls polish (0.05 mirror → 0.4 brushed → 0.7+ weathered)
│
├── Glass / clear / refractive
│   → Metallic=0, Transmission=1.0, IOR=1.5 (glass), Roughness=0.0
│   → Add Volume Absorption for thick tinted glass
│
├── Plastic / wood / stone (dielectric, opaque)
│   → Metallic=0, IOR=1.45 (plastic) or 1.5 (most others)
│   → Roughness per finish (0.15 glossy / 0.6 matte)
│   → Coat Weight 0.5+ for varnished/lacquered surfaces
│
├── Skin / wax / marble (subsurface scattering)
│   → Metallic=0, Subsurface Weight=1.0
│   → Subsurface Radius RGB tuned per material (skin: red scatters deepest)
│
├── Cloth / fabric (sheen)
│   → Metallic=0, Sheen Weight 0.2-0.5
│   → Roughness 0.6+, Sheen Roughness 0.5
│
└── Mirror / chrome (special metal)
    → Metallic=1.0, Roughness=0.02-0.05, near-white base
```

## Recipes (the 12 to know)

Each recipe creates the material and assigns it to a target object. Replace `'GEO-target'` with your actual object name.

### Recipe 1 — Brushed steel
```python
import bpy

mat = bpy.data.materials.new('MAT-steel_brushed')
mat.use_nodes = True
bsdf = mat.node_tree.nodes['Principled BSDF']
bsdf.inputs['Base Color'].default_value = (0.56, 0.57, 0.58, 1.0)
bsdf.inputs['Metallic'].default_value = 1.0
bsdf.inputs['Roughness'].default_value = 0.25

obj = bpy.data.objects['GEO-target']
if obj.data.materials:
    obj.data.materials[0] = mat
else:
    obj.data.materials.append(mat)
print(f"material:MAT-steel_brushed→{obj.name}")
```

### Recipe 2 — Polished gold
```python
import bpy
mat = bpy.data.materials.new('MAT-gold_polished')
mat.use_nodes = True
bsdf = mat.node_tree.nodes['Principled BSDF']
bsdf.inputs['Base Color'].default_value = (1.022, 0.782, 0.344, 1.0)
bsdf.inputs['Metallic'].default_value = 1.0
bsdf.inputs['Roughness'].default_value = 0.05
bpy.data.objects['GEO-target'].data.materials.append(mat)
print('material:gold_polished')
```

### Recipe 3 — Polished copper
```python
import bpy
mat = bpy.data.materials.new('MAT-copper_polished')
mat.use_nodes = True
bsdf = mat.node_tree.nodes['Principled BSDF']
bsdf.inputs['Base Color'].default_value = (0.926, 0.721, 0.504, 1.0)
bsdf.inputs['Metallic'].default_value = 1.0
bsdf.inputs['Roughness'].default_value = 0.05
bpy.data.objects['GEO-target'].data.materials.append(mat)
print('material:copper_polished')
```

### Recipe 4 — Mirror chrome
```python
import bpy
mat = bpy.data.materials.new('MAT-chrome')
mat.use_nodes = True
bsdf = mat.node_tree.nodes['Principled BSDF']
bsdf.inputs['Base Color'].default_value = (0.55, 0.56, 0.55, 1.0)
bsdf.inputs['Metallic'].default_value = 1.0
bsdf.inputs['Roughness'].default_value = 0.02
bpy.data.objects['GEO-target'].data.materials.append(mat)
print('material:chrome')
```

### Recipe 5 — Clear glass
```python
import bpy
mat = bpy.data.materials.new('MAT-glass_clear')
mat.use_nodes = True
bsdf = mat.node_tree.nodes['Principled BSDF']
bsdf.inputs['Base Color'].default_value = (1.0, 1.0, 1.0, 1.0)
bsdf.inputs['Metallic'].default_value = 0.0
bsdf.inputs['Roughness'].default_value = 0.0
bsdf.inputs['Transmission Weight'].default_value = 1.0
bsdf.inputs['IOR'].default_value = 1.5
bpy.data.objects['GEO-target'].data.materials.append(mat)
print('material:glass_clear')
```

### Recipe 6 — Frosted glass
```python
import bpy
mat = bpy.data.materials.new('MAT-glass_frosted')
mat.use_nodes = True
bsdf = mat.node_tree.nodes['Principled BSDF']
bsdf.inputs['Base Color'].default_value = (1.0, 1.0, 1.0, 1.0)
bsdf.inputs['Transmission Weight'].default_value = 1.0
bsdf.inputs['IOR'].default_value = 1.5
bsdf.inputs['Roughness'].default_value = 0.3
bpy.data.objects['GEO-target'].data.materials.append(mat)
print('material:glass_frosted')
```

### Recipe 7 — Matte plastic (red)
```python
import bpy
mat = bpy.data.materials.new('MAT-plastic_matte_red')
mat.use_nodes = True
bsdf = mat.node_tree.nodes['Principled BSDF']
bsdf.inputs['Base Color'].default_value = (0.8, 0.1, 0.05, 1.0)
bsdf.inputs['Metallic'].default_value = 0.0
bsdf.inputs['Roughness'].default_value = 0.6
bsdf.inputs['IOR'].default_value = 1.45
bpy.data.objects['GEO-target'].data.materials.append(mat)
print('material:plastic_matte_red')
```

### Recipe 8 — Lacquered plastic (car-paint look)
```python
import bpy
mat = bpy.data.materials.new('MAT-plastic_lacquered')
mat.use_nodes = True
bsdf = mat.node_tree.nodes['Principled BSDF']
bsdf.inputs['Base Color'].default_value = (0.8, 0.1, 0.05, 1.0)
bsdf.inputs['Metallic'].default_value = 0.0
bsdf.inputs['Roughness'].default_value = 0.15
bsdf.inputs['IOR'].default_value = 1.45
bsdf.inputs['Coat Weight'].default_value = 0.8
bsdf.inputs['Coat Roughness'].default_value = 0.05
bpy.data.objects['GEO-target'].data.materials.append(mat)
print('material:plastic_lacquered')
```

### Recipe 9 — Skin (light tone)
```python
import bpy
mat = bpy.data.materials.new('MAT-skin_light')
mat.use_nodes = True
bsdf = mat.node_tree.nodes['Principled BSDF']
bsdf.inputs['Base Color'].default_value = (0.85, 0.65, 0.55, 1.0)
bsdf.inputs['Metallic'].default_value = 0.0
bsdf.inputs['Roughness'].default_value = 0.4
bsdf.inputs['Subsurface Weight'].default_value = 1.0
bsdf.inputs['Subsurface Radius'].default_value = (1.0, 0.2, 0.1)
bsdf.inputs['Subsurface IOR'].default_value = 1.4
bpy.data.objects['GEO-target'].data.materials.append(mat)
print('material:skin_light')
```

### Recipe 10 — Velvet / cloth with sheen
```python
import bpy
mat = bpy.data.materials.new('MAT-velvet_red')
mat.use_nodes = True
bsdf = mat.node_tree.nodes['Principled BSDF']
bsdf.inputs['Base Color'].default_value = (0.6, 0.0, 0.1, 1.0)
bsdf.inputs['Roughness'].default_value = 0.9
bsdf.inputs['Sheen Weight'].default_value = 0.5
bsdf.inputs['Sheen Roughness'].default_value = 0.5
bsdf.inputs['Sheen Tint'].default_value = (0.8, 0.6, 0.6, 1.0)
bpy.data.objects['GEO-target'].data.materials.append(mat)
print('material:velvet_red')
```

### Recipe 11 — Soft silicone
```python
import bpy
mat = bpy.data.materials.new('MAT-silicone')
mat.use_nodes = True
bsdf = mat.node_tree.nodes['Principled BSDF']
bsdf.inputs['Base Color'].default_value = (0.65, 0.63, 0.60, 1.0)
bsdf.inputs['Metallic'].default_value = 0.0
bsdf.inputs['Roughness'].default_value = 0.7
bsdf.inputs['IOR'].default_value = 1.4
bpy.data.objects['GEO-target'].data.materials.append(mat)
print('material:silicone')
```

### Recipe 12 — Procedural wood (10 nodes)
```python
import bpy

mat = bpy.data.materials.new('MAT-wood_procedural')
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links

bsdf = nodes['Principled BSDF']

# Texture coordinate
tex_coord = nodes.new('ShaderNodeTexCoord')
tex_coord.location = (-800, 0)

# Mapping
mapping = nodes.new('ShaderNodeMapping')
mapping.location = (-600, 0)
mapping.inputs['Scale'].default_value = (3, 3, 3)

# Wave (the grain)
wave = nodes.new('ShaderNodeTexWave')
wave.location = (-400, 100)
wave.wave_type = 'BANDS'
wave.bands_direction = 'X'
wave.inputs['Scale'].default_value = 5.0
wave.inputs['Distortion'].default_value = 4.0

# Noise (variation)
noise = nodes.new('ShaderNodeTexNoise')
noise.location = (-400, -100)
noise.inputs['Scale'].default_value = 8.0

# Mix wave + noise
mix = nodes.new('ShaderNodeMixRGB')
mix.location = (-200, 0)
mix.blend_type = 'MULTIPLY'
mix.inputs[0].default_value = 0.5

# ColorRamp (tonal range)
ramp = nodes.new('ShaderNodeValToRGB')
ramp.location = (0, 0)
ramp.color_ramp.elements[0].color = (0.15, 0.07, 0.03, 1.0)  # dark wood
ramp.color_ramp.elements[1].color = (0.6, 0.35, 0.18, 1.0)   # light wood

# Wire
links.new(tex_coord.outputs['Generated'], mapping.inputs['Vector'])
links.new(mapping.outputs['Vector'], wave.inputs['Vector'])
links.new(mapping.outputs['Vector'], noise.inputs['Vector'])
links.new(wave.outputs['Color'], mix.inputs[1])
links.new(noise.outputs['Color'], mix.inputs[2])
links.new(mix.outputs['Color'], ramp.inputs['Fac'])
links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])

bsdf.inputs['Roughness'].default_value = 0.7

bpy.data.objects['GEO-target'].data.materials.append(mat)
print('material:wood_procedural')
```

**Note**: procedural materials don't export to glTF. For web/game export, bake to image textures first.

## PBR values reference

For exact F0 reflectance values for any metal: [physicallybased.info](https://physicallybased.info/) — covers 50+ materials. The recipes above use values from this database.

## Material naming convention

`MAT-{purpose}_{subtype}_{finish}`. Examples:
- `MAT-frame_metal_brushed`
- `MAT-lens_glass_dark_mirror`
- `MAT-pad_silicone_warm_gray`
- `MAT-wood_oak_glossy`

Avoid `Material.001`, `Material.027`. Always rename.

## Common pitfalls

| Symptom | Fix |
|---------|-----|
| "Plasticky" metals | Metallic must be exactly 0 or 1 |
| Black metal | Base color too dark; metals reflect 30–100%; keep ≥0.5 sRGB |
| Roughness 0 = artifacts | Use 0.01–0.05 minimum |
| Glass renders black | Increase Cycles transmission bounces (Recipe section 11-rendering) |
| Material not visible in glTF | Procedural shader; bake to image first |
| Normal map looks wrong | Set image texture to "Non-Color" color space |
| sRGB on roughness map | Set image texture to "Non-Color" |

## When to load `references/overview.md`

Load when:
- The recipe you need isn't in the 12 above
- You need anisotropy (brushed metal direction), volume absorption (tinted thick glass), or advanced shader-node combos
- The user asks for material variation across one mesh (Mix Shader patterns)
- You're baking procedural to image textures for export

The reference covers: full Principled BSDF parameter map, 50+ materials database link, procedural texture combinations (Voronoi, Wave, Noise), Sheen + Subsurface deep-dives, and bake-for-export workflow.
