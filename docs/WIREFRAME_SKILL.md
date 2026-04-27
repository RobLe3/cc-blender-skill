# Wireframe-to-3D Conversion Skill

**Name**: `wireframe-to-3d`

**Purpose**: Convert orthographic 2D wireframe images (technical drawings) to parametric 3D models in Blender, optimized for glTF/GLB export.

**Use Cases**:
- CAD-style eyeglasses from front/side orthographic views
- Technical wireframes of mechanical parts
- Industrial design sketches with dimensional profiles
- Character feature accessories (goggles, helmets, etc.)

**Status**: Ready for integration

---

## Quick Start

### For Users

```
You: "Convert my wireframe glasses drawing to a 3D Blender model"

Skill response:
  1. Analyze the wireframe image(s) you provide
  2. Extract contours and fit Bezier curves
  3. Create parametric curves in Blender
  4. Convert to mesh with proper topology
  5. Apply materials and export GLB
  → Returns: model.glb + log of optimization steps
```

### For Developers

The skill orchestrates three stages:

**Stage 1: Image Analysis** (`wireframe_analyzer.py`)
- Input: PNG wireframe image
- Output: JSON with Bezier control points
- Runtime: < 1s for typical 800×600 wireframe

**Stage 2: Blender Curve Creation** (Blender MCP via Python)
- Input: Analyzer JSON output
- Output: Blender `.blend` scene with curves
- Runtime: < 2s

**Stage 3: Mesh Conversion & Export** (Blender MCP)
- Input: Curve scene
- Output: Optimized GLB file
- Runtime: < 5s

---

## Decision Flow

### Q1: What's Your Input?

