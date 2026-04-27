---
name: blender-lighting
description: Light Blender scenes professionally — three-point setups, HDRI environments, studio/cinematic/dramatic configurations, light groups, color temperature, soft vs hard shadows. Use whenever the user asks to "light the scene", "set up lighting", "make it look cinematic / dramatic / studio / outdoor / sunset", "add a key light", "use HDRI", or any lighting-related request. Make sure to use this skill even if the user does not say "light" — also covers "make it look professional", "studio shot", "moody atmosphere", "golden hour", "rim light". Pairs with blender-materials (lighting reveals materials) and blender-cameras (lighting + composition together = shot).
when_to_use: Any lighting setup or modification in Blender. Includes HDRI/environment lighting and individual lamp placement.
allowed-tools: Read Bash mcp__blender__execute_blender_code mcp__blender__get_scene_info mcp__blender__get_object_info
---

# Blender Lighting

Light scenes the way pros do: with structure, intent, and physically reasonable values.

## The five light types

| Type | Behavior | Use for |
|------|----------|---------|
| **AREA** | Light from a rectangular surface; soft shadows automatic | 80% of cases. Window, softbox, fluorescent panel |
| **SUN** | Parallel rays from "infinity" | Sunlight, moonlight, distant directional |
| **POINT** | Omnidirectional from a point | Bulbs, candles, small omnis |
| **SPOT** | Cone with falloff | Stage lights, headlights, focused beams |
| **HDRI/World** | 360° environment image | Realistic ambient, outdoor, product photography |

**Default rule**: Use **Area lights** for almost everything except the sun. Soft shadows come for free.

## Decision tree

```
What's the mood?
├── Studio / commercial → Three-point lighting (key+fill+rim) + HDRI fill 0.3
├── Outdoor / sunlit → Sun + HDRI sky environment
├── Indoor cinematic → Sun through window + HDRI low + practicals (lamps as Point)
├── Dramatic / noir → Single Spot at high angle, no fill
├── Stylized / cartoon → Three-point with high contrast + saturated key color
└── Unsure → Three-point with HDRI grounding (works for 90% of cases)
```

## Recipes

### Helper: `aim_at(light, target)` — required for subject-aware lighting

Recipe 1 below positions lights at fixed world coords with hardcoded rotations. That's fine for a generic 1m subject at the world origin. For ANY other subject (small jewellery, tall sword, sprawling building), you need lights aimed at the subject. Use this helper:

```python
from mathutils import Vector

def aim_at(light_obj, target):
    """Aim a light at a world-space target.
    target may be a Vector or a tuple/list (x, y, z) or a Blender object.
    """
    target_pos = Vector(target.location) if hasattr(target, 'location') else Vector(target)
    direction = (target_pos - light_obj.location).normalized()
    light_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
```

### Helper: scene-aware light positioning

```python
from mathutils import Vector

def compute_scene_bbox_center(meshes):
    """Average bbox center over a list of mesh objects (world space)."""
    import bpy
    deps = bpy.context.evaluated_depsgraph_get()
    all_verts = []
    for o in meshes:
        eval_obj = o.evaluated_get(deps)
        em = eval_obj.to_mesh()
        for v in em.vertices:
            all_verts.append(o.matrix_world @ v.co)
        eval_obj.to_mesh_clear()
    xs = [v.x for v in all_verts]
    ys = [v.y for v in all_verts]
    zs = [v.z for v in all_verts]
    center = Vector(((min(xs)+max(xs))/2, (min(ys)+max(ys))/2, (min(zs)+max(zs))/2))
    extent = max(max(xs)-min(xs), max(ys)-min(ys), max(zs)-min(zs))
    return center, extent
```

### Recipe 0 — Three-point lighting **aimed at a subject** (preferred for orchestrator chains)

Use this instead of Recipe 1 when you have a specific subject. Lights are placed proportionally to the subject's largest dimension.

