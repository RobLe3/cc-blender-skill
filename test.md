# Test Results

**Status**: not yet run.

When the tester (Haiku 4.5 with `mcp__blender__execute_blender_code`) starts a run, they overwrite this file with the results, following the schema in [`TESTING_PLAN.md`](./TESTING_PLAN.md).

---

## How to use this file

1. **Tester** (Haiku): replaces this file's contents with structured per-test results.
2. **Patcher** (Opus): reads the structured results and applies fixes to the affected `plugin/skills/*/SKILL.md` files.
3. After patching: a new test run starts, this file gets overwritten again.

The `test.md` is the **handoff document** between roles. Keep its schema strict.

---

## Schema reminder (full version in TESTING_PLAN.md)

```markdown
# Test Results — vX.Y.Z

**Run date**: YYYY-MM-DD
**Environment**: <Blender version, OS, mcp version, deps>
**Score**: P/F/S out of N

## Test results

### A1
- **Skill**: <name>
- **Status**: PASS | FAIL | SKIP
- **Prompt**: <verbatim>
- **Code chunks executed**: <count>
- **Result text**: <verbatim>
- **Evidence**: <objective facts>
- **If FAIL — error**: <verbatim>
- **If FAIL — likely root cause**: <one line>
- **If SKIP — reason**: <why>
```

---

## Reference: prior validation (v0.4.0)

The first end-to-end run was done on 2026-04-27 (logged in [`IMPLEMENTATION_LOG.md`](./IMPLEMENTATION_LOG.md), not here). It was a 5-test smoke check, not the full 30-test plan above. Score was 5/5 after patching 2 cross-version bugs. The full plan in `TESTING_PLAN.md` is the broader follow-up.
