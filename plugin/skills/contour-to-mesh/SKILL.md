---
name: contour-to-mesh
description: Build Blender mesh surfaces directly from extracted 2D contours/masks instead of approximate primitives. Use for 1:1 mascot/logo reconstruction, exact leaf/petal silhouettes, filled wireframe shapes, shallow bas-relief forms, or when the model outline must match a front template before adding depth.
when_to_use: Source-locked contour-derived meshes, silhouette-first modeling, triangulated mask/contour surfaces, mesh generation from OpenCV contours, or replacing generic ellipses/primitives with measured shapes.
allowed-tools: Read Bash Glob Grep mcp__blender__execute_blender_code mcp__blender__get_scene_info mcp__blender__get_object_info
---

# Contour to Mesh

Use this when a reference silhouette is the contract. The mesh starts as a filled 2D contour in front-view X/Z, then gets shallow Y depth/crown after validation.

## Workflow

1. Extract or select a clean contour/mask for one structural part.
2. Generate a triangulated mesh recipe with `scripts/mask_to_mesh_recipe.py`.
3. Run the generated Blender Python to create a named `GEO_*` mesh.
4. Assign front-projected UVs immediately.
5. Add depth only as a modifier or vertex displacement that preserves X/Z boundary positions.
6. Validate the front render against the source mask.

## Hard rules

- Do not use radial duplication unless the manifest says the source is symmetric.
- Do not use a generic ellipse if a contour exists.
- Boundary vertices must keep source X/Z coordinates.
- Depth deformation may move Y and inner vertices, but must not alter front silhouette.
- One structural source part should become one named structural mesh.

## Blender pattern

Generated mesh coordinates should map image `x` to Blender `X` and image `y` to Blender `Z` with vertical flip. Use `Y` only for thickness/depth.


## Front-plane rotation rule

In this Blender coordinate convention, the front camera looks along the Y axis and the reference silhouette lives in the X/Z plane. Therefore 2D rotations inside the front view are rotations around the **Y axis**, not around Z. Use `rotation_euler = (0, angle, 0)` for 2D component orientation in the front projection. Z rotation spins objects into/out of screen-space incorrectly for X/Z-plane meshes.

## Sources distilled

- Blender Mesh API: create meshes from vertices/faces using `from_pydata`.
- Blender BMesh: use for cleanup, triangulation, normals, smoothing.
- OpenCV contours: detect and simplify boundaries.
- Delaunay triangulation: useful for filled interior meshes when filtered by mask containment.
