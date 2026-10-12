# v1.4.0 representative fixture renders

All six official-MCP fixture renders from the Blender 5.1.1 comparison are included.
They are small deterministic test subjects, not finished artistic deliverables or
reproductions of the older scene proofs. Their purpose is to compare geometry,
materials, lighting, and saved output across unchanged baseline recipes and both
backends. Four samples without denoising intentionally expose noise.

The baseline repeat showed emission-lamp sampling variation also present in the
legacy candidate. Every candidate fixture matched either the baseline or its
repeatability control. There were three non-render baseline recipe failures;
see the integration report rather than interpreting these images as universal
correctness evidence. GUI and raw runtime traces remain temporary test artifacts.
