---
description: |
  Test plugin hooks and skill descriptions. Runs fixture-driven hook tests
  and deterministic skill description checks. Use before publication.
  Triggers: "test plugin", "test hooks", "anvil test", "/anvil:test"
argument-hint: "[path-to-plugin]"
allowed-tools: Bash, Read, Glob, Grep
---

## /anvil:test — Hook and Skill Testing

### Step 1: Resolve target path

If `$ARGUMENTS` is non-empty, use it as the plugin path. Otherwise ask the user:
> "Which plugin do you want to test? Provide the absolute or relative path."

Expand `~` and resolve to an absolute path. Call it `PLUGIN_PATH`.

### Step 2: Verify prerequisites

Run:
```bash
test -d "$PLUGIN_PATH" && echo "EXISTS" || echo "MISSING"
```

If the directory does not exist, stop and report:
> "Path not found: $PLUGIN_PATH"

### Step 3: Run hook tests

Run the fixture-driven test runner and capture its full output and exit code:

```bash
python3 @${CLAUDE_PLUGIN_ROOT}/scripts/test_hooks.py "$PLUGIN_PATH"
```

If the output is `No hook test fixtures found.`, note that no hook tests exist — this is not a failure.

Otherwise, record the per-case results (each line starting with `[PASS]` or `[FAIL]`) and the summary line (`N tests: P passed, F failed`).

### Step 4: Run skill description checks

For each `skills/*/SKILL.md` found under `$PLUGIN_PATH`, perform these grep-based checks inline:

```bash
find "$PLUGIN_PATH/skills" -name "SKILL.md" 2>/dev/null | sort
```

For each SKILL.md file found, extract the skill directory name (the parent directory of SKILL.md) and run:

**Check A — description present and non-empty:**
```bash
grep -E '^description:' "$SKILL_FILE"
```
PASS if the line exists and has content after the colon. WARN otherwise.

**Check B — third-person voice (no first/second person at word boundaries):**
```bash
grep -iP '\b(I |You |My )\b' <<< "$DESCRIPTION_VALUE"
```
WARN if any match is found: "description uses first/second person".

**Check C — length under 1024 chars:**
Count characters in the extracted description value. WARN if >= 1024 chars.

**Check D — keywords from directory name:**
Take the skill directory name, split on `-` and `_`, drop words shorter than 4 chars, and check that at least one keyword appears (case-insensitive) in the description value:
```bash
grep -iF "$KEYWORD" <<< "$DESCRIPTION_VALUE"
```
WARN if no keywords match: "description missing keywords from skill name (<dir-name>)".

### Step 5: Present results

Output a two-section report.

**Section 1 — Hook Tests:**

```
## Hook Tests

  [PASS] <case-name>: PASS
  [FAIL] <case-name>: exit_code expected 0, got 1
  ...

N tests: P passed, F failed
```

If no fixtures exist:
```
## Hook Tests

  (no fixtures found — skipped)
```

**Section 2 — Skill Checks:**

```
## Skill Checks

  skills/<dir>/SKILL.md
    [PASS] description present
    [WARN] description uses first/second person
    [PASS] description < 1024 chars
    [WARN] description missing keywords from skill name (my-skill)
  ...
```

If no SKILL.md files exist:
```
## Skill Checks

  (no skills/ found — skipped)
```

### Step 6: Summary

Compute totals across both sections:
- Hook tests: P passed, F failed
- Skill checks: W warnings (all checks are PASS or WARN, not FAIL)

Print:
```
---
Summary: <hook-passed> hook test(s) passed, <hook-failed> failed | <skill-pass> skill check(s) passed, <skill-warn> warning(s)
```

Then state verdict:

If hook-failed == 0 and skill-warn == 0:
> **PASS** — all tests and checks clean.

If hook-failed == 0 and skill-warn > 0:
> **PASS with warnings** — hook tests clean, <skill-warn> skill description warning(s).

If hook-failed > 0:
> **FAIL** — <hook-failed> hook test(s) failed. Fix before publishing.
