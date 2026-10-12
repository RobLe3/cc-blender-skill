# Integration checks

Use a disposable workspace and Blender process. These checks execute recipes and
inspect artifacts; they do not establish natural-language skill selection.

## Local structural, source, and Blender export checks

```bash
RUN=$(mktemp -d)
mkdir "$RUN/baseline"
git archive 11016c9 | tar -x -C "$RUN/baseline"
CC_BLENDER_BASELINE="$RUN/baseline" python3 -m unittest discover -s tests -p 'test_*.py' -v
# Set BLENDER_BIN to the Blender executable for your platform.
CC_BLENDER_TEST_OUT="$RUN/export" "$BLENDER_BIN" --background --factory-startup \
  --python-exit-code 1 --python tests/blender_export_regressions.py
```

Use a new output directory for each run: the export helpers intentionally reject
existing output files. Host source-fixture tests need the image-processing packages
in `requirements.txt`; missing packages are skips, not proof of a passing release.
The static preservation test compares all original Python recipe blocks and existing
references/scripts/assets to the extracted baseline, except for the three approved
compatibility repairs: camera orbit F-curves, guarded EEVEE settings, and decimation
context/API handling.

## Actual MCP connections and GUI capture

Install each upstream server into its own temporary Python environment. Supply the
actual source of the legacy add-on and the official add-on (tested: official 1.0.3),
and absolute paths to their server Python executables. No personal MCP settings are
changed. A separate factory-startup Blender GUI instance provides both real bridges
on automatically selected private ports; never attach this test to a working scene.

```bash
# In a separate terminal; CC_MCP_PURE_PYTHON_SITE may supply pure-Python requests dependencies.
CC_MCP_INSTANCE_OUT="$RUN/instance" CC_LEGACY_ADDON="$LEGACY_ADDON_FILE" \
  CC_OFFICIAL_ADDON="$OFFICIAL_ADDON_DIR" BLENDER_USER_CONFIG="$RUN/blender-config" \
  "$BLENDER_BIN" --factory-startup --python-exit-code 1 --python tests/mcp_test_instance.py

# In a Python environment containing the MCP SDK:
python tests/mcp_recipe_regressions.py --instance "$RUN/instance" --out "$RUN/mcp" \
  --repo "$PWD" --baseline "$RUN/baseline" \
  --legacy-python "$LEGACY_SERVER_PYTHON" --official-python "$OFFICIAL_SERVER_PYTHON"
python3 tests/compare_mcp_regressions.py --runs "$RUN/mcp" --out "$RUN/comparison.json"
```

The MCP runner disables legacy telemetry and isolates its client data directory.
Close only the dedicated test Blender instance afterward; its PID is recorded in
`instance/instance.json`. Raw traces and screenshots stay in the temporary output,
not in the public repository.

The suite runs the same 35 checks on legacy baseline, legacy candidate, official
candidate, and a repeated baseline. A regression is a new failing check, missing
case, different fixture geometry/statistics, or a render that matches neither the
baseline nor its repeatability control. Baseline defects remain visible. The six
small scene fixtures exercise metal/glass/wood/emission/avatar/eyewear classes; they
are not recreations of the historical artist-authored scenes or aesthetic reviews.

## Required agent-behavior gate

Run all 225 `evals.json` queries and the ten backend scenarios using actual Codex
and Claude Code skill/tool traces, with matching baseline/candidate client and model
settings for each host.
Preserve the 220 existing classifications; evaluate the five added export queries
against their labels. For backend scenarios, provide the specified tool inventory
and verify actual selected backend, calls, and stopping behavior. No new misrouting
of baseline queries is allowed. Test explicit choice, provider requirements,
unreachable connections, ambiguous scenes, timeout recovery, and nested errors.

Codex is available in the implementation environment; Claude Code is not. Native
Codex checks therefore provide partial evidence, while the two-client matrix remains
**incomplete** until both clients have captured traces. Structural checks and model
self-reports do not simulate a pass. The JSON comparison reports this as an
agent-behavior gap separately from runtime regressions. Its zero exit code means the
runtime comparison passed, not that the unexecuted client matrix was completed.

Unreal imports and new Blender 4.x/5.2 live validation remain separate evidence;
Unreal acceptance is required before engine-side validation claims, not for merge.
