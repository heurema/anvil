---
description: |
  Deep validation of a Claude Code plugin. Runs schema, structure, hooks,
  conventions, consistency, and install-docs checks. Use when you want to
  validate a plugin before publication or after changes.
  Triggers: "validate plugin", "check plugin", "anvil check", "/anvil:check"
argument-hint: "[path-to-plugin]"
allowed-tools: Bash, Read, Glob
---

## /anvil:check — Plugin Validation Pipeline

### Step 1: Resolve target path

If `$ARGUMENTS` is non-empty, use it as the plugin path. Otherwise ask the user:
> "Which plugin do you want to validate? Provide the absolute or relative path."

Expand `~` and resolve to an absolute path. Call it `PLUGIN_PATH`.

### Step 2: Verify prerequisites

Run:
```bash
test -d "$PLUGIN_PATH" && echo "EXISTS" || echo "MISSING"
test -d "$PLUGIN_PATH/.claude-plugin" && echo "MANIFEST_DIR" || echo "NO_MANIFEST_DIR"
```

If the directory does not exist, stop and report:
> "Path not found: $PLUGIN_PATH"

If `.claude-plugin/` is missing, warn the user that this may not be a valid plugin root, but continue — the schema validator will produce the definitive finding.

### Step 3: Run validators sequentially with --json

Run each validator and capture its JSON output and exit code. Stop early as described in Step 4.

```bash
python3 @${CLAUDE_PLUGIN_ROOT}/scripts/validate_schema.py "$PLUGIN_PATH" --json
```

```bash
python3 @${CLAUDE_PLUGIN_ROOT}/scripts/validate_structure.py "$PLUGIN_PATH" --json
```

```bash
python3 @${CLAUDE_PLUGIN_ROOT}/scripts/validate_hooks.py "$PLUGIN_PATH" --json
```

```bash
python3 @${CLAUDE_PLUGIN_ROOT}/scripts/validate_conventions.py "$PLUGIN_PATH" --json
```

```bash
python3 @${CLAUDE_PLUGIN_ROOT}/scripts/validate_consistency.py "$PLUGIN_PATH" --json
```

```bash
python3 @${CLAUDE_PLUGIN_ROOT}/scripts/validate_install_docs.py "$PLUGIN_PATH" --json
```

### Step 4: Short-circuit rule

After running `validate_schema.py`, inspect its findings array. If any finding has `"check_id": "schema.no_manifest"`, skip `validate_conventions.py` and `validate_consistency.py` entirely. State:
> "Skipping conventions and consistency checks: plugin.json not found (schema.no_manifest)."

### Step 5: Aggregate findings

Collect all findings from every validator that was run into a single list. Each finding has the shape:
```json
{"check_id": "...", "severity": "ERROR|WARN|INFO", "message": "...", "sources": {}}
```

Compute totals: count of ERROR, WARN, INFO across all validators.

### Step 6: Present unified report

Print a human-readable report in this format:

```
## Anvil Check — <PLUGIN_PATH>

### ERRORS (<n>)
- [schema.xxx] message          (if sources present, append: — source_file:line)
- [hooks.yyy] message

### WARNINGS (<n>)
- [structure.zzz] message

### INFO (<n>)
- [conventions.aaa] message

---
Validators run: schema, structure, hooks, conventions, consistency, install-docs   (or fewer if short-circuited)
```

Omit a severity section entirely if its count is 0.

### Step 7: State verdict

If ERROR count is 0:
> **PASS** — 0 errors, <warn> warnings, <info> info. Plugin is ready.

If ERROR count > 0:
> **FAIL** — <error> error(s), <warn> warnings, <info> info. Fix errors before publishing.
