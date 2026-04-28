# Development Guide — CC Blender Skill

**Status**: Foundation Complete. Ready for Phase 1 Implementation.

**Timeline**: 3–5 days estimated to full implementation.

---

## Phase 1: Core Infrastructure (1–2 days)

### Goals
- Blender MCP client wrapper
- Code generators for each Blender operation
- Basic orchestration loop
- Unit tests for generators

### Files to Create

**`src/blender_mcp.py`** — Thin client to Blender MCP `execute_blender_code()`

```python
class BlenderMCP:
    def __init__(self, host="localhost", port=9876):
        self.host = host
        self.port = port
    
    async def execute_code(self, code: str) -> dict:
        """Send Python code to Blender, return result."""
        pass
    
    async def get_scene_info(self) -> dict:
        """Query current scene composition."""
        pass
    
    async def get_object_info(self, name: str) -> dict:
        """Query specific object properties."""
        pass
```

**`src/code_generators.py`** — Generate Blender Python code strings

```python
def generate_curve_creation_code(name: str, control_points: list) -> str:
    """Generate code to create a Bezier curve."""
    pass

def generate_mesh_conversion_code(curve_names: list) -> str:
    """Generate code to convert curves to meshes."""
    pass

def generate_material_creation_code(material_preset: str) -> str:
    """Generate code to create PBR materials."""
    pass

def generate_export_code(output_path: str) -> str:
    """Generate code to export scene to GLB."""
    pass

def generate_validation_code() -> str:
    """Generate code to validate mesh and return stats."""
    pass
```

**`src/wireframe_skill.py`** — Main skill orchestrator

```python
class WireframeToBlenderSkill:
    def __init__(self, blender_mcp: BlenderMCP):
        self.mcp = blender_mcp
    
    async def process(self, 
                     image_path: str,
                     view_type: str = 'front',
                     **parameters) -> dict:
        """End-to-end workflow."""
        pass
```

**`tests/test_code_generators.py`** — Unit tests for code generators

```python
def test_generate_curve_creation_code():
    # Verify generated code is valid Python
    # Verify placeholders are filled correctly
    pass

def test_generate_mesh_conversion_code():
    pass
```

### Implementation Checklist

- [ ] Create `BlenderMCP` class with `execute_code()` method
- [ ] Implement async socket communication to MCP server
- [ ] Create all 5 code generators (curves, meshes, materials, export, validation)
- [ ] Write unit tests for each generator
- [ ] Create `WireframeToBlenderSkill` orchestrator class
- [ ] Integrate `wireframe_analyzer.py` with skill
- [ ] Basic error handling (catch exceptions, log)

### Key References
- [BLENDER_INTEGRATION_GUIDE.md](./docs/BLENDER_INTEGRATION_GUIDE.md) § 3–9 — Code patterns
- [BLENDER_BEST_PRACTICES.md](./docs/BLENDER_BEST_PRACTICES.md) — Performance optimization patterns
- [BLENDER_MCP_ALIGNMENT.md](./docs/BLENDER_MCP_ALIGNMENT.md) — MCP integration strategy

---

## Phase 2: Validation & Optimization (1–2 days)

### Goals
- Topology validation (symmetry, aspect ratio)
- File size enforcement
- Intelligent error recovery
- Integration tests

### Files to Create

**`src/validators.py`** — Validation functions using MCP

```python
async def validate_symmetry(mcp: BlenderMCP, left_obj: str, right_obj: str) -> bool:
    """Check if left/right objects are symmetrical within tolerance."""
    pass

async def validate_aspect_ratio(mcp: BlenderMCP, obj_name: str, target_ratio: float) -> bool:
    """Check if object aspect ratio matches target within tolerance."""
    pass

async def validate_mesh(mcp: BlenderMCP, obj_name: str) -> list:
    """Return list of mesh issues (isolated vertices, degenerate faces, etc)."""
    pass
```

**`src/optimizers.py`** — Size and performance optimization

