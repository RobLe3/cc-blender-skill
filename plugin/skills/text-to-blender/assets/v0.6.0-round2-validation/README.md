# Round 2 Validation Renders — Sword Scene Iterations

Three renders showing how the skill recipes performed on a real multi-part scene-build. Iteration 1 used the recipes verbatim; iterations 2 and 3 applied progressive workarounds that revealed where the recipes have gaps.

| File | Recipe state | Outcome | What it reveals |
|------|-------------|---------|-----------------|
| `M_sword_attempt1_broken_world.png` | Recipes verbatim | Magenta dominates; sword barely visible | The world tree from a previous test (C2 HDRI placeholder) was still in place. **Recipes don't reset world state before composition.** |
| `M_sword_attempt2_clean_world.png` | After manual world reset | Clean dark BG; sword mostly in shadow | Lighting recipe places lights at fixed world coords with hardcoded rotations. **Lighting recipe lacks subject-awareness.** |
| `M_sword_attempt3_aimed_lights.png` | + aimed lights + reframed camera | Sword parts clearly readable; blade clips top | **Camera recipe lacks bounding-box-based framing logic.** |

See `test_round2.md` at repo root for the full investigation, root causes, and patch suggestions for Opus.

The renders are committed as honest proof of the skill's current state — these are NOT cherry-picked. They're the actual three iterations a tester needed to drag a recipe-driven scene build from "totally broken" to "credible but rough."