```python
import bpy, math
from mathutils import Vector

def aim_at(light_obj, target):
    target_pos = Vector(target.location) if hasattr(target, 'location') else Vector(target)
    direction = (target_pos - light_obj.location).normalized()
    light_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

# Determine subject and its scale
subject_meshes = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('GEO-')]
deps = bpy.context.evaluated_depsgraph_get()
all_verts = []
for o in subject_meshes:
    eo = o.evaluated_get(deps); em = eo.to_mesh()
    for v in em.vertices:
        all_verts.append(o.matrix_world @ v.co)
    eo.to_mesh_clear()
xs = [v.x for v in all_verts]; ys = [v.y for v in all_verts]; zs = [v.z for v in all_verts]
center = Vector(((min(xs)+max(xs))/2, (min(ys)+max(ys))/2, (min(zs)+max(zs))/2))
extent = max(max(xs)-min(xs), max(ys)-min(ys), max(zs)-min(zs))
light_dist = max(extent * 1.5, 1.0)

# Energy values scale roughly inversely with squared distance from subject — recipe targets
# physically reasonable values for a ~1m subject at ~1.5m light distance.
key_energy = 100 * (light_dist / 1.5) ** 2
fill_energy = key_energy * 0.3
rim_energy = key_energy * 0.8

# KEY (warm, front-right above)
key = bpy.data.objects.new('LGT-key', bpy.data.lights.new('LGT-key', type='AREA'))
key.data.energy = key_energy; key.data.size = 0.5; key.data.color = (1.0, 0.95, 0.85)
bpy.context.collection.objects.link(key)
key.location = (center.x + light_dist * 0.7, center.y - light_dist * 0.7, center.z + light_dist * 0.5)
aim_at(key, center)

# FILL (cool, opposite, weaker)
fill = bpy.data.objects.new('LGT-fill', bpy.data.lights.new('LGT-fill', type='AREA'))
fill.data.energy = fill_energy; fill.data.size = 1.0; fill.data.color = (0.85, 0.9, 1.0)
bpy.context.collection.objects.link(fill)
fill.location = (center.x - light_dist * 0.7, center.y - light_dist * 0.5, center.z + light_dist * 0.3)
aim_at(fill, center)

# RIM (cool, behind, separates subject from BG)
rim = bpy.data.objects.new('LGT-rim', bpy.data.lights.new('LGT-rim', type='SPOT'))
rim.data.energy = rim_energy; rim.data.color = (0.7, 0.85, 1.0); rim.data.spot_size = math.radians(50)
bpy.context.collection.objects.link(rim)
rim.location = (center.x, center.y + light_dist, center.z + light_dist * 0.5)
aim_at(rim, center)

print(f'lighting:three_point_aimed center={tuple(round(v,2) for v in center)} extent={extent:.2f}m dist={light_dist:.2f}m')
```

### Recipe 1 — Three-point lighting (the canonical setup)

```python
import bpy, math

# KEY LIGHT (warm, front-right)
key_data = bpy.data.lights.new('LGT-key', type='AREA')
key_data.energy = 1000
key_data.size = 1.0
key_data.color = (1.0, 0.95, 0.85)  # warm tungsten ~3200K
key = bpy.data.objects.new('LGT-key', key_data)
bpy.context.collection.objects.link(key)
key.location = (3, -3, 3.5)
key.rotation_euler = (math.radians(35), math.radians(45), 0)

# FILL LIGHT (cool, front-left, weaker)
fill_data = bpy.data.lights.new('LGT-fill', type='AREA')
fill_data.energy = 300
fill_data.size = 2.0
fill_data.color = (0.85, 0.9, 1.0)  # cool sky ~6500K
fill = bpy.data.objects.new('LGT-fill', fill_data)
bpy.context.collection.objects.link(fill)
fill.location = (-3, -2, 2.5)
fill.rotation_euler = (math.radians(50), math.radians(-45), 0)

# BACK / RIM LIGHT (cool, behind subject)
rim_data = bpy.data.lights.new('LGT-rim', type='SPOT')
rim_data.energy = 600
rim_data.spot_size = math.radians(40)
rim_data.color = (0.7, 0.85, 1.0)
rim = bpy.data.objects.new('LGT-rim', rim_data)
bpy.context.collection.objects.link(rim)
rim.location = (0, 4, 3.0)
rim.rotation_euler = (math.radians(120), 0, math.radians(180))

print('lighting:three_point')
```

**Standard ratios**:
- High-key (commercial): Key:Fill = 2:1
- Medium (portrait): 4:1
- Low-key (dramatic): 8:1+
- Rim: 50–100% of key

### Recipe 2 — HDRI environment

```python
import bpy

world = bpy.context.scene.world
world.use_nodes = True
nodes = world.node_tree.nodes
links = world.node_tree.links

# Wipe existing world nodes
for n in list(nodes):
    nodes.remove(n)

# Output → Background ← Environment Texture ← Mapping ← Texture Coordinate
output = nodes.new('ShaderNodeOutputWorld'); output.location = (300, 0)
bg = nodes.new('ShaderNodeBackground'); bg.location = (100, 0)
bg.inputs['Strength'].default_value = 1.0

env = nodes.new('ShaderNodeTexEnvironment'); env.location = (-100, 0)
env.image = bpy.data.images.load('/path/to/your.hdr')   # ← user provides path

mapping = nodes.new('ShaderNodeMapping'); mapping.location = (-300, 0)
tex_coord = nodes.new('ShaderNodeTexCoord'); tex_coord.location = (-500, 0)

links.new(tex_coord.outputs['Generated'], mapping.inputs['Vector'])
links.new(mapping.outputs['Vector'], env.inputs['Vector'])
links.new(env.outputs['Color'], bg.inputs['Color'])
links.new(bg.outputs['Background'], output.inputs['Surface'])
print('lighting:hdri')
```

