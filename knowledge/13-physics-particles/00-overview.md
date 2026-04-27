# Physics + Particles — Pro Knowledge Overview

**Domain**: 13 — Rigid body, soft body, cloth, fluid (Mantaflow), particles, hair  
**Status**: Initial pass complete  
**Last update**: 2026-04-27

---

## The 8 simulation systems

| System | Use | Solver |
|--------|-----|--------|
| **Rigid Body** | Hard objects colliding (boxes, debris, brick walls) | Bullet |
| **Soft Body** | Squishy deformable (jelly, mattress, simple cloth) | Mass-spring |
| **Cloth** | Realistic fabric (shirts, flags, capes) | Mass-spring + collision |
| **Fluid (Liquid)** | Water, splashes, drips | Mantaflow FLIP solver |
| **Fluid (Smoke/Fire)** | Smoke, fire, explosions, fog | Mantaflow Eulerian |
| **Particles (Emitter)** | Sparks, rain, snow, debris bursts | Per-particle physics |
| **Particles (Hair)** | Hair, fur, grass | Strand-based |
| **Force Fields** | Wind, vortex, magnetic — affects all of above | Field math |

A pro pipeline often combines several: **rigid body** for falling debris + **smoke** for dust + **particles** for sparks.

---

## Rigid Body simulation (the workhorse)

**What it does**: Objects fall, collide, bounce, stack realistically.

```python
import bpy

# Make object a rigid body
obj = bpy.data.objects['GEO-cube']
bpy.context.view_layer.objects.active = obj

bpy.ops.rigidbody.object_add()
rb = obj.rigid_body

# Settings
rb.type = 'ACTIVE'        # 'ACTIVE' (falls/moves) or 'PASSIVE' (collision only, doesn't move)
rb.mass = 1.0             # kg
rb.friction = 0.5
rb.restitution = 0.0      # bounciness (0 = no bounce, 1 = full bounce)
rb.collision_shape = 'CONVEX_HULL'   # 'BOX', 'SPHERE', 'CAPSULE', 'CYLINDER', 'CONE',
                                      # 'CONVEX_HULL', 'MESH', 'COMPOUND'
rb.collision_margin = 0.04  # small gap to prevent sticking
```

### Collision shapes (most-to-least performant)
1. `'BOX'`, `'SPHERE'`, `'CAPSULE'` — primitives (fastest)
2. `'CONVEX_HULL'` — wraps mesh in convex shape (good default, fast)
3. `'MESH'` — exact mesh shape (slow, only for static collision)
4. `'COMPOUND'` — multiple primitives combined (best for vehicles, complex shapes)

**Pro rule**: never use `MESH` for active rigid bodies. Use `CONVEX_HULL` for moving objects, `MESH` only for static ground/walls.

### Bake the simulation
```python
# Set frame range
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 250

# Bake all rigid bodies
bpy.ops.ptcache.bake_all(bake=True)
```

Without baking, Cycles renders each frame by re-simulating — slow and inconsistent. Baking caches results.

---

## Cloth simulation

```python
import bpy

obj = bpy.data.objects['GEO-flag']
bpy.context.view_layer.objects.active = obj

# Add Cloth modifier
cloth = obj.modifiers.new('Cloth', type='CLOTH')
settings = cloth.settings

# Material presets
settings.use_default = False
# Or use built-in presets via UI: Cotton, Denim, Leather, Rubber, Silk

# Manual tuning
settings.mass = 0.3                  # weight per area (kg/m²)
settings.tension_stiffness = 15      # stretch resistance
settings.compression_stiffness = 15  # compression resistance
settings.shear_stiffness = 5         # shear (diagonal) resistance
settings.bending_stiffness = 0.5     # how floppy/stiff bend

# Collision (interactions with other objects)
collision_settings = cloth.collision_settings
collision_settings.collision_quality = 5
collision_settings.distance_min = 0.001    # min distance to collider
collision_settings.use_self_collision = True
collision_settings.self_distance_min = 0.005
```

**Pin vertices** (to keep them fixed — like cloth hung on a hook):
1. Edit Mode → select pin vertices.
2. Vertex Group "Pin" → assign with weight 1.0.
3. In Cloth settings → Vertex Groups → Pinning: select "Pin" group.

