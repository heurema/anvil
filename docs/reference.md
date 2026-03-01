# Anvil Reference

## Commands

### /anvil:new [name]

Scaffold a new heurema-standard plugin interactively.

**Arguments**

| Argument | Required | Description |
|----------|----------|-------------|
| `name` | Yes | Plugin name. Must be a lowercase slug: `[a-z][a-z0-9-]*`. |

**Interactive flow**

1. Validates the name format and checks for conflicts in the heurema fabrica workspace.
2. Collects one-line description and comma-separated keywords.
3. Asks which components to include (commands, agents, skills, hooks).
4. Writes the target directory with all selected templates filled.
5. Offers optional `git init`.
6. Offers optional `gh repo create` under the heurema org (requires `gh` CLI and auth).

**Output**

```
Created: ~/personal/heurema/fabrica/my-plugin/
  plugin.json
  README.md
  LICENSE
  CHANGELOG.md
  .gitignore
  commands/  (if selected)
  agents/    (if selected)
  skills/    (if selected)

Next steps:
  /anvil:check ~/personal/heurema/fabrica/my-plugin
  /anvil:test  ~/personal/heurema/fabrica/my-plugin
```

---

### /anvil:check [path]

Run the six-validator pipeline against a plugin directory.

**Arguments**

| Argument | Required | Description |
|----------|----------|-------------|
| `path` | Yes | Absolute or relative path to the plugin root directory. |

**Validator execution order**

Validators run sequentially. If `validate_schema` reports `schema.no_manifest`, the remaining validators that depend on `plugin.json` are skipped.

| Order | Validator | Skipped if no manifest |
|-------|-----------|------------------------|
| 1 | `validate_schema.py` | No |
| 2 | `validate_structure.py` | No |
| 3 | `validate_hooks.py` | No |
| 4 | `validate_conventions.py` | Yes |
| 5 | `validate_consistency.py` | Yes |
| 6 | `validate_install_docs.py` | No |

**Output format**

```
Anvil check: ./my-plugin

[validate_schema]      PASS  (0 errors, 0 warnings)
[validate_structure]   PASS  (0 errors, 1 warning)
  WARN  structure.missing_optional  agents/ directory declared but not present
[validate_hooks]       PASS  (0 errors, 0 warnings)
[validate_conventions] FAIL  (1 error, 0 warnings)
  ERROR conventions.bad_injection  commands/run.md uses absolute path instead of @${CLAUDE_PLUGIN_ROOT}/
[validate_consistency] PASS  (0 errors, 0 warnings)
[validate_install_docs] PASS (0 errors, 0 warnings)

Result: FAIL  (1 error, 1 warning across 6 validators)
```

**Exit conditions**

- Any ERROR finding from any validator → FAIL
- WARN findings do not cause FAIL but are reported
- INFO findings are cosmetic only

---

### /anvil:test [path]

Run fixture-driven hook tests and skill description checks.

**Arguments**

| Argument | Required | Description |
|----------|----------|-------------|
| `path` | Yes | Absolute or relative path to the plugin root directory. |

**Output format**

```
Anvil test: ./my-plugin

Hook Tests
  PASS  Block dangerous rm -rf command        (exit 2, stderr "blocked")
  PASS  Allow safe ls command                 (exit 0)
  FAIL  Rate limit enforcement                (expected exit 1, got exit 0)

Skill Checks
  PASS  heurema-conventions  presence, voice, length, keywords

Summary: 2 passed, 1 failed (Hook Tests) | 1 passed, 0 failed (Skill Checks)
Verdict: FAIL
```

---

## Usage Scenarios

### Scenario 1: Starting a new plugin from scratch

```
/anvil:new sigil-guard
```

Follow the prompts. When the scaffold is complete:

```
/anvil:check ~/personal/heurema/fabrica/sigil-guard
```

Fix any ERRORs reported. Then run hook tests once you have written fixture cases:

```
/anvil:test ~/personal/heurema/fabrica/sigil-guard
```

Finally, invoke anvil-reviewer for the pre-publication quality gate:

```
@anvil-reviewer review ~/personal/heurema/fabrica/sigil-guard
```

---

### Scenario 2: Validating an existing plugin before a PR

