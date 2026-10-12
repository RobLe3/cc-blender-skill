"""Read-only evaluated collider checks and selection-scoped static FBX export.

Load inside Blender Python. No MCP server or source-mesh repair is performed.
"""
import itertools
import math
import re

PREFIXES = ('UCX_', 'UBX_', 'USP_', 'UCP_')


def validate_collider(obj):
    """Return a JSON-safe report. Primitive checks accept local-axis authored shapes."""
    import bpy
    import bmesh

    errors = []
    report = {'name': obj.name, 'passed': False, 'errors': errors}
    if obj.type != 'MESH':
        errors.append('Collider must be a mesh')
        return report
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        if not bm.verts or not bm.faces:
            errors.append('Empty collider')
            return report
        local = [v.co.copy() for v in bm.verts]
        lo = [min(c[i] for c in local) for i in range(3)]
        hi = [max(c[i] for c in local) for i in range(3)]
        local_eps = max(1e-9, math.dist(lo, hi) * 1e-6)
        prefix = next((p for p in PREFIXES if obj.name.startswith(p)), None)
        if prefix is None:
            errors.append('Unknown collision prefix')
        if prefix in ('UBX_', 'USP_', 'UCP_'):
            axes = [evaluated.matrix_world.to_3x3().col[i] for i in range(3)]
            scales = [v.length for v in axes]
            if min(scales) <= 0 or max(scales) - min(scales) > max(scales) * 1e-6:
                errors.append('Primitive collider requires uniform nonzero world scale; use UCX instead')
            if any(abs(axes[i].dot(axes[j])) > max(scales) ** 2 * 1e-6
                   for i, j in itertools.combinations(range(3), 2)):
                errors.append('Primitive collider cannot be sheared')
        if prefix == 'UBX_':
            corners = list(itertools.product(*[(lo[i], hi[i]) for i in range(3)]))
            if len(local) != 8 or any(not any(math.dist(c, corner) <= local_eps
                                             for corner in corners) for c in local):
                errors.append('UBX must be an eight-vertex local-axis rectangular box; use UCX otherwise')
        elif prefix in ('USP_', 'UCP_'):
            center = [(lo[i] + hi[i]) / 2 for i in range(3)]
            if prefix == 'USP_':
                radius = max(math.dist(c, center) for c in local)
                if any(abs(math.dist(c, center) - radius) > local_eps * 10 for c in local):
                    errors.append('USP vertices must form a sphere, not an ellipsoid')
            else:
                # A capsule is a cylinder plus hemispheres, not a cylinder with flat caps.
                matches = []
                for axis in range(3):
                    other = [i for i in range(3) if i != axis]
                    radius = max(math.hypot(*(c[i] - center[i] for i in other)) for c in local)
                    half = (hi[axis] - lo[axis]) / 2 - radius
                    matches.append(half > local_eps and all(
                        abs(math.sqrt(sum((c[i] - center[i]) ** 2 for i in other)
                                      + max(abs(c[axis] - center[axis]) - half, 0) ** 2)
                            - radius) <= local_eps * 10 for c in local))
                if not any(matches):
                    errors.append('UCP must be a local-axis capsule with hemispherical ends; use UCX otherwise')

        # Validate the evaluated world-space surface that will actually be exported.
        bm.transform(evaluated.matrix_world)
        bm.normal_update()
        coords = [v.co for v in bm.verts]
        lo = [min(c[i] for c in coords) for i in range(3)]
        hi = [max(c[i] for c in coords) for i in range(3)]
        eps = max(1e-9, math.dist(lo, hi) * 1e-6)
        if any(not edge.is_manifold or not edge.is_contiguous for edge in bm.edges):
            errors.append('Surface must be closed manifold with consistent winding')
        unseen = set(bm.verts)
        components = 0
        while unseen:
            components += 1
            pending = [unseen.pop()]
            while pending:
                for edge in pending.pop().link_edges:
                    for vertex in edge.verts:
                        if vertex in unseen:
                            unseen.remove(vertex)
                            pending.append(vertex)
        if components != 1:
            errors.append('Use one connected hull per collider object')
        volume = bm.calc_volume(signed=True)
        if volume <= eps ** 3:
            errors.append('Collider must have nonzero volume and outward winding')
        for face in bm.faces:
            if face.calc_area() <= eps ** 2:
                errors.append('Degenerate face')
                break
            anchor = face.verts[0].co
            if any(abs((v.co - anchor).dot(face.normal)) > eps for v in face.verts):
                errors.append('Non-planar face; triangulate explicitly and revalidate')
                break
            if any((co - anchor).dot(face.normal) > eps for co in coords):
                errors.append('Non-convex surface or inward face')
                break
        report.update(passed=not errors, vertices=len(bm.verts), faces=len(bm.faces),
                      volume=volume, tolerance=eps)
        return report
    finally:
        bm.free()
        evaluated.to_mesh_clear()