### Cloth physics presets (the ones to know)
| Preset | Best for |
|--------|----------|
| Cotton | Shirt, light dress |
| Silk | Smooth flowing scarves, dresses |
| Denim | Jeans, jackets (heavier) |
| Leather | Jackets, belts (very stiff) |
| Rubber | Latex, balloons |

---

## Fluid simulation (Mantaflow)

Mantaflow is Blender's unified fluid solver — handles liquids, smoke, fire.

### Liquid setup recipe
```python
import bpy

# 1. Domain: a box that contains the simulation
bpy.ops.mesh.primitive_cube_add(size=4, location=(0, 0, 0))
domain = bpy.context.object
domain.name = 'GEO-fluid-domain'
bpy.ops.object.modifier_add(type='FLUID')
domain.modifiers['Fluid'].fluid_type = 'DOMAIN'
domain.modifiers['Fluid'].domain_settings.domain_type = 'LIQUID'
domain.modifiers['Fluid'].domain_settings.resolution_max = 64   # higher = more detail, slower

# 2. Inflow: where liquid comes in
bpy.ops.mesh.primitive_cube_add(size=0.5, location=(0, 0, 1.5))
inflow = bpy.context.object
inflow.name = 'GEO-fluid-inflow'
bpy.ops.object.modifier_add(type='FLUID')
inflow.modifiers['Fluid'].fluid_type = 'FLOW'
inflow.modifiers['Fluid'].flow_settings.flow_type = 'LIQUID'
inflow.modifiers['Fluid'].flow_settings.flow_behavior = 'INFLOW'

# 3. Effector: an obstacle (e.g., a cup)
# Add cup mesh, then:
# bpy.ops.object.modifier_add(type='FLUID')
# obj.modifiers['Fluid'].fluid_type = 'EFFECTOR'

# 4. Bake the simulation
domain.select_set(True)
bpy.context.view_layer.objects.active = domain
bpy.ops.fluid.bake_all()
```

**Resolution guide**:
- `resolution_max = 64` — preview, fast
- `resolution_max = 128` — typical production
- `resolution_max = 256` — high detail (warning: long bake, big disk usage)
- `resolution_max = 512` — hero shots only (potentially hours to bake)

### Smoke / fire setup
Same as liquid, but `domain_type = 'GAS'` and `flow_type = 'SMOKE'` or `'FIRE'` or `'BOTH'`.

```python
inflow.modifiers['Fluid'].flow_settings.flow_type = 'FIRE'
inflow.modifiers['Fluid'].flow_settings.density = 1.0
inflow.modifiers['Fluid'].flow_settings.fuel_amount = 1.0
```

### Volumetric rendering
After baking, the domain shows simulation as a volume. Add Volume Scatter / Absorption shader to render.

```python
# Simple smoke material
mat = bpy.data.materials.new('MAT-smoke')
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links

# Remove default Principled BSDF
for n in list(nodes):
    if n.type != 'OUTPUT_MATERIAL':
        nodes.remove(n)

# Add Volume Scatter
scatter = nodes.new('ShaderNodeVolumeScatter')
output = nodes['Material Output']
links.new(scatter.outputs[0], output.inputs['Volume'])

# Or for fire: use Principled Volume node — it auto-handles temperature → emission
```

---

## Particle systems

### Emitter particles (sparks, rain, debris)
```python
import bpy

obj = bpy.data.objects['GEO-emitter']
bpy.context.view_layer.objects.active = obj

# Add particle system
psys = obj.modifiers.new('Particles', type='PARTICLE_SYSTEM')
ps = obj.particle_systems[0].settings

ps.type = 'EMITTER'
ps.count = 1000
ps.frame_start = 1
ps.frame_end = 100
ps.lifetime = 50

# Initial velocity
ps.normal_factor = 5.0    # along surface normals
ps.factor_random = 2.0    # random direction component

# Physics
ps.physics_type = 'NEWTON'
ps.mass = 0.01
ps.effector_weights.gravity = 1.0    # full gravity
ps.use_size_deflect = True
ps.use_die_on_collision = True

# Render as instanced object instead of dot
ps.render_type = 'OBJECT'
ps.instance_object = bpy.data.objects['GEO-spark']
ps.particle_size = 0.05
```

