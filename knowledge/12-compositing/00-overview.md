# Compositing — Pro Knowledge Overview

**Domain**: 12 — Compositor, render passes, color grading, post-processing  
**Status**: Initial pass complete  
**Last update**: 2026-04-27

---

## What compositing is

Post-processing the rendered image with node-based filters: combining render passes, color grading, adding effects (glare, bloom, lens distortion, vignette), masking, comping over backgrounds.

**Why use Blender's compositor instead of external tools (Photoshop/After Effects/Nuke)**:
- Stays in the same project (no roundtrip)
- Re-renders update automatically
- Per-pass access (relight in compositor, not re-render)
- No license cost

---

## The compositor workflow

```
Render Layers node (your render output)
       ↓
[ pass-specific manipulation ]
       ↓
Color Balance / Curves / Hue/Saturation
       ↓
Glare / Bloom / Vignette / Lens Distortion
       ↓
Composite node (final output) + Viewer node (preview)
```

**Always have**:
- A `Render Layers` node (the input)
- A `Composite` node (saves to final image)
- A `Viewer` node (preview in compositor — `Shift+Click` on any node's output to redirect)

---

## Render passes (AOVs)

Render passes split your image into separate layers. You can manipulate each independently.

**Built-in passes** (enable in View Layer Properties → Passes):

| Pass | What it shows | Use |
|------|--------------|-----|
| **Combined** | Final beauty render | Default output |
| **Z (Depth)** | Distance from camera | DoF in compositor, fog |
| **Mist** | Atmospheric haze | Faster than volumetrics |
| **Normal** | Surface normals as RGB | Fake relighting, edge enhance |
| **Vector** | Motion vectors | Motion blur in compositor |
| **UV** | UV coordinates | Texture re-projection |
| **Diffuse Direct/Indirect/Color** | Diffuse light components | Re-light without re-render |
| **Glossy Direct/Indirect/Color** | Specular components | Boost reflections in post |
| **Transmission** | Glass / refraction | Composite glass separately |
| **Emission** | Self-lit surfaces | Boost emissives without affecting other lighting |
| **Ambient Occlusion** | Self-shadowing | Crevice darkening |
| **Cryptomatte** | Per-object masks | Surgical color correction |

```python
import bpy

view_layer = bpy.context.view_layer
view_layer.use_pass_z = True
view_layer.use_pass_normal = True
view_layer.use_pass_diffuse_direct = True
view_layer.use_pass_diffuse_indirect = True
view_layer.use_pass_diffuse_color = True
view_layer.use_pass_glossy_direct = True
view_layer.use_pass_emit = True
view_layer.use_pass_ambient_occlusion = True
```

---

## Custom AOVs (your own passes)

Beyond built-in passes, you can create custom AOVs from material shaders.

```python
import bpy

# 1. Add AOV to View Layer
view_layer = bpy.context.view_layer
aov = view_layer.aovs.add()
aov.name = 'AOV-character_id'
aov.type = 'COLOR'    # 'COLOR' or 'VALUE'

# 2. In a material's shader graph, add 'AOV Output' node
mat = bpy.data.materials['MAT-character']
mat.use_nodes = True
nodes = mat.node_tree.nodes
aov_out = nodes.new('ShaderNodeOutputAOV')
aov_out.aov_name = 'AOV-character_id'

# Wire constant color to it (or any value)
rgb = nodes.new('ShaderNodeRGB')
rgb.outputs[0].default_value = (1.0, 0.0, 0.0, 1.0)
mat.node_tree.links.new(rgb.outputs['Color'], aov_out.inputs['Color'])
```

In compositor: `Render Layers` node now has an output for `AOV-character_id`. Use it as a mask.

**Limit**: 16 Color AOVs + 16 Value AOVs per render layer.

---

## Cryptomatte (surgical masking)

Cryptomatte gives you **per-object** or **per-material** masks automatically — no manual setup needed.

```python
import bpy

view_layer = bpy.context.view_layer
view_layer.use_pass_cryptomatte_object = True
view_layer.use_pass_cryptomatte_material = True
view_layer.use_pass_cryptomatte_asset = True
view_layer.pass_cryptomatte_depth = 6   # how many "layers" of masks
```

In compositor: `Cryptomatte V2` node lets you click-pick objects from the rendered image to generate clean masks.

**Use case**: change the color of one specific object after render, no re-render needed.

---

## Color grading basics

### Color Balance (3-way color corrector)
Standard pro tool. Three controls: Lift (shadows), Gamma (midtones), Gain (highlights).

```
Render Layers ─→ Color Balance ─→ Composite
                  ├─ Lift: cool shadows blue
                  ├─ Gamma: neutral
                  └─ Gain: warm highlights orange
                  
Result: "Hollywood teal/orange" look
```

### Curves
Most powerful color tool. RGB master curve + per-channel R/G/B curves.

**Standard curves moves**:
- **S-curve on master** = increase contrast (lift highlights, drop shadows)
- **Lift the bottom of red** = warm shadows
- **Drop the top of blue** = warm highlights
- **Anchor middle, lift quarter-tones** = lift skin tones without affecting black/white

### Hue/Saturation/Value
For broad color adjustments and saturation tweaks.

### LUTs (Color Lookup Tables)
For applying graded looks. Blender's compositor doesn't natively support .cube LUTs (3.5+ in viewport but not compositor). External tool needed.

---

## Glare node (the bloom/streaks classic)

```
Render Layers ─→ Glare ─→ Composite
                  ├─ Type: 'BLOOM'    (soft glow)
                  ├─ Type: 'STREAKS'  (lens streaks)
                  ├─ Type: 'GHOSTS'   (lens ghosts)
                  ├─ Type: 'FOG_GLOW' (atmospheric haze around bright)
                  └─ Type: 'SIMPLE_STAR' (4-point star burst)
```

Settings:
- **Threshold** = which pixels qualify (0–1.5; 1.0 is "white"). Lower = more pixels glow.
- **Quality** = 'High' for production, 'Medium' for preview
- **Mix** = 0 (just the glare) to 1 (mixed back with original); typical 0.5

```python
import bpy

scene = bpy.context.scene
scene.use_nodes = True
nodes = scene.node_tree.nodes
links = scene.node_tree.links

render = nodes['Render Layers']
composite = nodes['Composite']

glare = nodes.new('CompositorNodeGlare')
glare.glare_type = 'BLOOM'
glare.threshold = 1.0
glare.quality = 'HIGH'
glare.mix = 0.0    # additive

links.new(render.outputs['Image'], glare.inputs['Image'])
links.new(glare.outputs['Image'], composite.inputs['Image'])
```

---

## Lens Distortion

Simulates real-camera lens imperfections:

| Property | Effect |
|----------|--------|
| **Distort** (-1 to 1) | Pincushion (negative) or barrel (positive) distortion |
| **Dispersion** (0 to 1) | Chromatic aberration (color fringing on edges) |
| **Jitter** | Noise / shake |
| **Fit** | Auto-crop to original frame size |

```python
distort = nodes.new('CompositorNodeLensdist')
distort.use_jitter = False
distort.use_fit = True

distort.inputs['Distort'].default_value = -0.05    # subtle barrel
distort.inputs['Dispersion'].default_value = 0.005 # subtle chromatic aberration
```

**Pro tip**: real lenses have distortion AND dispersion. Adding both at low values (~0.05 distort, ~0.005 dispersion) instantly makes a render feel like it came from a real camera.

---

## Vignette (darken edges)

Several ways:

### Method A: Lens Distortion + crop (cheap)
Use a Mask + Color → Mix in Multiply mode.

### Method B: Vignette via Ellipse Mask
```
Render Layers → Mix (Multiply with mask) → Composite
                       ↑
                Ellipse Mask (inverted, soft falloff)
```

### Method C: Color Balance with mask
For a subtle dark+desaturated edge instead of pure black vignette.

---

## Compositing pipeline (production grade)

```
Render Layers
   │
   ├── Beauty (Combined)
   │
   ├── Diffuse_Direct ─┐
   ├── Diffuse_Indirect ─┴── Mix → boost interior bounces
   │
   ├── Glossy_Direct ─── Mix → boost reflections
   │
   ├── Z (Depth) ──── Defocus → DoF (alternative to camera DoF)
   │
   └── Cryptomatte ─── pick objects → color-correct selectively

   ↓ All combined
   
   → Color Balance (broad grade)
   → Curves (S-curve contrast, color tweaks)
   → Glare (bloom/streaks)
   → Lens Distortion (subtle)
   → Vignette
   → Composite
```

**Each step is non-destructive**. Dial back at any point.

---

## Exporting compositor output

By default, `Composite` node writes to the final render. To save intermediate versions or multiple variants:

### File Output node
```python
file_out = nodes.new('CompositorNodeOutputFile')
file_out.base_path = '/tmp/render/'
file_out.format.file_format = 'PNG'
file_out.format.color_mode = 'RGBA'
file_out.format.color_depth = '16'

# Add slots for multiple outputs
file_out.file_slots.new('beauty_')
file_out.file_slots.new('diffuse_only_')
```

Each slot writes a separate file per render — great for managing versions.

---

## Real-time vs full compositor

Blender 3.5+ has a **Real-time Compositor** (viewport overlay):
- Runs at viewport FPS
- Subset of nodes supported (no Cryptomatte, limited Glare)
- Useful for previewing post-effects without full render

Full compositor (after render) is the "final pass" used for production output.

```python
# Enable real-time compositor in viewport
space = bpy.context.space_data
space.shading.use_compositor = 'ALWAYS'   # 'DISABLED', 'CAMERA', 'ALWAYS'
```

---

## Common pitfalls

| Mistake | Why | Fix |
|---------|-----|-----|
| Heavy color grade in Standard view transform | Blown highlights, neon colors | Use AgX or Filmic; grade on top |
| Too much bloom | Looks like a 2010 video game | Mix factor ≤ 0.3 typical |
| Vignette fully black at edge | Crushes image | Stop at 30–50% darkness for natural look |
| Not enabling needed render passes | Compositor missing inputs | Enable passes BEFORE rendering, not after |
| Compositor enabled but no `Composite` node | "Why is my render black?" | Add a Composite node, wire inputs |
| Heavy real-time compositor | Tanks viewport FPS | Disable for animation; use only for stills |
| Wrong color space on file output | Wrong colors when re-imported | Match output space to your view transform |

---

## Sources

- [Render Passes — Blender 5.1 Manual](https://docs.blender.org/manual/en/latest/render/layers/passes.html)
- [Blender Developers Blog — Real-time Compositor](https://code.blender.org/2022/07/real-time-compositor/)
- [Creative Shrimp — 9 Tips for Real-time Compositor](https://www.creativeshrimp.com/blender-3-5-realtime-compositor.html)
- [Artisticrender — 12 post-processing effects to enhance Blender renders](https://artisticrender.com/top-12-post-processing-effects-to-enhance-your-blender-renders/)
- [Blended Boris — Cinematic color grading in Blender](https://blendedboris.com/our-blog/tpost/color-grading-in-blender)
- [LinkedIn — Best practices for color grading in Blender](https://www.linkedin.com/advice/0/what-best-color-grading-practices-blenders-post-processing-zrj6f)

---

## Outstanding

- [ ] LUT-based grading (external pipeline)
- [ ] Specific style recipes (Wes Anderson, noir, retro VHS)
- [ ] Multi-pass workflow for relighting
- [ ] Defocus (Z-pass DoF) detailed setup
