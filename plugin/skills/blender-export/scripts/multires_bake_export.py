"""Bake a single-material Multires mesh and export its cage, restoring context.

Run inside Blender. The output normal image/material connection is intentional;
temporary selection, mode, bake settings, and subdivision levels are restored.
"""
from contextlib import contextmanager
from pathlib import Path


def multires_bake_settings(render):
    """Resolve the 5.x and 4.x property layouts without swallowing bake errors."""
    if hasattr(render.bake, 'use_multires'):
        return render.bake, 'use_multires', render.bake, 'type'
    if hasattr(render, 'use_bake_multires') and hasattr(render, 'bake_type'):
        return render, 'use_bake_multires', render, 'bake_type'
    raise RuntimeError('Installed Blender does not expose Multires baking settings')


@contextmanager
def cage_bake_context(obj):
    """Keep level 0 active until the caller has exported, then restore state."""
    import bpy

    if obj.type != 'MESH' or not obj.data.uv_layers:
        raise ValueError('Multires bake requires a mesh with UVs')
    modifiers = [m for m in obj.modifiers if m.type == 'MULTIRES']
    if len(modifiers) != 1 or obj.modifiers[-1] != modifiers[0]:
        raise ValueError('Exactly one Multires modifier must be last in the stack')
    multires = modifiers[0]
    if not multires.total_levels or not multires.show_viewport:
        raise ValueError('Multires needs sculpt levels and must be enabled')
    if obj.name not in bpy.context.view_layer.objects or obj.hide_get() or obj.hide_select:
        raise ValueError('Bake target must be selectable in the active view layer')
    selected = list(bpy.context.selected_objects)
    active = bpy.context.view_layer.objects.active
    mode = active.mode if active else 'OBJECT'
    render = bpy.context.scene.render
    use_owner, use_attr, type_owner, type_attr = multires_bake_settings(render)
    saved = [(multires, 'levels', multires.levels),
             (multires, 'render_levels', multires.render_levels),
             (render, 'engine', render.engine),
             (type_owner, type_attr, getattr(type_owner, type_attr)),
             (use_owner, use_attr, getattr(use_owner, use_attr)),
             (render.bake, 'margin', render.bake.margin)]
    try:
        if mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        multires.levels = 0  # The bake target and exported cage must be identical.
        multires.render_levels = multires.total_levels
        render.engine = 'CYCLES'
        setattr(use_owner, use_attr, True)
        normal_types = [e.identifier for e in type_owner.bl_rna.properties[type_attr].enum_items]
        normal_type = 'NORMALS' if 'NORMALS' in normal_types else 'NORMAL'
        if normal_type not in normal_types:
            raise RuntimeError('Multires normal-map baking is unavailable')
        setattr(type_owner, type_attr, normal_type)
        render.bake.margin = 16
        yield multires
    finally:
        # Restore the Multires flag before the old type; that flag changes the enum.
        for owner, attr, value in reversed(saved):
            setattr(owner, attr, value)
        bpy.ops.object.select_all(action='DESELECT')
        for item in selected:
            item.select_set(True)
        bpy.context.view_layer.objects.active = active
        if mode != 'OBJECT':
            bpy.ops.object.mode_set(mode=mode)


def bake_export_cage(obj, normal_path, fbx_path, export_fbx=None):
    """Bake the active image in one used material, connect normals, export only obj.

    export_fbx, when supplied, is a callable taking the destination path. It must
    finish synchronously and preserve selection scope; useful for custom FBX presets.
    """
    import bpy

    materials = {p.material_index for p in obj.data.polygons} if obj.type == 'MESH' else set()
    if len(materials) != 1:
        raise ValueError('This recipe supports one used material; split multi-material bakes explicitly')
    index = next(iter(materials))
    mat = obj.data.materials[index] if index < len(obj.data.materials) else None
    node = mat.node_tree.nodes.active if mat and mat.use_nodes else None
    if not node or node.type != 'TEX_IMAGE' or not node.image:
        raise ValueError('The material active node must be an Image Texture with a bake target')
    image = node.image
    if mat.users > 1 or image.users > 1:
        raise ValueError('Use a single-user material and bake image; do not change other objects')
    if image.colorspace_settings.name != 'Non-Color':
        raise ValueError('Normal-map bake target must use Non-Color data')
    bsdf = next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bsdf is None or bsdf.inputs['Normal'].is_linked:
        raise ValueError('Use a Principled material with an unlinked Normal input; do not overwrite an existing normal setup')
    normal_path, fbx_path = Path(normal_path), Path(fbx_path)
    if not normal_path.is_absolute() or not fbx_path.is_absolute() or normal_path.suffix.lower() != '.png':
        raise ValueError('Supply absolute PNG normal-map and FBX output paths')
    if fbx_path.suffix.lower() != '.fbx':
        raise ValueError('Cage export destination must end in .fbx')
    if normal_path.exists() or fbx_path.exists():
        raise FileExistsError('Choose new output paths; accepted outputs must not be overwritten')
    if not normal_path.parent.is_dir() or not fbx_path.parent.is_dir():
        raise ValueError('Output directories must already exist')
    image_state = (image.filepath_raw, image.file_format)
    normal_node = None
    try:
        with cage_bake_context(obj) as multires:
            result = bpy.ops.object.bake_image()
            if 'FINISHED' not in result:
                raise RuntimeError('Multires bake did not finish')
            image.filepath_raw = str(normal_path)
            image.file_format = 'PNG'
            image.save()
            if not normal_path.is_file() or normal_path.stat().st_size == 0:
                raise RuntimeError('Bake did not save a nonempty normal image')
            normal_node = mat.node_tree.nodes.new('ShaderNodeNormalMap')
            normal_node.space = 'TANGENT'
            mat.node_tree.links.new(node.outputs['Color'], normal_node.inputs['Color'])
            mat.node_tree.links.new(normal_node.outputs['Normal'], bsdf.inputs['Normal'])
            if export_fbx is None:
                result = bpy.ops.export_scene.fbx(
                    filepath=str(fbx_path), use_selection=True, object_types={'MESH'},
                    apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL',
                    bake_space_transform=True, use_mesh_modifiers=True,
                    mesh_smooth_type='FACE', bake_anim=False, embed_textures=True,
                    path_mode='COPY', axis_forward='-Z', axis_up='Y')
                if 'FINISHED' not in result:
                    raise RuntimeError('Cage export did not finish')
            else:
                export_fbx(str(fbx_path))
            if not fbx_path.is_file() or fbx_path.stat().st_size == 0:
                raise RuntimeError('Cage export did not create a nonempty FBX')
            return {'object': obj.name, 'bake_level': 0, 'export_level': 0,
                    'sculpt_levels': multires.total_levels,
                    'normal_path': str(normal_path), 'fbx_path': str(fbx_path)}
    except Exception:
        if normal_node is not None:
            mat.node_tree.nodes.remove(normal_node)
        image.filepath_raw, image.file_format = image_state
        # Keep generated files as failure evidence, not accepted outputs.
        raise