### Hair particles
```python
psys = obj.modifiers.new('Hair', type='PARTICLE_SYSTEM')
ps = obj.particle_systems[0].settings

ps.type = 'HAIR'
ps.count = 5000
ps.hair_step = 5         # segments per hair
ps.hair_length = 0.1

# Children (extra hairs around each parent)
ps.child_type = 'INTERPOLATED'
ps.child_nbr = 50
ps.rendered_child_count = 100

# Render strands
ps.render_type = 'PATH'
ps.material_slot = 'MAT-hair'
```

**Pro tip**: For game-ready hair (cards), don't use particles — model hair planes manually with alpha textures.

---

## Force fields (the universal modifier)

Affect all physics types. Add via `Add → Force Field`:

| Type | Effect | Use |
|------|--------|-----|
| **Force** | Push/pull | Basic gravity replacement, attraction/repulsion |
| **Wind** | Constant directional force | Cloth flapping, particle drift |
| **Vortex** | Spinning force | Tornadoes, drains, swirls |
| **Magnetic** | Charge-based | Attract/repel based on object charge |
| **Harmonic** | Spring-like return | Bouncy attraction |
| **Charge** | Coulomb force | Plasma, electrical |
| **Lennard-Jones** | Atomic-like | Molecular dynamics |
| **Texture** | Force from texture | Custom turbulence patterns |
| **Curve Guide** | Particles follow curve | Channeled flow |
| **Boid** | Flocking behavior | Bird flocks, fish schools |
| **Turbulence** | Noise-based | Realistic randomness |
| **Drag** | Friction with air | Slow particles down |
| **Smoke Flow** | Move along smoke sim velocity | Layered effects |

```python
import bpy

bpy.ops.object.effector_add(type='WIND')
wind = bpy.context.object
wind.field.strength = 5.0
wind.field.flow = 1.0
wind.field.noise = 0.5
wind.field.seed = 0
```

---

## Performance tips

| Tip | Why |
|-----|-----|
| Bake everything before rendering | Real-time recompute + render = nightmare |
| Lower resolution during preview, raise for final | Smoke/fluid resolution doubles = ~8× compute |
| Use Convex Hull collision for active rigid bodies | Mesh collision is 10-100× slower |
| Disable self-collision in cloth if not needed | Big speedup |
| Limit particle count — 10K is a lot | Render time ≈ count |
| Cache to disk, not memory | Long sims survive Blender crashes |

```python
# Disk cache for fluid
domain.modifiers['Fluid'].domain_settings.cache_directory = '/tmp/fluid_cache/'
domain.modifiers['Fluid'].domain_settings.cache_type = 'ALL'
```

---

## Common pitfalls

| Mistake | Why | Fix |
|---------|-----|-----|
| Rigid body falls through floor | Floor not Passive rigid body | Add rigid body to floor, type 'PASSIVE' |
| Cloth explodes / flies away | Stiffness too high, mass too low | Use preset; reduce stiffness 10-50× |
| Fluid empty / nothing visible | Forgot to bake | `bpy.ops.fluid.bake_all()` |
| Smoke renders white block | Volume Scatter not added to domain material | Add Principled Volume or Volume Scatter |
| Particles render as black dots | No `instance_object` set; no material | Set render type + material slot |
| Resolution_max 512 → out of memory | Too dense | Drop to 128–256, use upres for fakes |
| Sim looks the same every time | Same `seed` | `ps.seed = random.randint(0, 1000)` |

---

## Sources

- [Fluid — Blender 5.1 Manual](https://docs.blender.org/manual/en/latest/physics/fluid/index.html)
- [CG Cookie — CORE: Fundamentals of Physics in Blender](https://cgcookie.com/courses/core-fundamentals-of-physics-in-blender)
- [Stephen Pearson — Learn Blender Simulations the Right Way (book)](https://www.oreilly.com/library/view/learn-blender-simulations/9781803234151/)
- [Cookwithrome — Adding Physics to Blender](https://cookwithrome.com/blender/is-it-possibble-to-add-physics-to-blender/)
- [Udemy — Ultimate Blender 3D Simulations, Physics & Particles](https://www.udemy.com/course/blender-simulations-physics-particles/)
- [WaitUK Forum — 5 Steps to Render Physics in Blender](https://forum.waituk.com/how-to-render-physics-in-blender/)

---

## Outstanding

- [ ] Soft body specifics (vs cloth — when to use each)
- [ ] Boids flocking system
- [ ] Mantaflow whitewater (foam, spray, bubbles)
- [ ] Dynamic Paint (paint on objects via collision)
- [ ] Cell Fracture addon (for shattering)
