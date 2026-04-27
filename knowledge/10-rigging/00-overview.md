# Rigging — Pro Knowledge Overview

**Domain**: 10 — Armatures, IK/FK, bone constraints, weight painting, Rigify  
**Status**: Initial pass complete  
**Last update**: 2026-04-27

---

## What rigging is

Building the *control system* that animators use to pose and animate a character. The rig is the puppet's strings.

**Three layers of a rig**:
1. **Deformation bones** — actually attached to mesh vertices (via vertex groups)
2. **Control bones** — what the animator grabs (IK targets, custom shape controllers)
3. **Mechanism bones** — internal logic (drivers, helpers, twist bones)

A pro rig hides the deformation layer, exposes only clean control bones to animators.

---

## Decision tree: build custom rig vs use Rigify

```
Is it a humanoid biped (or close to it)?
├── YES → Use Rigify
│         + Pre-built meta-rigs for biped, quadruped, bird, fish, cat
│         + Saves days of work
│         + Industry-standard IK/FK switching, stretchy limbs, face controls
│         - Can be hard to debug if you need to customize internals
│
└── NO  → Custom rig with armatures
          (mechanical objects, props, non-standard creatures)
```

**Rigify** is bundled in Blender. Enable in Preferences → Add-ons → "Rigify".

---

## Rigify workflow (fastest path to rigged biped)

```python
import bpy

# 1. Add a meta-rig (Add → Armature → Human (Meta-Rig))
bpy.ops.object.armature_human_metarig_add()
metarig = bpy.context.object
metarig.name = 'ARM-character_metarig'

# 2. In Edit Mode, snap meta-rig bones to the character mesh proportions
# (Move bones to align with shoulders, hips, knees, etc.)
# This is the part that takes time — manual alignment.

# 3. In Object Mode, generate the rig
bpy.ops.pose.rigify_generate()
# Creates 'rig' object with full control system

# 4. Parent the mesh to the generated rig
mesh = bpy.data.objects['GEO-character']
rig = bpy.data.objects['rig']
mesh.parent = rig
mod = mesh.modifiers.new('Armature', type='ARMATURE')
mod.object = rig

# 5. Auto-weight (or manual weight paint)
bpy.context.view_layer.objects.active = rig
mesh.select_set(True)
rig.select_set(True)
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
```

After step 3, the **generated rig** has:
- IK/FK arms and legs (with switches in N-panel)
- Stretchy limbs
- Face controls (if Faces meta-rig used)
- Spine with bend / twist controls
- Custom bone shapes for clarity

---

## Custom armature (for non-humanoid rigs)

```python
import bpy

# Add empty armature
arm_data = bpy.data.armatures.new('ARM-prop')
arm_obj = bpy.data.objects.new('ARM-prop', arm_data)
bpy.context.collection.objects.link(arm_obj)

bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.mode_set(mode='EDIT')

# Add bones
edit_bones = arm_data.edit_bones
b1 = edit_bones.new('Root')
b1.head = (0, 0, 0)
b1.tail = (0, 0, 0.5)

b2 = edit_bones.new('Arm')
b2.head = (0, 0, 0.5)
b2.tail = (1, 0, 0.5)
b2.parent = b1

bpy.ops.object.mode_set(mode='OBJECT')
```

---

## IK vs FK (the central concept)

### Forward Kinematics (FK)
Rotate parent bone → children follow. Like rotating your shoulder → arm and hand swing.

**When to use**:
- Animating arcs of motion (waving)
- Hair, tail, secondary motion
- Pose-to-pose animation

### Inverse Kinematics (IK)
Position end-effector → solver computes parent rotations. Like grabbing the hand and the arm bones figure out their rotations.

**When to use**:
- Hand stays planted on a surface (table, weapon)
- Foot lock (walking, contact poses)
- Reaching for a target

### Setting up IK
```python
import bpy

rig = bpy.data.objects['ARM-character']
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='POSE')

# Add IK constraint to the last bone in the chain (e.g., 'Hand.IK')
hand = rig.pose.bones['Hand']
ik = hand.constraints.new('IK')
ik.target = rig
ik.subtarget = 'Hand_IK_Target'   # an empty bone that the animator moves
ik.chain_count = 2                 # how many bones up the chain to solve
ik.pole_target = rig
ik.pole_subtarget = 'Elbow_Pole'   # determines elbow direction

bpy.ops.object.mode_set(mode='OBJECT')
```

**Pole target**: an extra bone/empty positioned where the elbow should "aim". Without it, IK solver may flip elbows unpredictably.

### IK/FK switching
Animators want to use *both* per-shot. Rigify provides this out-of-the-box; for custom rigs, you set up:
1. Two bone chains: FK chain and IK chain.
2. A "mech" chain that copies from one or the other based on a property.
3. The visible deform bones follow the mech chain.

---

## Bone constraints (the toolkit)

| Constraint | Purpose |
|-----------|---------|
| **IK** | Inverse kinematics solver |
| **Copy Location/Rotation/Scale** | Bone follows another |
| **Track To** | Bone aims at target (eyes following) |
| **Damped Track** | Smoother track-to (less twitchy) |
| **Stretch To** | Stretches between two bones (rubber arms, soft IK) |
| **Limit Rotation/Location/Scale** | Constrain bone movement (prevents over-rotation) |
| **Floor** | Bone can't pass through plane (foot on ground) |
| **Child Of** | Animatable parenting (hand grabs sword, then releases) |
| **Action** | Drive an action by bone transform (corrective shape keys) |

---

## Weight painting (the laborious part)

Tells Blender which bones move which mesh vertices, with what strength.

