# Checked static FBX export

The two new helpers are optional Blender-side functions, not MCP wrappers.
Read their source when using non-default behavior. Load them in Blender's Python
environment through the selected MCP backend, using the installed absolute paths.
They keep general Recipe 3's transform convention; they do not establish that its
`bake_space_transform=True` setting is best for every Unreal or rigged export.

## Combine a cage bake with collision export

```python
import bpy, runpy
collision = runpy.run_path('/installed/blender-export/scripts/collision_preflight.py')
bake = runpy.run_path('/installed/blender-export/scripts/multires_bake_export.py')
target = bpy.data.objects['GEO-target']
colliders = [bpy.data.objects['UCX_GEO-target_01']]
result = bake['bake_export_cage'](
    target, '/tmp/new_normal.png', '/tmp/new_asset.fbx',
    export_fbx=lambda path: collision['export_collision_fbx'](target, colliders, path))
print(result)
```

Only the target is selected while baking. The callback runs afterward, while its
viewport level is still 0; collision preflight scopes FBX selection to the target
and colliders. Both contexts then restore prior temporary state. Do not export the
restored high-resolution target against the cage's normal map.

The material must have one active Non-Color bake image, one used material slot,
and an unlinked Principled Normal input. Make the material/image single-user before
running if necessary. The new image pixels, saved path, and normal connection are
intentional outputs. On failure, the helper removes its connection and restores
temporary state; it keeps generated files for diagnosis, not as accepted assets.

## Engine-side acceptance checklist — pending validation

The naming and primitive rules follow
[Epic's FBX static mesh documentation](https://dev.epicgames.com/documentation/en-us/unreal-engine/fbx-static-mesh-pipeline-in-unreal-engine).
The helper exports one render mesh plus its colliders; Epic documents limitations
when several independently colliding render meshes share a single FBX.

Before labeling an example Unreal-validated:

1. Import into a recorded Unreal version; record custom-collision/auto-generation
   options rather than relying on defaults.
2. Inspect collision visualization and hull count. Test openings with a player or
   physics body; verify that a table/doorway's empty space remains usable.
3. Check scale/orientation and primitive restrictions, including non-uniform scale.
4. Inspect the imported normal texture and material connection. Confirm expected
   cage face count and surface detail; normal maps cannot recreate silhouette changes.
5. Save screenshots and the import settings with the example's evidence.

Blender-side export/re-import and saved files do not satisfy this checklist.