```python
async def check_and_optimize_glb(mcp: BlenderMCP, 
                                  filepath: str, 
                                  max_size_mb: int = 15) -> bool:
    """Verify file size; apply Decimate if needed."""
    pass
```

**`src/error_handlers.py`** — Blender error parsing and recovery

```python
def parse_blender_error(error_msg: str) -> tuple:
    """Parse Blender error message, return (error_type, suggestion)."""
    pass

async def retry_with_fallback(func, *args, retries: int = 3, **kwargs):
    """Retry function with exponential backoff."""
    pass
```

**`tests/test_blender_integration.py`** — Integration tests with mock Blender

```python
@pytest.mark.asyncio
async def test_full_workflow_glasses():
    # Test with glasses wireframes (front + side)
    # Verify output GLB is valid
    # Check file size < 15 MB
    pass
```

### Implementation Checklist

- [ ] Create validators (symmetry, aspect ratio, mesh integrity)
- [ ] Create optimizers (file size, Decimate strategy)
- [ ] Create error handlers (parsing, retry logic)
- [ ] Write integration tests with sample wireframes
- [ ] Test error cases (bad image, oversized output)
- [ ] Performance profiling

### Key References
- [SKILL_FOUNDATION.md](./docs/SKILL_FOUNDATION.md) § 7 — Validation rules
- [WIREFRAME_SKILL.md](./docs/WIREFRAME_SKILL.md) § 8 — Error handling
- [BLENDER_BEST_PRACTICES.md](./docs/BLENDER_BEST_PRACTICES.md) § 8 — Export optimization

---

## Phase 3: Skill Integration (1 day)

### Goals
- Package as Claude Skill
- Create skill prompt/instructions
- End-to-end testing
- Documentation

### Files to Create

**`SKILL.md`** — Skill instructions for Claude

```markdown
# Wireframe-to-3D Conversion Skill

Converts 2D orthographic wireframes to parametric 3D Blender models.

## When to use this skill

- User provides wireframe PNG(s)
- Need to create 3D model in Blender
- Target: optimized glTF/GLB export

## How it works

1. Analyze wireframe image(s)
2. Extract contours, fit Bezier curves
3. Create parametric curves in Blender
4. Convert to mesh with proper topology
5. Apply materials and export GLB

## Parameters

- `image_path`: Path to wireframe PNG
- `view_type`: 'front', 'side', 'multi'
- `detail_level`: 'preview', 'production', 'high'
- ... (see WIREFRAME_SKILL.md for full list)
```

**`examples/workflow_glasses.py`** — Example end-to-end usage

```python
async def main():
    mcp = BlenderMCP()
    skill = WireframeToBlenderSkill(mcp)
    
    result = await skill.process(
        image_path='glasses_front.png',
        image_path_side='glasses_side.png',
        view_type='multi',
        detail_level='production'
    )
    
    print(f"✓ Exported: {result['output_file']}")
```

**`docs/IMPLEMENTATION_LOG.md`** — Track progress and decisions

```markdown
# Implementation Log

## 2026-04-27 — Phase 1 Kickoff

### Completed
- ✓ Created BlenderMCP wrapper
- ✓ Implemented all code generators

### In Progress
- [ ] Unit tests for generators
- [ ] Integration tests

### Next Steps
- Phase 2: Validation & Optimization
```

### Implementation Checklist

- [ ] Create `SKILL.md` with instructions
- [ ] Package skill for Claude Code
- [ ] Create example workflows
- [ ] Test with glasses wireframes (front + side)
- [ ] Generate documentation & examples
- [ ] Write implementation log
- [ ] Tag v0.1.0 release

### Key References
- [WIREFRAME_SKILL.md](./docs/WIREFRAME_SKILL.md) — Skill specification
- [SKILL_RESEARCH_SUMMARY.md](./docs/SKILL_RESEARCH_SUMMARY.md) — Quick overview

---

## Development Workflow

### Setup