**Auto-weights** (`Ctrl+P → Armature Deform → With Automatic Weights`) get you 80% there. The remaining 20% — joints, faces, fingers — needs manual cleanup.

```python
import bpy

mesh = bpy.data.objects['GEO-character']
rig = bpy.data.objects['ARM-character']

# Parent with automatic weights (creates vertex groups + Armature modifier)
mesh.select_set(True)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')

# Switch mesh to Weight Paint mode
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
```

### Weight painting pitfalls (and fixes)

| Issue | Fix |
|-------|-----|
| Mesh deforms unnaturally at joint | Add edge loops at joint; smooth weights |
| Stretched or pinched vertices | Use `Weights → Smooth` or paint strength manually |
| One bone influences too much | Set max influence per vertex to 4 (`Limit Total`) |
| Weights bleed across mesh islands | Set `Falloff Type` to 'Project' for hard surfaces |

### Standard rules
- **Total weights per vertex = 1.0** (Blender normalizes by default)
- **Maximum 4 bone influences per vertex** (game engine limitation; Blender supports more but breaks export)
- **Use mirror modifier** during paint for symmetric characters: weights mirror automatically

---

## Custom bone shapes (clean rig UI)

Replace blocky default bones with elegant shapes (circles, arrows, hooks):

```python
import bpy

# 1. Create shape mesh
bpy.ops.mesh.primitive_circle_add(vertices=32, radius=0.3)
shape = bpy.context.object
shape.name = 'WGT-circle'

# Hide the shape mesh (it's just for display)
shape.hide_render = True
shape.hide_viewport = True

# 2. Assign to bone
rig = bpy.data.objects['ARM-character']
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='POSE')

bone = rig.pose.bones['Hand_IK_Target']
bone.custom_shape = bpy.data.objects['WGT-circle']
bone.custom_shape_scale_xyz = (1.5, 1.5, 1.5)

bpy.ops.object.mode_set(mode='OBJECT')
```

**Pro tip**: keep all shape meshes in a hidden collection ('Widgets' or 'WGT'). Naming convention: `WGT-{shape_name}`.

---

## Drivers (Python expressions on properties)

Drive one property based on another. Example: when shoulder rotates >45°, fix neck distortion via a corrective shape key.

```python
import bpy

mesh = bpy.data.objects['GEO-character']
rig = bpy.data.objects['ARM-character']

# Add a driver to a shape key value
sk = mesh.data.shape_keys.key_blocks['neck_correction']
fcurve = sk.driver_add('value')
driver = fcurve.driver

# Variable: shoulder rotation
var = driver.variables.new()
var.name = 'shoulder_x'
var.targets[0].id_type = 'OBJECT'
var.targets[0].id = rig
var.targets[0].data_path = 'pose.bones["Shoulder.L"].rotation_euler[0]'

# Expression
driver.expression = 'max(0, shoulder_x - 0.785)'  # > 45° = engage shape key
```

---

## Common pitfalls

| Mistake | Why | Fix |
|---------|-----|-----|
| Auto-weights only | Joints crease incorrectly | Manual weight paint at joints + smoothed |
| No edge loops at joints | Bend point pinches | Add 2-3 edge loops on either side of joint |
| Forgot Armature modifier | Mesh doesn't move with bones | Add `Armature` modifier, set `Object` to rig |
| Bone roll wrong | Limbs twist when posed | Edit Mode → select bone → `Ctrl+N → Recalculate Roll` |
| Skinning weights > 4 per vertex | Game engine breaks export | `Limit Total → 4` |
| Symmetry off when painting | Asymmetric weights | Enable `X-Mirror` in tool settings |
| IK solver flips elbow | No pole target | Add pole bone/empty |

---

## Export to game engines

Most engines (Unreal, Unity, Godot, Three.js) expect:
- **One armature** per character
- **No drivers** (bake them to keyframes first)
- **Max 4 bone influences per vertex**
- **Bone count limits**: Unreal ≤ 65,535 (no real limit); Unity ≤ ~256 efficient
- **Naming**: avoid spaces, use only ASCII

```python
# Bake drivers to keyframes before export
bpy.ops.nla.bake(
    frame_start=1,
    frame_end=240,
    only_selected=True,
    visual_keying=True,
    clear_constraints=False,
    clear_parents=False,
    use_current_action=True,
    bake_types={'POSE'},
)
```

---

## Sources

- [Rigify — Blender 2.81 Manual (still applicable to 5.x)](https://docs.blender.org/manual/en/2.81/addons/rigging/rigify.html)
- [CGDive — Rig Anything with Rigify](https://cgdive.com/easy-rigging-in-blender-with-rigify-armature-basics/)
- [Whizzy Studios — Custom Rigs without Add-ons](https://www.whizzystudios.com/post/how-to-create-custom-rigs-in-blender-without-any-add-ons-no-rigify-needed)
- [0curtain0 — Blender Rigging and Weight Painting Guide](https://0curtain0.github.io/blender_rigging.html)
- [Auto-Rig Pro (Superhive paid addon)](https://superhivemarket.com/products/auto-rig-pro)
- [Alasali 3D — Blender Rigging Guide](https://alasali3d.com/blender-rigging-guide/)
- [CGDive — Rigify Workflow Chapter 2](https://cgdive.com/rig-anything-with-rigify-chapter-2-the-rigify-workflow/)

---

## Outstanding

- [ ] Face rigs (corrective shape keys, blink driver, jaw setup)
- [ ] Cloth-aware rig (bones for skirt, cape, hair)
- [ ] Quadruped Rigify customization
- [ ] Mocap retargeting from BVH/FBX onto Rigify