You have made changes to an existing plugin and want to ensure nothing is broken before pushing.

```
/anvil:check ~/personal/heurema/fabrica/reporter
```

If PASS, proceed. If FAIL, address the listed errors and re-run. The check is idempotent and fast (pure Python, no LLM calls during the script phase).

---

### Scenario 3: Debugging a hook script

You have a hook that behaves differently from expectations. Add a fixture case:

```json
// fixtures/hooks/my-case/case.json
{
  "name": "Reject curl to external hosts",
  "hook_script": "hooks/network-guard.sh",
  "event": {
    "tool_name": "Bash",
    "tool_input": {"command": "curl https://example.com"}
  },
  "expected": {
    "exit_code": 2,
    "stderr_contains": ["blocked: external network"]
  },
  "timeout_seconds": 5
}
```

Then run:

```
/anvil:test ~/personal/heurema/fabrica/my-plugin
```

The runner will show exactly what exit code and output the script produced, making it easy to diff against the expected values.

---

### Scenario 4: Running validators directly (CI or shell)

Each validator can be invoked from the shell without Claude Code:

```bash
cd ~/personal/heurema/fabrica/my-plugin

python3 scripts/validate_schema.py .       --json
python3 scripts/validate_structure.py .    --json
python3 scripts/validate_hooks.py .        --json
python3 scripts/validate_conventions.py .  --json
python3 scripts/validate_consistency.py .  --json
python3 scripts/validate_install_docs.py . --json
```

Without `--json`, output is human-readable. With `--json`, output is a JSON array of finding objects suitable for parsing in CI scripts.

**JSON finding schema:**

```json
[
  {
    "id": "conventions.bad_injection",
    "severity": "ERROR",
    "message": "commands/run.md uses absolute path instead of @${CLAUDE_PLUGIN_ROOT}/"
  }
]
```

Exit codes: `0` = no errors (warnings may be present), `1` = at least one ERROR.

---

### Scenario 5: Using anvil-reviewer as a final gate

After `/anvil:check` and `/anvil:test` both pass, invoke the reviewer agent for a holistic quality assessment before submitting to the emporium marketplace:

```
@anvil-reviewer review ~/personal/heurema/fabrica/my-plugin
```

The agent reads all plugin files in read-only mode and produces:

```
anvil-reviewer findings
=======================

| # | Item                             | Status |
|---|----------------------------------|--------|
| 1 | plugin.json required fields      | PASS   |
| 2 | semver format                    | PASS   |
| 3 | CHANGELOG entry matches version  | PASS   |
| 4 | README install block present     | FAIL   |
| 5 | Hook: no eval usage              | PASS   |
...
| 21| Skill description length < 1024  | PASS   |

Verdict: REQUEST CHANGES

Required fixes:
1. [Item 4] README is missing the <!-- INSTALL:START --> block required by emporium.
```

---

## Configuration

Anvil has no configuration file. Conventions are encoded in the validator scripts and the `heurema-conventions` skill. To customise validation behaviour for your own fork, edit the relevant `scripts/validate_*.py` file and bump the version in `plugin.json`.

---

## Troubleshooting

**"No such file or directory: plugin.json"**
The path you passed to `/anvil:check` does not point to a plugin root. Ensure the directory contains `plugin.json`. Run with the absolute path to avoid working-directory confusion.

**"validate_hooks.py: jq not found"**
Install `jq`: `brew install jq` (macOS) or `apt install jq` (Debian/Ubuntu). The hook validator requires `jq` to statically analyse JSON parsing patterns in hook scripts.

**Hook test times out**
The fixture `timeout_seconds` value is too low, or the hook script is hanging. Check that the hook script reads from stdin and exits promptly when given the test payload. Increase `timeout_seconds` to diagnose.

**anvil-reviewer returns REQUEST CHANGES on a passing /anvil:check**
`/anvil:check` is deterministic and checks structural correctness. `anvil-reviewer` is LLM-based and evaluates quality, clarity, and completeness beyond what static validators can detect. Both gates are intentional and complementary. Address the reviewer's findings, then re-invoke it.

**"gh: command not found" during /anvil:new**
Install the GitHub CLI: https://cli.github.com. The `gh repo create` step is optional — you can skip it and push the repository manually later.