**Single orthographic view** (e.g., front glasses wireframe only)
→ **Linear profiles only** (can't infer depth)
→ Skill suggests: "Please provide side view for depth inference, or specify extrusion depth manually"

**Two orthographic views** (e.g., front + side)
→ **Full 3D reconstruction possible**
→ Skill proceeds: Combine front (silhouette) + side (depth) to create 3D model

**Three views** (front + side + back)
→ **Maximum geometric detail**
→ Skill uses: Back view for validation and detail refinement

### Q2: What Level of Detail Do You Need?

**Quick preview** (low polygon, simple materials)
- Analyzer: RDP epsilon = 4–5 px (aggressive simplification)
- Result: ~1000–2000 triangles
- Export: 500 KB–1 MB GLB
- Time: ~3–5 seconds

**Production quality** (moderate polygon, polished)
- Analyzer: RDP epsilon = 2–3 px (balanced)
- Result: ~5000–8000 triangles
- Export: 2–4 MB GLB
- Time: ~10–15 seconds

**High fidelity** (high polygon, detailed)
- Analyzer: RDP epsilon = 1–2 px (fine detail)
- Result: 10000–20000 triangles
- Export: 5–15 MB GLB (may need optimization)
- Time: ~15–30 seconds

**Your selection determines all downstream parameters.**

### Q3: What Type of Geometry?

**Thin wires / frames** (bridges, arms, hinges)
→ Use **bevel extrusion** (curve.bevel_depth = 1–2 mm)
→ Output: Single-surface tubular mesh

**Curved surfaces** (lenses, domes, helmets)
→ Use **profile lofting** (2 profiles + interpolation)
→ Output: Multi-surface, smooth topology

**Composite** (e.g., glass frames + lenses)
→ Use **hybrid approach** (wires + surfaces)
→ Output: Multiple mesh parts, single GLB

**Your choice influences tessellation strategy and polygon budget.**

### Q4: Do You Have Existing 3D Constraints?

**No** → Skill auto-infers dimensions from wireframe aspect ratio

**Yes, real-world measurements** (e.g., "glasses are 140mm wide")
→ Supply measurements in request
→ Skill scales model to real-world units (1 Blender unit = 1 mm)

**Yes, custom target** (e.g., "fit within 50KB GLB")
→ Skill applies aggressive decimation post-export
→ May sacrifice quality; warns if visible

---

## Skill Parameters

### Required

- **image_path**: Path to wireframe PNG (or upload inline)
- **view_type**: `'front'` | `'side'` | `'multi'` (if providing multiple views)

### Optional (with Sensible Defaults)

| Parameter | Default | Range | Effect |
|-----------|---------|-------|--------|
| `detail_level` | `'production'` | `'preview'`, `'production'`, `'high'` | RDP epsilon & tessellation resolution |
| `geometry_type` | `'hybrid'` | `'wires'`, `'surfaces'`, `'hybrid'` | Extrusion vs. lofting strategy |
| `world_width_mm` | Auto-infer | 50–500 | Object physical width (for scaling) |
| `output_format` | `'glb'` | `'glb'`, `'blend'`, `'json'` | Export format |
| `material_preset` | `'matte_plastic'` | `'matte_plastic'`, `'brushed_metal'`, `'mirror_glass'` | PBR material presets |
| `target_file_size_mb` | 15 | 0.5–15 | Hard cap; triggers decimation if exceeded |
| `verbose` | `False` | bool | Log all pipeline steps |

### Example Request

```json
{
  "image_path": "aviator_front.png",
  "image_path_side": "aviator_side.png",
  "view_type": "multi",
  "detail_level": "production",
  "geometry_type": "hybrid",
  "world_width_mm": 140.0,
  "material_preset": "brushed_metal",
  "target_file_size_mb": 8.0,
  "verbose": true
}
```

---

## Step-by-Step Execution

### 1. **Validate Input**

```
✓ Image file exists and is PNG?
✓ Image dimensions reasonable (> 400×400 px)?
✓ Image contrast sufficient (histogram bimodal)?
✓ view_type is recognized?
✓ If multi-view: all images provided?
✓ Parameters within valid ranges?
```

**If validation fails**: Return specific error, suggest remedies.

### 2. **Analyze Wireframes**

For each view (front, side, optional back):
```
a. Call wireframe_analyzer.py with image + parameters
   - Input: PNG image, RDP epsilon (from detail_level)
   - Process: grayscale → binarize → edge detect → contour extract → simplify → Bezier fit
   - Output: JSON with contours + Bezier curves
   
b. Validate analyzer output
   - Each contour has 3+ simplified points?
   - Bezier curves fit error < 3px?
   - Number of contours matches expectation?
```

**If analysis fails**: Return analyzer logs, suggest parameter tuning (e.g., "try increasing Canny threshold").

### 3. **Infer 3D Geometry**

**For front + side views**:
- Read silhouette from front
- Read depth profile from side
- Infer object bounds: width (from front), height (from front), depth (from side)
- Scale pixel→world using `world_width_mm` parameter

**For single view**:
- Infer depth = 0 (flat extrusion); warn user

**For front + side + back**:
- Use back for validation; flag asymmetries > tolerance

### 4. **Create Blender Scene**

```
a. Create curve objects (one per contour)
   - Populate from analyzer's Bezier control points
   - Set handle types to ALIGNED (C¹ continuity)
   - Set bevel_depth based on geometry_type
   
b. If multi-view: Merge curves into coherent parts
   - Example: Front lens silhouette + side depth → lofted 3D lens surface
   - Use curve extrude/revolve operations
   
c. Apply materials
   - Create PBR materials from preset (material_preset parameter)
   - Assign to parts
```

**Output**: `.blend` scene with curves and materials (no meshes yet).

### 5. **Convert Curves to Meshes**

```
For each curve object:
  a. Convert to mesh
  b. Cleanup: remove doubles, fix normals, smooth shading
  c. Validate: no isolated vertices, no degenerate faces
  d. Estimate final triangle count
  
If estimated_triangles > polygon_budget:
  → Warn: "High polygon count, may exceed file size"
  → Plan decimation for post-export
```

### 6. **Validate Topology**

**Static geometry checks**:
- No interpenetration (lenses through bridge)?
- Symmetry (for paired parts)? Tolerance ± 1 mm
- Aspect ratios match reference? Tolerance ± 5%
- Edge loops well-formed (for future animation)?

**Return warnings** if checks fail, but don't block export.

### 7. **Optimize and Export**

```
a. Flatten UV map (even if no textures; required for glTF)
b. Export to GLB with embedded materials
c. Check file size
   If size > target_file_size_mb:
     → Apply Decimate modifier (ratio = 0.8–0.9)
     → Re-export
     → Iterate until size ≤ target
d. Verify GLB is valid (can load in three.js)
```

**Output**: `model.glb` (≤ target size, all materials embedded).

### 8. **Return Results**

```json
{
  "status": "success",
  "output_file": "model.glb",
  "file_size_mb": 2.5,
  "metadata": {
    "total_triangles": 5200,
    "polygon_reduction_percent": 0,
    "num_parts": 4,
    "materials": ["FrameMetal", "LensMirror", "Silicone"],
    "bounds": {
      "width_mm": 140.0,
      "height_mm": 95.0,
      "depth_mm": 25.0
    }
  },
  "warnings": [
    "Left and right lenses differ by 0.8mm in height (minor asymmetry)"
  ],
  "processing_time_seconds": 12.4,
  "analyzer_config": {
    "gaussian_kernel": 5,
    "canny_threshold1": 50,
    "canny_threshold2": 150,
    "rdp_epsilon": 2.0
  },
  "reference_docs": [
    "docs/avatar-design-kit/SKILL_FOUNDATION.md",
    "docs/avatar-design-kit/BLENDER_INTEGRATION_GUIDE.md"
  ]
}
```

---

## Error Handling and Fallbacks

### Image Analysis Fails

**Symptom**: "No contours detected"

**Root causes**:
1. Wireframe has very low contrast
2. Wireframe uses colored lines (not black on white)
3. Image is too small (< 400×400 px)

**Fallbacks** (in order):
1. Try local adaptive thresholding instead of Otsu
2. Convert to HSV, extract blue channel (if colored)
3. Upscale image 2× using bicubic interpolation, retry

**If still failing**: Return raw edge-detected image, ask user to verify wireframe quality manually.

### Curve Fitting Error

**Symptom**: "RMS error > 5 px" on simplified contour

**Causes**:
1. RDP epsilon too aggressive (removed important control points)
2. Contour has sharp corners (cusps) not well-fit by cubic Bezier

**Fallback**:
1. Reduce epsilon: retry with ε → ε / 2
2. Split at cusp: detect sharp turns (angle < 20°), subdivide contour
3. Use more control points: increase segment length

### Blender Script Execution Fails

**Symptom**: "Unknown object type" or MCP connection error

**Fallback**:
1. Retry with fresh Blender instance (restart MCP)
2. Simplify: export curves as SVG instead of GLB (for review)
3. Provide manual Blender workflow (step-by-step Python code to run locally)

---

## Integration with Blender MCP

### Prerequisites

- Blender ≥ 4.0 with Python API (bundled)
- Claude Code MCP connection to local Blender instance
- `wireframe_analyzer.py` in Python path (bundled with skill)

### MCP Methods Used

| Method | Purpose |
|--------|---------|
| `bpy.data.curves.new()` | Create curve objects |
| `bpy.data.objects.new()` | Create scene objects |
| `bpy.data.materials.new()` | Create PBR materials |
| `bpy.ops.export_scene.gltf()` | Export GLB |
| `bpy.ops.object.convert()` | Curve → Mesh |
| `bpy.ops.object.modifier_apply()` | Apply modifiers (Decimate, Subdiv) |

### Safe Practices

- **Don't modify user's existing scene**: work in isolated collection
- **Clean up on failure**: delete temporary objects before returning error
- **Log all steps**: verbose output helps debugging
- **Estimate before committing**: preview polygon count before conversion

---

## Quality Assurance

### Automated Tests

**For each detail_level** (quick, production, high):
- Test with glasses wireframe (front + side)
- Verify output within polygon budget
- Check file size ≤ target
- Validate materials are PBR (no procedural shaders)

**For error cases**:
- Low-contrast image → should trigger fallback
- Single view only → should warn, not fail
- Multi-view mismatch (different aspect ratios) → should warn

### Manual Validation

1. Open exported GLB in **three.js editor** (https://threejs.org/editor/)
   - Check geometry is correct
   - Verify materials render
   - Confirm no black faces or inverted normals

2. Compare side-by-side with original wireframe
   - Trace key features (lens outline, bridge position)
   - Measure aspect ratios, confirm ±5% match

3. Check polygon count vs. specification
   - Glasses: ≤ 5500 verts → ≤ 8000 tris
   - Helmet: ≤ 8000 verts → ≤ 12000 tris

---

## Configuration and Tuning

### Per-Project Defaults

Store in project's `avatar-design-kit/` as `skill_config.json`:

```json
{
  "geometry_type": "hybrid",
  "world_width_mm": 140.0,
  "material_preset": "brushed_metal",
  "canny_threshold1": 50,
  "canny_threshold2": 150,
  "rdp_epsilon_preview": 4.0,
  "rdp_epsilon_production": 2.0,
  "rdp_epsilon_high": 1.0,
  "bevel_depth_mm": 1.0,
  "target_file_size_mb": 8.0
}
```

### Tuning for Specific Wireframes

**If contours are over-simplified** (sharp features lost):
→ Decrease `rdp_epsilon` by 0.5–1.0

**If contours are noisy** (too many points):
→ Increase `rdp_epsilon` by 1–2

**If export is too large**:
→ Increase `detail_level` from "production" to "preview"
→ OR decrease `target_file_size_mb`

**If edge detection misses fine lines**:
→ Decrease `canny_threshold1` (e.g., 30 instead of 50)
→ Increase `gaussian_kernel` (e.g., 7 instead of 5)

---

## Documentation and Examples

**Reference documents**:
- `SKILL_FOUNDATION.md` — Deep technical foundation (algorithms, standards, theory)
- `BLENDER_INTEGRATION_GUIDE.md` — Blender Python API patterns and examples
- `wireframe_analyzer.py` — Source code for image processing pipeline

**Example usage**:
```python
from wireframe_skill import WireframeToBlenderSkill

skill = WireframeToBlenderSkill()

result = skill.process(
    image_path="aviator_front.png",
    image_path_side="aviator_side.png",
    view_type="multi",
    detail_level="production",
    geometry_type="hybrid",
    world_width_mm=140.0,
)

print(f"✓ Exported: {result['output_file']}")
print(f"  Size: {result['file_size_mb']} MB")
print(f"  Triangles: {result['metadata']['total_triangles']}")
```

---

## Troubleshooting Guide

| Problem | Diagnostic | Solution |
|---------|-----------|----------|
| "No contours detected" | Check wireframe PNG in image viewer | Increase Gaussian blur kernel, lower Canny thresholds |
| "Curve looks wrong" | Compare analyzer output (JSON) with wireframe | Visualize RDP simplification; reduce epsilon |
| "File too large" | Check output GLB file size | Enable Decimate, reduce detail_level |
| "Lenses asymmetrical" | Measure pixel widths in wireframe | Verify wireframe symmetry; may be original design |
| "Materials not showing" | Open GLB in three.js editor | Check material is Principled BSDF; no procedural nodes |
| "Mesh has holes" | Inspect in Blender | Increase curve resolution_u, check contour connectivity |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-04-27 | Initial release: wireframe analysis + Blender integration + GLB export |

---

## Related Docs

- Parent: `docs/avatar-design-kit/README.md`
- Foundation: `docs/avatar-design-kit/SKILL_FOUNDATION.md`
- Blender Reference: `docs/avatar-design-kit/BLENDER_INTEGRATION_GUIDE.md`
- Example Model: `docs/avatar-design-kit/BLENDER_BUILD_LOG.md`
- Wireframe Analyzer: `docs/avatar-design-kit/wireframe_analyzer.py`

---

**Status**: Ready for Integration  
**Next Phase**: Build Claude Skill wrapper + Blender MCP orchestration  
**Estimated Complexity**: Medium (image processing + Blender automation + error handling)  
**Test Coverage**: Manual validation on glasses wireframes (front + side)
