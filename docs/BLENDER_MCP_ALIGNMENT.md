# Blender MCP Server Alignment & Integration Strategy

**Date**: 2026-04-27  
**Purpose**: Map existing Blender MCP capabilities to wireframe-to-3D skill, avoid duplication, identify what still needs building.

**MCP Server Location**: `/Users/roble/.tools/blender-mcp`  
**Version**: blender_mcp-1.5.5

---

## Existing Blender MCP Tools

### Tier 1: Scene Management (Core Capabilities)

**✓ Available & Directly Usable**:

1. **`execute_blender_code(code: str) → str`**
   - **Purpose**: Execute arbitrary Python code in Blender context
   - **Perfect for**: Running all curve creation, mesh conversion, material assignment
   - **Status**: Ready to use
   - **In our skill**: Used for all Blender operations (curves, meshes, materials, export)

2. **`get_scene_info() → str`**
   - **Purpose**: Query current scene composition (objects, materials, collections)
   - **Perfect for**: Validation before export, checking mesh count
   - **Status**: Ready to use
   - **In our skill**: Used for post-conversion validation

3. **`get_object_info(object_name: str) → str`**
   - **Purpose**: Get properties of specific object (bounds, mesh info, modifiers)
   - **Perfect for**: Symmetry checks, aspect ratio validation
   - **Status**: Ready to use
   - **In our skill**: Used for topology validation

4. **`get_viewport_screenshot(max_size: int = 800) → Image`**
   - **Purpose**: Capture 3D viewport as PNG
   - **Perfect for**: Preview rendering before export, visual validation
   - **Status**: Ready to use
   - **In our skill**: Optional, for preview image generation

### Tier 2: Asset Libraries (Not Needed for This Skill)

**Available but not used**:
- Polyhaven asset download/search (for base meshes, textures, HDRIs)
- Sketchfab model download/search (for reference models)
- Hyper3D generation (text-to-3D, image-to-3D)
- Hunyuan3D generation (text-to-3D)

**Why not used**: Our skill generates from 2D wireframes, not from AI generation services. These are alternatives to our approach, not complements.

---

## Skill Implementation Strategy

### What the MCP Already Provides

```
✓ Blender Python execution environment
✓ Scene introspection (get_scene_info, get_object_info)
✓ Screenshot rendering (visual validation)
```

### What We Build On Top

```
→ wireframe_analyzer.py (image processing — NOT in MCP)
→ Blender orchestration layer (Python code generators for MCP's execute_blender_code)
→ Error handling & parameter tuning (skill decision logic)
```

### Architecture Diagram

```
User Input
   ↓
[Skill Decision Logic]
   ├─→ Validate parameters
   ├─→ Call wireframe_analyzer.py
   └─→ Parse analyzer output → JSON
        ↓
    [Blender MCP orchestrator]
    (generates Python code)
        ↓
    execute_blender_code(generated_code)
        ├─→ Create curves from control points
        ├─→ Convert to mesh
        ├─→ Apply materials
        ├─→ Validate (get_object_info, get_scene_info)
        └─→ Export GLB
             ↓
        Output .glb file
             ↓
    [Post-processing]
    (check file size, validate, return metadata)
```

---

## Integration Points

### 1. **Wireframe Analysis** (Pre-MCP)

Our responsibility:
```python
from wireframe_analyzer import WireframeAnalyzer

analyzer = WireframeAnalyzer(image_path, verbose=True)
result = analyzer.process(
    rdp_epsilon=2.0,
    canny_threshold1=50,
    canny_threshold2=150,
)
# Output: JSON with Bezier control points
```

This runs **locally** (not in MCP), outputs JSON.

### 2. **Blender Curve Creation** (Via `execute_blender_code`)

We generate Python code that we pass to MCP:

```python
code = f"""
import bpy

# Create curve data
curve_data = bpy.data.curves.new(name='RightLens', type='CURVE')
curve_data.dimensions = '3D'

# Populate from analyzer output
bezier_points = {control_points_json}  # From analyzer
# ... rest of curve setup code ...
"""

result = mcp.execute_blender_code(code=code)
```

