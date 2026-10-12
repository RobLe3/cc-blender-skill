# Contributing to cc-blender-skill

Thanks for considering a contribution. This is a small project; the workflow below keeps the bar honest and low-friction.

## Bug reports

Open a GitHub issue using the **Bug** template. Include:

- Your Blender version (`bpy.app.version_string`) and OS
- Your agent/client and version (for example, Claude Code or Codex)
- The selected MCP backend plus add-on/server versions
- Whether the skill was discovered automatically or invoked explicitly
- Whether it was installed at personal or project scope
- The exact prompt you sent + the skill that triggered (or didn't)
- Whether the failure was numerical (Python error, file not created) or visual (render looks wrong)
- For visual bugs: attach the rendered output
- Sanitized logs or traces, with credentials, private paths, and proprietary data removed

The validation pattern documented in [`docs/test-results/`](../docs/test-results/) shows how the project's tester→patcher loop works. Bug reports that follow that pattern get acted on faster.

### v1.4.0 feedback priorities

The repository has Blender 5.1.1 coverage through both supported MCP backends and
bounded native Codex workflow evidence. The highest-value remaining reports are:

- Claude Code skill discovery, implicit routing, and explicit invocation
- Queries from the 225-case trigger set or ten backend scenarios that misroute
- Unreal Engine imports of collision FBX or Multires cage-normal output
- Blender 4.x or post-5.1 compatibility results
- Legacy provider download/generation behavior

Successful runs are useful too. State exactly what you exercised so the result is
not mistaken for broader coverage.

## Feature requests

Open a GitHub issue using the **Feature** template. Useful new content:

- New scene-class validation (e.g. character, vehicle, kitchen) — surfaces recipe gaps
- New material recipe (e.g. Neon glow, anodized aluminum) — extends `blender-materials`
- New dimension reference for a common subject — extends `references/common-object-dimensions.md`
- Cross-version compat report from a Blender 4.x install
- Trigger-eval queries that surfaced real false-positive / false-negative behaviour

## Pull requests

Welcome but not required. If you do open one:

- Branch from `main`
- Keep the change scoped to a single concern
- Update [`CHANGELOG.md`](../CHANGELOG.md) with the version it lands in
- If the change affects skill behaviour, add an `evals/evals.json` entry covering the new trigger / no-trigger boundary
- For a Claude Code routing fix, include the failing prompt, expected skill/backend,
  observed trace, and a regression eval when one can represent the boundary
- If the change adds a new scene class, add the proof render to `plugin/skills/text-to-blender/assets/v<version>-validation/` — including failure-state renders if the path was non-trivial. Honest validation > cherry-picked best result.

## Honesty principle

Every version of this project so far has shipped with explicit "what doesn't work" documentation. Maintain that. If a change has trade-offs or known limits, surface them in the PR description and the relevant skill's failure-modes table.

## Versioning

[Semantic Versioning](https://semver.org/). Pre-1.0 (unstable) was through v0.9.x; v1.x is the stable line. Breaking changes warrant a major bump; recipe additions are minor; doc-only fixes are patch.

## License

By contributing, you agree your contribution is licensed under the project's [MIT license](../LICENSE).