def collision_report(render_obj, colliders):
    """Require correctly named colliders belonging to this render mesh."""
    items = list(colliders)
    errors = []
    if render_obj.type != 'MESH':
        errors.append('Render object must be a mesh')
    if not items or len({o.as_pointer() for o in items}) != len(items):
        errors.append('Provide a nonempty, distinct collider list')
    results = []
    for obj in items:
        item = validate_collider(obj)
        if not re.fullmatch(r'(?:UCX|UBX|USP|UCP)_' + re.escape(render_obj.name)
                            + r'(?:_\d+)?', obj.name):
            item['errors'].append('Collider name must match the exact render mesh name')
        if obj == render_obj:
            item['errors'].append('Collider and render object must be separate')
        if obj.name.startswith(('UBX_', 'USP_')):
            scales = [render_obj.matrix_world.to_3x3().col[i].length for i in range(3)]
            if max(scales) - min(scales) > max(scales) * 1e-6:
                item['errors'].append('Box/sphere collision is unsuitable for a non-uniformly scaled render object')
        item['passed'] = not item['errors']
        results.append(item)
    return {'passed': not errors and all(r['passed'] for r in results),
            'render_object': render_obj.name, 'errors': errors, 'colliders': results}


def export_collision_fbx(render_obj, colliders, filepath, **options):
    """Export one static mesh plus checked colliders; preserve selection and mode."""
    import bpy
    from pathlib import Path

    colliders = list(colliders)
    filepath = Path(filepath)
    if not filepath.is_absolute() or filepath.suffix.lower() != '.fbx' or not filepath.parent.is_dir():
        raise ValueError('Supply an absolute FBX path in an existing directory')
    if filepath.exists():
        raise FileExistsError('Choose a new FBX path; do not overwrite an accepted output')
    report = collision_report(render_obj, colliders)
    if not report['passed']:
        raise ValueError('Collision preflight failed: ' + repr(report))
    selected = list(bpy.context.selected_objects)
    active = bpy.context.view_layer.objects.active
    mode = active.mode if active else 'OBJECT'
    defaults = dict(apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL',
                    bake_space_transform=True, use_mesh_modifiers=True,
                    mesh_smooth_type='FACE', bake_anim=False,
                    embed_textures=True, path_mode='COPY', axis_forward='-Z', axis_up='Y')
    if {'filepath', 'use_selection', 'object_types'} & options.keys():
        raise ValueError('Selection scope and filepath cannot be overridden')
    defaults.update(options)
    try:
        if mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        for obj in [render_obj, *colliders]:
            if obj.name not in bpy.context.view_layer.objects or obj.hide_get() or obj.hide_select:
                raise ValueError('Export object is not selectable in the active view layer: ' + obj.name)
            obj.select_set(True)
        bpy.context.view_layer.objects.active = render_obj
        result = bpy.ops.export_scene.fbx(filepath=str(filepath), use_selection=True,
                                         object_types={'MESH'}, **defaults)
        if 'FINISHED' not in result or not Path(filepath).is_file() or Path(filepath).stat().st_size == 0:
            raise RuntimeError('FBX export did not create a nonempty file')
        return report
    finally:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in selected:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = active
        if mode != 'OBJECT':
            bpy.ops.object.mode_set(mode=mode)
