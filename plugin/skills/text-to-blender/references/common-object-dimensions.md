# Common-Object Reference Dimensions

When the user says "build a sword" or "render a chair", the orchestrator needs to know the real-world proportions of the subject. Guessing produces broken results — a 50×50cm "blade" looks nothing like a sword.

This file is the lookup table. **Always check before sizing**.

---

## Eyewear / sunglasses

### Aviator sunglasses (Ray-Ban classic)
- **Lens**: 58mm wide × 50mm tall, **teardrop shape** (rounder at top, lower at bottom — "droop")
  - Build: 8-10 point Bezier curve outline, top arc rounder than bottom; bottom point pulled down ~10% extra
  - For mirror lenses: filled disc inside the rim with `Metallic=1.0, Roughness=0.05, Base Color=tinted F0`
- **Bridge gap**: 14mm between lens inner edges
- **Double-bar bridge** (the classic Aviator detail): 
  - Top bar: thin straight wire spanning across both lens tops, slightly above the rim
  - Bottom/middle bar: shorter, with a slight saddle dip, between lens inner-tops
- **Frame wire**: ~0.6-1.0mm diameter (very thin) — use bevel_depth=0.0006 on Bezier curves
- **Nose pads**: 3mm sphere scaled to vertical pill (1.0, 1.5, 2.5); silicone material; one each side of bridge
- **Temple arms**: 135mm long; start at outer-mid of lens; extend straight back along Y with slight downward droop at the ear-bend (last 5cm)
- **Materials**:
  - Frame: gunmetal (Metallic=1.0, Base Color=(0.18,0.18,0.20), Roughness=0.30) or polished gold/silver
  - Mirror lens: solid metal with tinted base color (blue: (0.05, 0.10, 0.22); green: (0.08, 0.20, 0.10); brown: (0.20, 0.10, 0.05))
  - Tinted (non-mirror): Metallic=0, Transmission=1, IOR=1.5, with surface tint or Volume Absorption

**Critical for hero shots**: thin metal temple arms catch side lighting as specular streaks in narrow studio setups. Use SOFTBOX from above or front instead of strong side rim light, OR crop the temple arms out of the frame.

## Bladed weapons

