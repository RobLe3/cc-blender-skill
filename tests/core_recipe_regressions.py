"""Deterministic recipe checks and six small scene-class fixtures inside Blender.

Call run_suite(source_root, output_dir) through either MCP's execute_blender_code.
These execute recipes, not natural-language skill selection or aesthetic grading.
"""
import json
import math
from pathlib import Path
import re
import struct


def recipe(root, skill, number):
    text = (Path(root) / 'plugin/skills' / skill / 'SKILL.md').read_text()
    section = text.split('### Recipe ' + str(number) + ' —', 1)[1].split('\n### ', 1)[0]
    return re.search(r'```python\n(.*?)```', section, re.S).group(1)


def run_suite(source_root, output_dir):
    import bpy
    from mathutils import Vector
    root, out = Path(source_root), Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    fixtures = {}
    def clear():
        if bpy.context.object and bpy.context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        for obj in list(bpy.data.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        for collection in [bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights, bpy.data.actions]:
            for block in list(collection):
                if block.users == 0:
                    collection.remove(block)
        bpy.context.scene.frame_set(1)
    def cube(name='GEO-target', location=(0, 0, 0), scale=(1, 1, 1)):
        bpy.ops.mesh.primitive_cube_add(location=location)
        obj = bpy.context.object
        obj.name = name
        obj.scale = scale
        return obj
    def execute(skill, n, substitutions=None):
        code = recipe(root, skill, n)
        for a, b in (substitutions or {}).items():
            code = code.replace(a, b)
        exec(code, {})
    def check(label, fn):
        try:
            value = fn()
            rows.append({'id': label, 'status': 'PASS', 'evidence': value})
        except Exception as error:
            rows.append({'id': label, 'status': 'FAIL', 'error': type(error).__name__ + ': ' + str(error)})
    def require(value, message):
        if not value:
            raise AssertionError(message)
    def modeling(n):
        clear()
        if n in [1, 2, 4]:
            execute('blender-modeling', 1)
            if n != 1: execute('blender-modeling', n)
            obj = bpy.data.objects['GEO-base_box']
        elif n == 5:
            obj = cube('GEO-character_half')
            execute('blender-modeling', 5)
        else:
            curve = bpy.data.curves.new('curve', 'CURVE')
            curve.dimensions = '3D'
            spline = curve.splines.new('BEZIER'); spline.bezier_points.add(1)
            spline.bezier_points[1].co = (1, 0, 0); curve.bevel_depth = 0.02
            obj = bpy.data.objects.new('GEO-target', curve); bpy.context.collection.objects.link(obj)
            obj.select_set(True); bpy.context.view_layer.objects.active = obj
            bpy.ops.object.convert(target='MESH')
        require(obj.type == 'MESH' and len(obj.data.vertices) > 0, 'No geometry')
        if n == 2: require([m.type for m in obj.modifiers] == ['BEVEL','SUBSURF'], 'Modifier ordering')
        if n == 4: require(len(obj.data.vertices) != 8, 'Boolean did not cut')
        if n == 5: require(obj.modifiers[0].type == 'MIRROR', 'Missing mirror')
        return {'vertices': len(obj.data.vertices), 'modifiers': [m.type for m in obj.modifiers]}
    for label, n in [('A1',1),('A2',2),('A3',4),('A4',5),('A5',0)]: check(label, lambda n=n:modeling(n))
    def material(n, key, expected):
        clear(); obj = cube(); execute('blender-materials', n)
        mat = obj.data.materials[0]; nodes = mat.node_tree.nodes
        if key:
            value = next(i.default_value for i in nodes['Principled BSDF'].inputs if i.name == key)
            require(abs(value-expected)<1e-6, 'Wrong shader parameter')
        else: require(all(any(node.bl_idname == x for node in nodes) for x in ['ShaderNodeTexWave','ShaderNodeTexNoise','ShaderNodeValToRGB']), 'Missing wood nodes')
        return {'nodes': sorted(node.bl_idname for node in nodes)}
    for label,n,key,value in [('B1',1,'Metallic',1),('B2',5,'Transmission Weight',1),('B3',9,'Subsurface Weight',1),('B4',10,'Sheen Weight',0.5),('B5',12,None,None)]:
        check(label,lambda n=n,key=key,value=value:material(n,key,value))
    def lighting(n):
        clear();cube()
        if n=='0a':
            exec(recipe(root,'blender-lighting',n)+"\napply_three_point('metal')",{})
            energies=[bpy.data.objects['LGT-'+x].data.energy for x in ['key','fill','rim']]
            require(abs(energies[0]/energies[1]-4)<1e-6 and abs(energies[2]/energies[1]-2)<1e-6,'Lighting ratios')
        elif n==2:
            image=bpy.data.images.new('HDR-test',width=4,height=2,float_buffer=True)
            image.filepath_raw=str(out/'fixture.hdr');image.file_format='HDR';image.save()
            execute('blender-lighting',n,{'/path/to/your.hdr':str(out/'fixture.hdr')})
            require(any(node.type=='TEX_ENVIRONMENT' and node.image for node in bpy.context.scene.world.node_tree.nodes),'Missing HDRI')
        else:
            execute('blender-lighting',n);require(bpy.data.objects['LGT-sun'].data.energy==5,'Sun energy')
        return {'lights': sorted(o.data.type for o in bpy.context.scene.objects if o.type=='LIGHT')}
    for label,n in [('C1','0a'),('C2',2),('C3',3)]:check(label,lambda n=n:lighting(n))
    def camera(n):
        clear();cube('GEO-subject');execute('blender-cameras',n)
        cam=bpy.context.scene.camera
        if n==1:require(cam.data.lens==85 and abs(cam.data.dof.aperture_fstop-2.8)<1e-6,'Hero camera')
        if n==2:require(cam.data.lens==24,'Wide camera')
        evidence={'lens':cam.data.lens,'objects':sorted(o.type for o in bpy.context.scene.objects)}
        if n==5:
            pivot=bpy.data.objects['Empty-orbit_pivot']
            action=pivot.animation_data.action if pivot.animation_data else None
            require(action is not None,'Orbit pivot has no action')
            if hasattr(action,'fcurves'):
                curves=list(action.fcurves)
            else:
                curves=[fc for layer in action.layers for strip in layer.strips
                        if hasattr(strip,'channelbags') for bag in strip.channelbags
                        for fc in bag.fcurves]
            require(curves and sum(len(fc.keyframe_points) for fc in curves)>=2,'Orbit keyframes missing')
            require(all(kp.interpolation=='LINEAR' for fc in curves for kp in fc.keyframe_points),
                    'Orbit interpolation is not linear')
            evidence['orbit_fcurves']=len(curves)
        return evidence
    for label,n in [('D1',1),('D2',2),('D3',5)]:check(label,lambda n=n:camera(n))
    def configure_render(n):
        execute('blender-rendering',n)
        engine=bpy.context.scene.render.engine
        require(engine in {'BLENDER_EEVEE','BLENDER_EEVEE_NEXT','CYCLES'},'Unsupported render engine')
        return {'engine':engine,'samples':bpy.context.scene.cycles.samples}
    check('E1',lambda:configure_render(1));check('E2',lambda:configure_render(3))
    def render_fixture(path):
        scene=bpy.context.scene
        scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=4
        scene.cycles.use_denoising=False;scene.cycles.seed=0
        scene.render.resolution_x=192;scene.render.resolution_y=192;scene.render.resolution_percentage=100
        scene.render.image_settings.file_format='PNG';scene.render.filepath=str(path)
        bpy.context.view_layer.update()
        bpy.ops.render.render(write_still=True)
        require(path.stat().st_size>1000,'Empty render')
        return {'bytes':path.stat().st_size}
    def still():
        clear();cube('GEO-subject');execute('blender-cameras',1);execute('blender-lighting',3)
        return render_fixture(out/'core-still.png')
    check('E3',still)
    def animation(n):
        clear();obj=cube('GEO-character_face' if n==5 else 'GEO-target');execute('blender-animation',n)
        if n==3:
            execute('blender-animation',1);execute('blender-animation',3)
        action=obj.animation_data.action if obj.animation_data else None
        if n in [1,2,3]: require(action is not None,'Missing action')
        return {'action':bool(action),'shape_keys':bool(obj.data.shape_keys)}
    for label,n in [('F1',1),('F2',2),('F3',5)]:check(label,lambda n=n:animation(n))
    def export(n):
        clear();obj=cube();execute('blender-animation',1)
        ext={1:'glb',3:'fbx',4:'obj'}[n];path=out/('core.'+ext)
        execute('blender-export',n,{'/tmp/output.'+ext:str(path)})
        require(path.is_file() and path.stat().st_size>0,'Missing export')
        if ext=='glb':
            data=path.read_bytes();require(data[:4]==b'glTF','Wrong GLB header')
            length=struct.unpack_from('<I',data,12)[0];g=json.loads(data[20:20+length]);require(g.get('animations'),'Missing exported animation')
        if ext=='fbx':
            bpy.ops.object.select_all(action='DESELECT');bpy.ops.import_scene.fbx(filepath=str(path));require(bpy.context.selected_objects,'Empty FBX re-import')
        if ext=='obj':require(path.with_suffix('.mtl').exists(),'Missing MTL')
        return {'bytes':path.stat().st_size}
    for label,n in [('G1',1),('G2',3),('G3',4)]:check(label,lambda n=n:export(n))
    def decimate():
        clear();sentinel=cube('GEO-sentinel',(3,0,0));bpy.ops.mesh.primitive_uv_sphere_add();obj=bpy.context.object;obj.name='GEO-target'
        original_path=out/'original.glb'
        bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
        bpy.ops.export_scene.gltf(filepath=str(original_path),export_format='GLB',use_selection=True)
        sentinel.select_set(True);bpy.context.view_layer.objects.active=obj;bpy.ops.object.mode_set(mode='EDIT')
        selected_names=sorted(item.name for item in bpy.context.selected_objects);active_name=obj.name
        count=len(obj.data.polygons);vertices_before=len(obj.data.vertices)
        execute('blender-export',2);reduced=len(obj.data.polygons);vertices_reduced=len(obj.data.vertices)
        require(reduced<count,'No decimation')
        require(bpy.context.object.mode=='EDIT','Object mode was not restored')
        require(bpy.context.view_layer.objects.active.name==active_name,'Active object was not restored')
        require(sorted(item.name for item in bpy.context.selected_objects)==selected_names,'Selection was not restored')
        bpy.ops.object.mode_set(mode='OBJECT');bpy.data.objects.remove(sentinel,do_unlink=True)
        bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
        path=out/'decimated.glb';execute('blender-export',1,{'/tmp/output.glb':str(path)})
        clear();bpy.ops.import_scene.gltf(filepath=str(path))
        imported_faces=sum(len(item.data.polygons) for item in bpy.context.selected_objects if item.type=='MESH')
        clear();bpy.ops.import_scene.gltf(filepath=str(original_path))
        original_faces=sum(len(item.data.polygons) for item in bpy.context.selected_objects if item.type=='MESH')
        require(0<imported_faces<original_faces,'Export/re-import did not preserve the reduction')
        return {'faces_before':count,'faces_after':reduced,
                'vertices_before':vertices_before,'vertices_after':vertices_reduced,
                'exported_faces_before':original_faces,'exported_faces_after':imported_faces}
    check('G4',decimate)
    # The wireframe analyzer itself runs in the host-Python fixture test.
    check('H1_curve_conversion',lambda:modeling(0))
    check('I1_render_chain',still);check('I2_animation_export_chain',lambda:export(1))
    def scene_class(kind):
        clear();parts=[]
        if kind=='sword':
            parts=[cube('GEO-blade',(0,0,0.65),(.04,.01,.5)),cube('GEO-guard',(0,0,.15),(.22,.04,.03)),cube('GEO-grip',(0,0,0),(.04,.04,.15))]
        elif kind=='bottle':
            for name,rad,depth,z in [('body',.13,.45,.225),('neck',.04,.2,.55)]:
                bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=rad,depth=depth,location=(0,0,z));bpy.context.object.name='GEO-'+name;parts.append(bpy.context.object)
        elif kind=='chair':
            parts=[cube('GEO-seat',(0,0,.45),(.225,.225,.02)),cube('GEO-back',(0,.2,.7),(.225,.02,.25))]
            parts += [cube('GEO-leg-'+str(i),(x,y,.225),(.025,.025,.225)) for i,(x,y) in enumerate([(-.18,-.18),(-.18,.18),(.18,-.18),(.18,.18)])]
        elif kind=='aviator':
            for x in [-.2,.2]:
                bpy.ops.mesh.primitive_torus_add(major_segments=32,minor_segments=8,location=(x,0,.3),rotation=(math.pi/2,0,0),major_radius=.17,minor_radius=.012);bpy.context.object.name='GEO-frame-'+str(x);parts.append(bpy.context.object)
            parts.append(cube('GEO-bridge',(0,0,.35),(.08,.015,.015)))
        elif kind=='desk_lamp':
            parts=[cube('GEO-base',(0,0,.03),(.2,.2,.03)),cube('GEO-stem',(0,0,.4),(.025,.025,.4))]
            bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=.1,location=(0,0,.8));bpy.context.object.name='GEO-bulb';parts.append(bpy.context.object);execute('blender-materials','11b')
        else:
            bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=.2,location=(0,0,.7));bpy.context.object.name='GEO-head';parts=[bpy.context.object,cube('GEO-torso',(0,0,.3),(.25,.12,.25)),cube('GEO-mic',(.35,-.1,.5),(.04,.04,.15))]
        for obj in parts:
            if obj.name=='GEO-bulb':continue
            execute('blender-materials',5 if kind=='bottle' else 12 if kind=='chair' else 1,{'GEO-target':obj.name})
        bpy.context.view_layer.update()
        exec(recipe(root,'blender-lighting','0a')+"\napply_three_point("+repr('glass' if kind=='bottle' else 'wood' if kind=='chair' else 'metal')+")",{})
        scene=bpy.context.scene
        world=scene.world;world.use_nodes=True;world.node_tree.nodes.clear()
        bg=world.node_tree.nodes.new('ShaderNodeBackground');bg.inputs['Color'].default_value=(.04,.04,.05,1)
        output=world.node_tree.nodes.new('ShaderNodeOutputWorld');world.node_tree.links.new(bg.outputs['Background'],output.inputs['Surface'])
        cam_data=bpy.data.cameras.new('CAM-fixture');cam=bpy.data.objects.new('CAM-fixture',cam_data);bpy.context.collection.objects.link(cam);scene.camera=cam
        cam.location=(2,-3,1.8);cam.rotation_euler=(Vector((0,0,.45))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=1.65
        data={'meshes':len(parts),'vertices':sum(len(o.data.vertices) for o in parts),'faces':sum(len(o.data.polygons) for o in parts),'lights':len([o for o in scene.objects if o.type=='LIGHT'])}
        render_fixture(out/(kind+'.png'));fixtures[kind]=data
        return data
    for kind in ['sword','bottle','chair','aviator','desk_lamp','broadcaster_avatar']:
        check('scene_'+kind,lambda kind=kind:scene_class(kind))
    report={'source_root':str(root),'blender_version':bpy.app.version_string,'tests':rows,'fixtures':fixtures,
            'limitations':['Deterministic recipe execution, not natural-language skill loading.','Small representative fixtures, not reproductions of historical artist-authored validation scenes.']}
    (out/'core-tests.json').write_text(json.dumps(report,indent=2))
    return report