**Pro source**: free HDRIs at [polyhaven.com/hdris](https://polyhaven.com/hdris) (CC0).

### Recipe 3 — Sunny outdoor

```python
import bpy, math

sun_data = bpy.data.lights.new('LGT-sun', type='SUN')
sun_data.energy = 5.0
sun_data.color = (1.0, 0.95, 0.8)  # golden hour
sun_data.angle = math.radians(0.5)  # realistic sun size; bigger = softer
sun = bpy.data.objects.new('LGT-sun', sun_data)
bpy.context.collection.objects.link(sun)
sun.location = (0, 0, 10)
sun.rotation_euler = (math.radians(45), math.radians(15), 0)
print('lighting:outdoor_sun')
```

Combine with HDRI sky environment (Recipe 2) for natural ambient fill.

### Recipe 4 — Indoor window light

```python
import bpy, math

# Sun coming through window — cool blue, sharp
sun_data = bpy.data.lights.new('LGT-window_sun', type='SUN')
sun_data.energy = 3.0
sun_data.color = (0.85, 0.9, 1.0)
sun_data.angle = math.radians(2.0)  # softer than direct sun
sun = bpy.data.objects.new('LGT-window_sun', sun_data)
bpy.context.collection.objects.link(sun)
sun.location = (5, -3, 4)
sun.rotation_euler = (math.radians(60), math.radians(-30), 0)

# Practical lamp — warm point light
lamp_data = bpy.data.lights.new('LGT-lamp', type='POINT')
lamp_data.energy = 60
lamp_data.color = (1.0, 0.7, 0.4)  # warm bulb
lamp = bpy.data.objects.new('LGT-lamp', lamp_data)
bpy.context.collection.objects.link(lamp)
lamp.location = (-1, 2, 1.5)
print('lighting:indoor_window')
```

### Recipe 5 — Dramatic single-source

```python
import bpy, math

spot_data = bpy.data.lights.new('LGT-drama', type='SPOT')
spot_data.energy = 800
spot_data.spot_size = math.radians(30)
spot_data.spot_blend = 0.3
spot_data.color = (1.0, 0.95, 0.85)
spot = bpy.data.objects.new('LGT-drama', spot_data)
bpy.context.collection.objects.link(spot)
spot.location = (2, -2, 6)
spot.rotation_euler = (math.radians(60), 0, 0)
print('lighting:dramatic')
```

For full noir: pair with strong volumetrics (atmosphere) — see `references/overview.md` for the volumetric setup.

### Recipe 6 — Color-temperature cheat sheet

| Source | RGB |
|--------|-----|
| Candle (1850K) | `(1.0, 0.6, 0.3)` |
| Tungsten (3200K) | `(1.0, 0.85, 0.6)` |
| LED warm (3000K) | `(1.0, 0.8, 0.6)` |
| Sunset / golden (3500K) | `(1.0, 0.85, 0.65)` |
| Daylight noon (5500K) | `(1.0, 1.0, 1.0)` |
| Overcast sky (6500K) | `(0.95, 0.95, 1.0)` |
| Blue hour (8000K) | `(0.8, 0.9, 1.0)` |

**Pro mix**: Warm key (tungsten) + cool fill (daylight) = the "golden/teal" Hollywood look.

### Recipe 7 — Soft vs hard shadow tweak

```python
import bpy, math

light_data = bpy.data.lights['LGT-key']

# Make shadows softer
light_data.size = 2.0     # Area: bigger size = softer shadow
# Or for Sun:
# light_data.angle = math.radians(5)  # bigger angle = softer shadow

# Make shadows harder (crisp)
# light_data.size = 0.1
# Or:
# light_data.angle = math.radians(0.5)
```

## Naming convention

| Prefix | Meaning |
|--------|---------|
| `LGT-key` | Main / key light |
| `LGT-fill` | Fill light |
| `LGT-rim` / `LGT-back` | Rim or back light |
| `LGT-sun` | Sun lamp |
| `LGT-{name}` | Practical lights (lamp, candle, neon, etc.) |

## Common pitfalls

| Symptom | Fix |
|---------|-----|
| Half the model in pitch black | Add fill (Area light or HDRI) |
| Render looks "flat" | Increase key:fill ratio; add rim |
| Hard shadows everywhere | Increase Area size or Sun angle |
| Too dark overall | Boost View Transform exposure or HDRI strength |
| No reflections on materials | Always set a world environment (HDRI) |
| Light inside object | Check world position; light must be visible from camera |
| Backlight blowing out subject | Rim energy ≤ key energy |

## When to load `references/overview.md`

Load when:
- The user asks for a setup not in the recipes (volumetric god rays, light groups, light linking)
- HDRI rotation / strength tuning is needed beyond defaults
- Multi-light scenes (5+ lamps) require organization
- Color science or color management gets specific (AgX, Filmic)

The reference covers: all 5 light types in depth, full HDRI workflow, light groups for re-lighting in compositor, recipes for product/portrait/architectural/character/animation looks.