### One-handed arming sword (medieval)
- **Total length**: 95–100 cm
- **Blade**: 78 cm long × 4.5 cm broad face × 0.8 cm thick (cutting-edge axis)
  - Aspect ratio length : broad : thin ≈ 100 : 5.7 : 1
  - **Tip**: pinch the top vertices to a single point (don't just scale them — that gives a chiseled flat tip)
  - **Optional fuller**: a 1mm-deep groove running along the broad face, ~50% of blade length, centered
- **Cross-guard**: 20 cm wide × 2.5 cm tall × 1.5 cm thick
  - Long axis (20cm) is **horizontal**, perpendicular to the blade
- **Grip**: 13 cm long × 2.8 cm diameter (cylinder)
- **Pommel**: 5.6 cm sphere

### Dagger
- Total: 30–40 cm
- Blade: 22cm × 2.5cm × 0.5cm

### Greatsword
- Total: 150–180 cm
- Blade: 110cm × 5cm × 0.9cm
- Two-handed grip: 30cm

### Katana
- Total: 100–110 cm
- Blade: 70 cm × 3 cm × 0.7 cm; **curved** (not straight)
- Tsuka (handle): 25–30 cm wrapped in tsukamaki

---

## Furniture

### Dining chair (Mission / Shaker style — recommended baseline)

A "chair" rendered as 6 plain rectangles (seat + 4 legs + back panel) reads as "simple plastic wrap on rectangles" — see v0.8.0 validation. To produce a credible chair, include these standard details:

**Core parts:**
- Seat: 45cm × 45cm × 4cm thick; seat top at 45cm above floor
- Legs: 4cm × 4cm × 45cm; legs inset ~2.5cm from seat edges; **taper bottom 70%** (chair legs narrow toward the floor)

**Required structural details (don't skip these):**
- **Stretchers** — 4 horizontal bars connecting the legs at ~10cm above floor. Front and back stretchers along X axis; left and right along Y axis. Cross-axis stretchers should sit ~4cm higher than parallel-axis ones to avoid intersecting. Each: 1.8cm × 2.5cm cross-section.
- **Slatted back** — instead of a solid panel, use 4-6 vertical slats (each 2.5cm × 2cm × 41cm) with even spacing across a 40cm-wide region centred on the seat back edge.
- **Top rail** — horizontal bar across the top of the slats: 40cm wide × 2.5cm × 4cm tall, slightly overlapping the slat tops.

**Shape refinements:**
- Seat: bevel modifier with width 0.005m, segments 3 (rounded edges, no sharp corners)
- Slight curve at top of back rail (pull top corners inward 8% in X for a soft rounded silhouette)

This produces a recognisable Mission-style chair. For other chair styles (modern minimalist, Windsor, office), document explicitly and build differently.

### Office chair (basic, no wheels)
- Seat: 50cm × 50cm
- Total height: 90cm

### Coffee table
- Top: 120cm × 60cm × 4cm
- Height: 45cm
- Legs: 5cm × 5cm × 41cm
- Optional: lower shelf at 15cm above floor (add 4cm-thick board between legs)
- Edge bevel: ~5mm

### Dining table (4-person)
- Top: 150cm × 90cm × 3.5cm thick
- Height: 75cm
- Legs: 7cm × 7cm × 71.5cm; inset 8-12cm from corners
- Optional: aprons (horizontal supports under top, between legs) — 2cm thick × 8cm tall, mortised flush with leg tops
- Edge bevel: ~4mm

### Desk lamp (classic articulated arm style)
- Base: ø14cm × 3cm tall cylinder (heavy weighted base)
- Lower arm: 30cm × 2cm × 2cm rectangular bar, pivots on base
- Upper arm: 25cm × 2cm × 2cm rectangular bar, pivots at elbow
- Lampshade: cone, ø10cm at opening, ø6cm at top, 12cm tall
- Materials: matte metal arm + base; lampshade interior glossy white (reflects bulb)
- Joints have visible pivot screws (small cylinders perpendicular to arms)

### Floor lamp
- Base: ø35cm × 2cm tall
- Pole: 150cm tall × 3cm dia cylinder
- Lampshade: ø45cm × 35cm tall truncated cone (drum shade), centered at pole top
- Pole-to-shade fitting: small ring or harp at top

---

## Containers

### Wine bottle
- Total height: 28-32 cm
- Body diameter: 7.5 cm
- Neck diameter: 2.5 cm
- Neck length: 8 cm
- Body length: 22 cm

### Beer bottle
- Total: 23-25 cm
- Body ø: 6 cm

### Coffee mug
- Body: cylinder, ø8 cm × 9 cm tall (outer); wall thickness 5 mm; inner ø7 cm × 8.5 cm depth
- **Bottom**: solid (don't model interior all the way to base)
- Handle: D-shaped loop, 8 cm tall × 2 cm wide × 1 cm thick; attached at body side, 1 cm from top and 1 cm from bottom
- Use Boolean Difference of inner cylinder from outer to create the cup interior, OR Solidify modifier on a hollowed shell
- Base bevel: ~3mm rounded
- Material: typically ceramic — Principled BSDF with Roughness 0.4, Metallic 0, IOR 1.5; subtle subsurface for white ceramic glow

---

## Vehicles (rough silhouettes)

### Compact car
- Length: 4.2 m
- Width: 1.7 m
- Height: 1.5 m

### Bicycle
- Length: 1.7 m
- Wheel diameter: 70 cm
- Saddle height: 90 cm

---

## Architecture (rough)

### Door
- Standard interior: 80cm wide × 200cm tall × 4cm thick

### Window
- Standard residential: 120cm × 150cm

### Wall thickness
- Interior: 12cm; exterior: 25cm

---

## Human-scale reference (anchor when in doubt)

- Average adult height: 170 cm
- Eye level: 160 cm
- Shoulder width: 45 cm
- Hip width: 35 cm
- Hand: 18 cm long × 8 cm wide
- Head: 22 cm tall × 18 cm wide

When you don't have a specific reference for a subject, anchor it against human scale: a sword that fits in one hand has a ~13cm grip; a chair you sit in has a 45cm seat height; a doorway you walk through is 80cm wide.

---

## How to use these in code

The `text-to-blender` orchestrator should read this file (at most once per session) before generating any modeling code. Pattern:

```python
# Sword example with explicit reference values
BLADE_LEN = 0.78
BLADE_BROAD = 0.045   # the wide flat face axis (visible from the side)
BLADE_THIN = 0.008    # the cutting-edge axis (thin)
GUARD_WIDTH = 0.20
GRIP_LEN = 0.13
POMMEL_RADIUS = 0.028

# Build with these — never guess
```

---

## Adding to this list

When the user asks for a subject not listed here, look up the real-world dimensions from a credible source (dimensions.com, Wikipedia, manufacturer specs) BEFORE generating Blender code. Add the new entry here for future sessions if the subject is general (avoid hyper-specific items).