The MCP **executes this in Blender's Python context** and returns status/errors.

### 3. **Mesh Conversion & Materials** (Via `execute_blender_code`)

Same pattern: generate code, execute in Blender.

```python
code = """
# Convert curves to mesh
bpy.ops.object.convert(target='MESH')

# Create materials
mat = bpy.data.materials.new('FrameMetal')
mat.metallic = 1.0
# ... etc ...
"""

result = mcp.execute_blender_code(code=code)
```

### 4. **Validation** (Via MCP Info Tools)

```python
# Get mesh stats for validation
info = mcp.get_object_info(object_name='RightLens')
# Returns: vertex count, face count, bounds, etc.

# Get full scene summary
scene_info = mcp.get_scene_info()
# Returns: all objects, materials, collections
```

### 5. **Export** (Via `execute_blender_code`)

```python
code = """
bpy.ops.export_scene.gltf(
    filepath='/path/to/output.glb',
    export_format='GLB',
    ...
)
"""

result = mcp.execute_blender_code(code=code)
```

### 6. **Visual Validation** (Optional, Via `get_viewport_screenshot`)

```python
# After export, optionally capture preview
screenshot = mcp.get_viewport_screenshot(max_size=800)
# Returns: PNG image of viewport
```

---

## Code Generation Strategy

Instead of calling Blender APIs directly, the skill **generates Python code strings** that are passed to `execute_blender_code()`.

### Example: Curve Creation Code Generator

```python
def generate_curve_creation_code(name: str, control_points: list, z_offset: float = 0.0) -> str:
    """Generate Blender Python code to create a curve from control points."""
    
    cp_json = json.dumps(control_points)
    
    code = f"""
import bpy

# Create curve
curve_data = bpy.data.curves.new(name='{name}', type='CURVE')
curve_data.dimensions = '3D'
curve_obj = bpy.data.objects.new('{name}', curve_data)
bpy.context.collection.objects.link(curve_obj)

# Populate control points
control_points = {cp_json}
spline = curve_data.splines.new(type='BEZIER')
spline.bezier_points.add(len(control_points) - 1)

for i, cp in enumerate(control_points):
    pt = spline.bezier_points[i]
    x, y = cp[0], cp[1]
    pt.co = (x, y, {z_offset}, 1.0)
    pt.handle_left_type = 'ALIGNED'
    pt.handle_right_type = 'ALIGNED'

curve_data.resolution_u = 24
curve_data.bevel_depth = 0.001
curve_data.use_fill_caps = True
"""
    return code
```

Then call it:
```python
code = generate_curve_creation_code('RightLens', control_points)
result = mcp.execute_blender_code(code=code)  # MCP executes in Blender
```

---

## What Still Needs to Be Built

### 1. **Skill Orchestrator** (Python wrapper)

```python
class WireframeToBlenderSkill:
    def __init__(self):
        self.mcp = BlenderMCP()  # Connection to MCP
    
    def process(self, image_path, view_type='front', **kwargs):
        # 1. Validate input
        # 2. Analyze wireframe (wireframe_analyzer.py)
        # 3. Generate Blender code (code generators)
        # 4. Execute via MCP
        # 5. Validate output
        # 6. Return results
```

### 2. **Code Generators** (for different operations)

- `generate_curve_creation_code()` — create curves from control points
- `generate_mesh_conversion_code()` — convert curves to mesh
- `generate_material_creation_code()` — create PBR materials
- `generate_export_code()` — export to GLB
- `generate_validation_code()` — symmetry/aspect-ratio checks
- `generate_decimate_code()` — reduce polygon count if needed

### 3. **MCP Wrapper** (communicate with `execute_blender_code`)

```python
class BlenderMCP:
    def __init__(self):
        # Connection to MCP server at localhost:9876
        pass
    
    def execute_code(self, code: str) -> dict:
        """Send Python code to Blender, get result"""
        pass
    
    def get_scene_info(self) -> dict:
        """Query scene composition"""
        pass
    
    def get_object_info(self, name: str) -> dict:
        """Query specific object"""
        pass
```

