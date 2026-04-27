# Trigger-Eval Files — How to Use

Each skill in this plugin ships with a starter `evals/evals.json` containing 10 trigger queries (should activate the skill) + 10 no-trigger queries (should NOT activate it). These are sized for a quick description-quality check, not exhaustive coverage.

Per Anthropic's skill-authoring best practices: skill descriptions are the **primary triggering mechanism**. Bad descriptions → Claude misses skill invocations OR over-triggers on adjacent prompts. The evals files let you measure both failure modes.

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
2. **Read each query** and **mentally check** whether Claude's description for that skill would cause it to load.
3. **Score**: count true positives (trigger queries that activate), false negatives (trigger queries that don't), false positives (no-trigger queries that wrongly activate), true negatives (no-trigger queries correctly skipped).
4. **If false-negative rate > 20%**: description is under-triggering. Make it more "pushy" (Anthropic's term) — add explicit example phrases users might say.
5. **If false-positive rate > 10%**: description is over-triggering. Tighten with disambiguating phrases ("ONLY for Blender 3D work, NOT for general Python coding").

## Pairing with claude `--print` for actual verification

You can also automate the loop by sending each query to a fresh Claude session and inspecting whether it loaded the skill. Sketch:

```bash
for query in $(jq -r '.[].query' plugin/skills/text-to-blender/evals/evals.json); do
    echo "=== $query ==="
    claude --print "$query" 2>&1 | grep -E "(loaded.*skill|Reading.*SKILL\.md)" | head -3
done
```

(Requires Claude CLI in `--print` mode + a way to introspect skill loading. Out of scope for this plugin — left to the operator.)

## Honest caveats

- These are **starter sets** (10/10), not the recommended 20/20. Adequate for pre-v1.0 checks, not for production-grade trigger tuning.
- Queries are written in English only.
- Several no-trigger queries are *adjacent* (e.g. lighting on the modeling skill's no-trigger list) — these test whether Claude correctly routes to the right skill within the plugin, not just whether the plugin activates at all.
- Borderline cases are marked with rationale notes (e.g. "vectorize this raster image to SVG" for `wireframe-to-3d` — could go either way).

## When to update an evals file

- After changing a skill's `description` or `when_to_use` frontmatter
- After patching a skill that turned out to over- or under-trigger in real use
- When adding new trigger phrases users actually said

Per Anthropic: descriptions should be tuned via this loop rather than written once and shipped.
