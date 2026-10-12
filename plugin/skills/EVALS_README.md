# Trigger-Eval Files — How to Use

Each skill in this plugin ships with a starter `evals/evals.json` containing 10 trigger queries (should activate the skill) + 10 no-trigger queries (should NOT activate it). These are sized for a quick description-quality check, not exhaustive coverage.

Skill descriptions are the **primary triggering mechanism** in supported hosts. Weak descriptions make an agent miss a skill or over-trigger on adjacent prompts. The eval files measure both failure modes.

## Schema

```json
[
  { "query": "user prompt verbatim", "should_trigger": true,  "rationale": "optional one-line note" },
  { "query": "another prompt",        "should_trigger": false, "rationale": "why this should not trigger" }
]
```

- **`query`** — what a real user might type
- **`should_trigger`** — boolean ground truth
- **`rationale`** — optional, helps the patcher understand the decision boundary

## Running the evals (manual loop)

There is no automated runner shipped yet. The intended workflow is:

1. **Pick a skill** to evaluate (start with `text-to-blender` since it's the most-invoked entry point).
2. **Read each query** and make a preliminary check whether the description should cause the target agent to load it.
3. **Score**: count true positives (trigger queries that activate), false negatives (trigger queries that don't), false positives (no-trigger queries that wrongly activate), true negatives (no-trigger queries correctly skipped).
4. **If false-negative rate > 20%**: description is under-triggering. Make it more "pushy" (Anthropic's term) — add explicit example phrases users might say.
5. **If false-positive rate > 10%**: description is over-triggering. Tighten with disambiguating phrases ("ONLY for Blender 3D work, NOT for general Python coding").

## Actual verification in an agent client

Send each query to a fresh, isolated client session and inspect the client's skill and tool trace. A text-only self-assessment is not a substitute for an observed load. For example, a Claude Code harness may resemble:

```bash
for query in $(jq -r '.[].query' plugin/skills/text-to-blender/evals/evals.json); do
    echo "=== $query ==="
    claude --print "$query" 2>&1 | grep -E "(loaded.*skill|Reading.*SKILL\.md)" | head -3
done
```

Codex should be tested with the skills linked into an isolated `.agents/skills/`
directory and its structured execution trace retained. Keep client/model/tool settings
fixed between baseline and candidate runs. The repository does not claim a client
gate passed unless the native trace was captured and reviewed.

## Honest caveats

- These are **starter sets** (10/10), not the recommended 20/20. Adequate for pre-v1.0 checks, not for production-grade trigger tuning.
- Queries are written in English only.
- Several no-trigger queries are *adjacent* (e.g. lighting on the modeling skill's no-trigger list) — these test whether Claude correctly routes to the right skill within the plugin, not just whether the plugin activates at all.
- Borderline cases are marked with rationale notes (e.g. "vectorize this raster image to SVG" for `wireframe-to-3d` — could go either way).

## When to update an evals file

- After changing a skill's `description` or its body-level `Use when:` guidance
- After patching a skill that turned out to over- or under-trigger in real use
- When adding new trigger phrases users actually said

Descriptions should be tuned through observed routing, not written once and assumed correct.

## v1.4.0 backend scenarios

`text-to-blender/evals/backend-scenarios.json` is a separate scenario schema, not
`should_trigger` data. Evaluate each with its stated tool availability and inspect
actual skill/tool traces. It covers backend preference, legacy-only assets, explicit
choices, unavailable connections, timeout recovery, nested errors, and render paths.
The 220 existing trigger cases are retained; blender-export adds five from PR #2.
Compare baseline/candidate runs using the same client/model/settings. No new false
positive/negative routes are allowed. If the client or trace capture is unavailable,
mark this gate unexecuted; static JSON validation does not substitute for it.
