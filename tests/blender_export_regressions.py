"""Run with Blender --background --factory-startup --python <this file>."""
import bmesh
import bpy
import importlib.util
import json
import math
import os
from pathlib import Path
import runpy
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('CC_BLENDER_TEST_OUT', tempfile.mkdtemp(prefix='blender-export-tests-')))
OUT.mkdir(parents=True, exist_ok=True)


def module(name):
    path = ROOT / 'plugin/skills/blender-export/scripts' / (name + '.py')
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


collision = module('collision_preflight')
bake = module('multires_bake_export')


def cube(name='GEO-target'):
    bpy.ops.mesh.primitive_cube_add()
    obj = bpy.context.object
    obj.name = name
    return obj


def edit(obj, operation):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    operation(bm)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


class Exports(unittest.TestCase):
    def setUp(self):
        if bpy.context.object and bpy.context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)

    def test_closed_convex_and_scale(self):
        obj = cube('UCX_SM_Prop_01')
        for scale in [1e-3, 1, 1e3]:
            obj.scale = (scale,) * 3
            bpy.context.view_layer.update()
            self.assertTrue(collision.validate_collider(obj)['passed'])

    def test_open_empty_inward_and_concave_rejected(self):
        for case in ['open', 'empty', 'inward', 'concave']:
            self.setUp()
            obj = cube('UCX_SM_Prop_01')
            if case == 'open':
                edit(obj, lambda bm: bmesh.ops.delete(bm, geom=[bm.faces[0]], context='FACES'))
            elif case == 'empty':
                obj.data.clear_geometry()
            elif case == 'inward':
                edit(obj, lambda bm: bmesh.ops.reverse_faces(bm, faces=list(bm.faces)))
            else:
                edit(obj, lambda bm: setattr(bm.verts[0], 'co', (0, 0, 0)))
            self.assertFalse(collision.validate_collider(obj)['passed'], case)

    def test_evaluated_modifier_concavity(self):
        obj = cube('UCX_SM_Prop_01')
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.75))
        cutter = bpy.context.object
        cutter.hide_render = True
        mod = obj.modifiers.new('cut', 'BOOLEAN')
        mod.operation = 'DIFFERENCE'
        mod.object = cutter
        self.assertFalse(collision.validate_collider(obj)['passed'])
        self.assertEqual(len(obj.data.polygons), 6, 'Preflight must not apply the modifier')

    def test_names_and_missing_colliders(self):
        mesh = cube('SM_Prop')
        obj = cube('UCX_wrong_01')
        self.assertFalse(collision.collision_report(mesh, [obj])['passed'])
        self.assertFalse(collision.collision_report(mesh, [])['passed'])
        obj.name = 'UCX_SM_Prop_01'
        self.assertTrue(collision.collision_report(mesh, [obj])['passed'])

    def test_primitive_constraints(self):
        box = cube('UBX_SM_Prop_01')
        self.assertTrue(collision.validate_collider(box)['passed'])
        edit(box, lambda bm: setattr(bm.verts[0].co, 'x', -0.75))
        self.assertFalse(collision.validate_collider(box)['passed'])
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8)
        sphere = bpy.context.object
        sphere.name = 'USP_SM_Prop_01'
        self.assertTrue(collision.validate_collider(sphere)['passed'])
        sphere.scale = (2, 1, 1)
        bpy.context.view_layer.update()
        self.assertFalse(collision.validate_collider(sphere)['passed'])
        bpy.ops.mesh.primitive_cylinder_add(vertices=16)
        cylinder = bpy.context.object
        cylinder.name = 'UCP_SM_Prop_01'
        self.assertFalse(collision.validate_collider(cylinder)['passed'])
        # Stretch a sphere's two hemispheres apart, keeping an equatorial cylinder.
        sphere.scale = (1, 1, 1)
        sphere.name = 'UCP_SM_Prop_02'
        for v in sphere.data.vertices:
            v.co.z += 0.5 if v.co.z >= 0 else -0.5
        sphere.data.update()
        bpy.context.view_layer.update()
        self.assertTrue(collision.validate_collider(sphere)['passed'])

    def test_collision_export_scope_and_selection(self):
        mesh = cube('SM_Prop')
        collider = cube('UCX_SM_Prop_01')
        other = cube('GEO-other')
        selected = {o.name for o in bpy.context.selected_objects}
        active = bpy.context.object.name
        path = OUT / 'collision.fbx'
        collision.export_collision_fbx(mesh, [collider], path)
        self.assertEqual({o.name for o in bpy.context.selected_objects}, selected)
        self.assertEqual(bpy.context.object.name, active)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.import_scene.fbx(filepath=str(path))
        self.assertEqual(len(bpy.context.selected_objects), 2)
        self.assertTrue(all(not o.name.startswith('GEO-other') for o in bpy.context.selected_objects))
        with self.assertRaises(FileExistsError):
            collision.export_collision_fbx(mesh, [collider], path)

    def setup_bake(self):
        obj = cube()
        mat = bpy.data.materials.new('MAT-bake')
        mat.use_nodes = True
        obj.data.materials.append(mat)
        image = bpy.data.images.new('N-test', width=32, height=32)
        image.colorspace_settings.name = 'Non-Color'
        node = mat.node_tree.nodes.new('ShaderNodeTexImage')
        node.image = image
        mat.node_tree.nodes.active = node
        mod = obj.modifiers.new('Multires', 'MULTIRES')
        for _ in range(2):
            bpy.ops.object.multires_subdivide(modifier=mod.name)
        mod.levels = 1
        mod.render_levels = 1
        bpy.context.scene.render.engine = 'BLENDER_EEVEE'
        return obj, mod, image

    def state(self):
        r = bpy.context.scene.render
        return {'selected': sorted(o.name for o in bpy.context.selected_objects),
                'active': bpy.context.object.name if bpy.context.object else None,
                'mode': bpy.context.object.mode if bpy.context.object else None,
                'engine': r.engine, 'use_multires': r.bake.use_multires,
                'type': r.bake.type, 'margin': r.bake.margin}

    def test_bake_cage_success_and_state_restoration(self):
        obj, mod, image = self.setup_bake()
        other = cube('GEO-other')
        obj.select_set(True)
        before = self.state()
        result = bake.bake_export_cage(obj, OUT / 'normal.png', OUT / 'cage.fbx')
        self.assertEqual(result['bake_level'], 0)
        self.assertEqual(result['export_level'], 0)
        self.assertEqual((mod.levels, mod.render_levels), (1, 1))
        self.assertEqual(self.state(), before)
        self.assertTrue(obj.data.materials[0].node_tree.nodes['Principled BSDF'].inputs['Normal'].is_linked)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.import_scene.fbx(filepath=str(OUT / 'cage.fbx'))
        self.assertEqual(len(bpy.context.selected_objects), 1)
        self.assertEqual(len(bpy.context.selected_objects[0].data.polygons), 6)
        self.assertGreater(max(image.pixels[:]), 0)

    def test_bake_failure_restores_edit_context_and_material(self):
        obj, mod, image = self.setup_bake()
        bpy.ops.object.mode_set(mode='EDIT')
        before = self.state()
        def failing_export(path):
            self.assertEqual(mod.levels, 0)
            self.assertEqual([o.name for o in bpy.context.selected_objects], [obj.name])
            raise RuntimeError('intentional exporter failure')
        with self.assertRaisesRegex(RuntimeError, 'intentional exporter failure'):
            bake.bake_export_cage(obj, OUT / 'failed-normal.png', OUT / 'failed.fbx', failing_export)
        self.assertEqual(self.state(), before)
        self.assertEqual((mod.levels, mod.render_levels), (1, 1))
        self.assertFalse(obj.data.materials[0].node_tree.nodes['Principled BSDF'].inputs['Normal'].is_linked)
        self.assertEqual(image.filepath_raw, '')
        self.assertTrue((OUT / 'failed-normal.png').is_file(), 'Keep failed output as evidence')

    def test_bake_guards(self):
        obj, mod, image = self.setup_bake()
        before = self.state()
        obj.modifiers.new('Smooth', 'SMOOTH')
        with self.assertRaisesRegex(ValueError, 'last'):
            bake.bake_export_cage(obj, OUT / 'guard.png', OUT / 'guard.fbx')
        obj.modifiers.remove(obj.modifiers[-1])
        obj.data.uv_layers.remove(obj.data.uv_layers[0])
        with self.assertRaisesRegex(ValueError, 'UV'):
            bake.bake_export_cage(obj, OUT / 'guard.png', OUT / 'guard.fbx')
        self.assertEqual(self.state(), before)

    def test_bake_with_collision_callback(self):
        obj, mod, image = self.setup_bake()
        collider = cube('UCX_GEO-target_01')
        before = self.state()
        bake.bake_export_cage(obj, OUT / 'combined-normal.png', OUT / 'combined.fbx',
                             lambda path: collision.export_collision_fbx(obj, [collider], path))
        self.assertEqual(self.state(), before)
        self.assertEqual(mod.levels, 1)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.import_scene.fbx(filepath=str(OUT / 'combined.fbx'))
        self.assertEqual(len(bpy.context.selected_objects), 2)
        self.assertTrue(all(len(o.data.polygons) == 6 for o in bpy.context.selected_objects))

    def test_bake_rejects_shared_material_without_mutation(self):
        obj, mod, image = self.setup_bake()
        other = cube('GEO-other')
        other.data.materials.append(obj.data.materials[0])
        before = self.state()
        with self.assertRaisesRegex(ValueError, 'single-user'):
            bake.bake_export_cage(obj, OUT / 'shared.png', OUT / 'shared.fbx')
        self.assertEqual(self.state(), before)
        self.assertFalse((OUT / 'shared.png').exists())

    def test_reference_uv_coverage_and_export(self):
        obj = cube('GEO-reference')
        mat = bpy.data.materials.new('MAT-reference')
        mat.use_nodes = True
        obj.data.materials.append(mat)
        texture = mat.node_tree.nodes.new('ShaderNodeTexImage')
        texture.image = bpy.data.images.new('atlas-fixture', width=4, height=4)
        texture.image.pixels[:] = [1.0, 0.5, 0.2, 1.0] * 16
        mat.node_tree.links.new(texture.outputs['Color'], mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
        helper = runpy.run_path(str(ROOT / 'plugin/skills/closed-surface-uv-coverage/scripts/surface_texture_coverage_audit.py'))
        self.assertFalse(helper['audit_object'](obj)['warnings'])
        self.assertEqual(len(obj.data.polygons), 6)
        for poly in obj.data.polygons:
            uvs = [obj.data.uv_layers.active.data[i].uv[:] for i in poly.loop_indices]
            self.assertGreater(max(u[0] for u in uvs) - min(u[0] for u in uvs), 0)
            self.assertGreater(max(u[1] for u in uvs) - min(u[1] for u in uvs), 0)
        result = bpy.ops.export_scene.gltf(filepath=str(OUT / 'reference.glb'), export_format='GLB')
        self.assertIn('FINISHED', result)
        self.assertTrue((OUT / 'reference.glb').is_file())
        obj.data.uv_layers.remove(obj.data.uv_layers.active)
        self.assertIn('Mesh has no UV layers.', helper['audit_object'](obj)['warnings'])


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Exports))
    report = {'blender_version': bpy.app.version_string, 'tests_run': result.testsRun,
              'failures': [(t.id(), e) for t, e in result.failures],
              'errors': [(t.id(), e) for t, e in result.errors], 'passed': result.wasSuccessful()}
    (OUT / 'export-tests.json').write_text(json.dumps(report, indent=2))
    if not result.wasSuccessful():
        raise SystemExit(1)