### 4. **Error Handling & Retry Logic**

- MCP connection failures → retry with exponential backoff
- Blender code execution errors → parse error messages, suggest fixes
- File export failures → debug, suggest parameter changes

### 5. **Documentation & Examples**

✓ Already created: `BLENDER_INTEGRATION_GUIDE.md`, `SKILL_FOUNDATION.md`, `WIREFRAME_SKILL.md`

---

## Key Insight: Avoid Reimplementing

**Do NOT try to duplicate these MCP capabilities**:
- Curve/mesh creation APIs (use `execute_blender_code` with generated code)
- Export functionality (MCP already talks to Blender's exporter)
- Scene introspection (use `get_scene_info`, `get_object_info`)

**DO extend MCP's capabilities with**:
- Image analysis pipeline (our `wireframe_analyzer.py`)
- Intelligent code generation (based on user parameters)
- Decision logic (which parameters, how to optimize, error recovery)

---

## Implementation Checklist

### Phase 1: Core Orchestration

- [ ] Create `WireframeToBlenderSkill` class
- [ ] Create `BlenderMCP` wrapper (thin client to execute_blender_code)
- [ ] Create code generators for:
  - [ ] Curve creation from control points
  - [ ] Mesh conversion
  - [ ] Material creation (PBR)
  - [ ] Export to GLB

### Phase 2: Validation & Error Handling

- [ ] Implement `validate_output()` using `get_object_info`
- [ ] Implement `check_symmetry()` for paired parts
- [ ] Implement retry logic for MCP connection failures
- [ ] Parse Blender error messages, suggest fixes

### Phase 3: Optimization

- [ ] Implement `apply_decimate()` code generator
- [ ] Implement file size checking
- [ ] Implement polygon budget enforcement

### Phase 4: Integration

- [ ] Package as Claude Skill
- [ ] Write skill prompt/instructions
- [ ] Add to skill registry
- [ ] Document for users

---

## Example: Complete Workflow Via MCP

```python
# Step 1: Analyze wireframe (local)
from wireframe_analyzer import WireframeAnalyzer

analyzer = WireframeAnalyzer('glasses_front.png')
result = analyzer.process(rdp_epsilon=2.0)
control_points = result['bezier_curves']

# Step 2: Generate Blender code
code = generate_curve_creation_code('RightLens', control_points[0])

# Step 3: Execute in Blender via MCP
from blender_mcp import BlenderMCP
mcp = BlenderMCP()
exec_result = mcp.execute_code(code)

# Step 4: Validate
scene_info = mcp.get_scene_info()
if scene_info['objects'] > 0:
    print("✓ Curves created successfully")

# Step 5: Mesh conversion
mesh_code = generate_mesh_conversion_code()
mcp.execute_code(mesh_code)

# Step 6: Export
export_code = generate_export_code('/tmp/model.glb')
mcp.execute_code(export_code)

# Step 7: Verify output
import os
size_mb = os.path.getsize('/tmp/model.glb') / (1024*1024)
print(f"✓ Exported: {size_mb:.2f} MB")
```

---

## Summary

| Task | Tool | Approach |
|------|------|----------|
| Wireframe analysis | `wireframe_analyzer.py` | Local Python (not in MCP) |
| Curve creation | `execute_blender_code` | Generate Python code, send to MCP |
| Mesh conversion | `execute_blender_code` | Generate Python code, send to MCP |
| Material creation | `execute_blender_code` | Generate Python code, send to MCP |
| Export to GLB | `execute_blender_code` | Generate Python code, send to MCP |
| Scene validation | `get_object_info`, `get_scene_info` | Direct MCP calls |
| Visual preview | `get_viewport_screenshot` | Direct MCP call (optional) |

**Key principle**: Use MCP's flexible `execute_blender_code` as a general-purpose Blender executor, wrapped with smart code generators and error handling.

---

**Next Steps**:
1. Build `BlenderMCP` wrapper class
2. Build code generators for each operation
3. Integrate with `wireframe_analyzer.py`
4. Package as Claude Skill
5. Test end-to-end with glasses wireframes