```bash
# Clone repo
git clone git@github.com:RobLe3/cc-blender-skill.git
cd cc-blender-skill

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install dev tools
pip install black flake8 mypy pytest pytest-cov pytest-asyncio
```

### Code Style

```bash
# Format code
black src/ tests/

# Lint
flake8 src/ tests/

# Type check
mypy src/

# Test
pytest tests/ -v --cov=src
```

### Branching

```bash
# Feature branches from main
git checkout -b feature/phase-1-infrastructure
git commit -m "feat: implement BlenderMCP wrapper"
git push origin feature/phase-1-infrastructure

# Then open PR for review
```

### Testing

```bash
# Unit tests (no Blender required)
pytest tests/test_code_generators.py -v

# Integration tests (requires Blender MCP)
pytest tests/test_blender_integration.py -v

# Coverage report
pytest --cov=src --cov-report=html
```

---

## Key Decision Points

### 1. Async vs. Sync Code

**Decision**: Use `async/await` for MCP calls  
**Reason**: Non-blocking, scalable for multiple parallel skill invocations

### 2. Code Generation vs. Direct API

**Decision**: Generate code strings, execute via `execute_blender_code()`  
**Reason**: Avoids reimplementing Blender APIs, leverages existing MCP flexibility

### 3. Error Handling Strategy

**Decision**: Attempt recovery first, then fallback  
**Example**: Low-contrast image → try local adaptive thresholding → fallback to manual suggestion  
**Reason**: Better UX than immediate failure

### 4. File Organization

**Decision**: Keep research docs in `docs/`, implementation in `src/`  
**Reason**: Clear separation of foundation knowledge from code

---

## Testing Strategy

### Unit Tests (No Blender Needed)
- Code generators produce valid Python syntax
- Analyzer processes sample images correctly
- Validators return expected results for test data

### Integration Tests (Requires Blender MCP)
- End-to-end with glasses wireframes (front + side)
- Output GLB is valid (can load in three.js)
- File size < 15 MB
- Error cases (bad input, oversized output)

### Manual Tests
- Test with different detail levels (quick, production, high)
- Test with single view vs. multi-view
- Test error recovery (low contrast, asymmetrical design)

---

## Documentation Requirements

- Code comments: focus on WHY, not WHAT
- Docstrings: function signature, args, returns, raises
- README: quick start + architecture diagram
- SKILL.md: user-facing instructions
- Examples: end-to-end workflows

---

## Performance Targets

- Image analysis: < 1 second
- Blender operations: < 10 seconds
- Export & optimization: < 5 seconds
- **Total**: < 15 seconds

**If exceeding targets**:
- Profile with `cProfile`
- Apply optimizations from BLENDER_BEST_PRACTICES.md § 1 (foreach_set, context caching)
- Reduce curve resolution if needed

---

## Success Criteria

Skill is production-ready when:

1. ✅ Accepts wireframe PNG(s) + parameters
2. ✅ Outputs valid GLB file ≤ 15 MB
3. ✅ Handles error cases gracefully
4. ✅ All tests passing (unit + integration)
5. ✅ Documentation complete
6. ✅ Example workflows working
7. ✅ Code reviewed and clean (black, flake8, mypy)

---

## Resources

### Code References
- [wireframe_analyzer.py](./src/wireframe_analyzer.py) — Image processing pipeline
- [BLENDER_INTEGRATION_GUIDE.md](./docs/BLENDER_INTEGRATION_GUIDE.md) — API patterns
- [BLENDER_BEST_PRACTICES.md](./docs/BLENDER_BEST_PRACTICES.md) — Performance & standards

### External Documentation
- [Blender Python API](https://docs.blender.org/api/current/)
- [Khronos glTF 2.0 Spec](https://github.com/KhronosGroup/glTF/tree/master/specification/2.0)
- [OpenCV Documentation](https://docs.opencv.org/)

---

**Next Step**: Start Phase 1 — Create `src/blender_mcp.py` and `src/code_generators.py`
