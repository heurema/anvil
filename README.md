# anvil

Plugin development toolkit for the heurema fabrica workspace — scaffold, validate, and test Claude Code plugins before publication.

## Overview

Anvil is a Claude Code plugin used exclusively within the [heurema fabrica](https://github.com/heurema) workspace to develop other plugins. It combines an LLM-driven scaffold command with a deterministic 5-validator pipeline and a fixture-driven hook test runner, closing the loop between creation and publication quality gate. Anvil is not a general-purpose plugin linter — it encodes heurema-specific conventions and is intended for fabrica maintainers only.

## Installation

### Via Emporium (recommended)

```bash
claude plugin marketplace add heurema/emporium   # once
claude plugin install anvil@emporium
```

### Manual

```bash
git clone https://github.com/heurema/anvil.git ~/.claude/plugins/anvil
```

Then enable in `~/.claude/settings.json`:

```json
{
  "enabledPlugins": {
    "anvil@local": true
  }
}
```

Verify: `ls ~/.claude/plugins/anvil/commands/` should show `new.md`, `check.md`, and `test.md`. Then open a new Claude Code session.

## Commands

### `/anvil:new [name]`

Scaffold a new plugin under `~/personal/heurema/fabrica/<name>/`. Interactively collects plugin name, description, and keywords, then creates the full directory structure and fills five templates: `plugin.json`, `README.md`, `LICENSE`, `.gitignore`, and `CHANGELOG.md`. Optionally initializes a git repository and creates a GitHub repo under the heurema org.

### `/anvil:check [path]`

Run the 5-validator pipeline against a plugin directory. Validators execute sequentially; if `validate_schema` reports a missing manifest (`schema.no_manifest`), conventions and consistency checks are skipped. Results are aggregated into a unified report with ERROR / WARN / INFO counts and a PASS or FAIL verdict.

Validators:

| Validator | What it checks |
|-----------|---------------|
| `validate_schema.py` | `plugin.json` required fields, semver format, name slug, CHANGELOG version alignment |
| `validate_structure.py` | Required files present (`README.md`, `LICENSE`, `CHANGELOG.md`), declared commands/agents/skills exist on disk |
| `validate_hooks.py` | Hook scripts executable, use `jq` or Python JSON parsing for stdin, no dangerous shell patterns (`eval`, unquoted expansions), no hardcoded absolute paths |
| `validate_conventions.py` | `@${CLAUDE_PLUGIN_ROOT}/` injection syntax, prompt templates in `lib/prompts/`, skill descriptions (third person, keyword-rich, under 1024 chars), no XML tags in frontmatter |
| `validate_consistency.py` | Cross-file coherence: `plugin.json` name matches directory, version matches CHANGELOG, no duplicate command names |

### `/anvil:test [path]`

Run fixture-driven hook tests and skill description checks against a plugin directory. Hook tests exercise actual hook scripts against JSON payloads from `fixtures/hooks/`. Skill checks verify each `skills/*/SKILL.md` description for presence, voice, length, and keyword coverage. Produces a two-section report (Hook Tests / Skill Checks) with a summary verdict.

## Agent

### anvil-reviewer

A read-only sonnet agent that performs a 20-item pre-publication quality review. It checks schema and metadata completeness, README and CHANGELOG quality, command and skill frontmatter, hook security (no hardcoded paths, no `eval`, stdin JSON safety), and heurema conventions. Produces a structured findings table with PASS / FAIL / WARN / N/A status per item, a verdict (APPROVE or REQUEST CHANGES), and numbered required fixes if any FAILs are found.

Use anvil-reviewer as a final gate before pushing a plugin to GitHub and submitting it to the emporium marketplace. It is not a replacement for `/anvil:check` and `/anvil:test` — run those first to catch structural and hook issues deterministically.

## Skill

### heurema-conventions

An auto-triggered skill (not user-invocable) that injects heurema plugin development conventions into the context whenever Claude Code is creating or editing plugin components: commands, skills, agents, hooks, or `plugin.json`. Covers file injection syntax (`@${CLAUDE_PLUGIN_ROOT}/path`), prompt organization (`lib/prompts/`), agent and skill frontmatter requirements, hook safety rules, shell portability, quality gate steps, and Conventional Commits format. The skill fires automatically — no explicit invocation needed.

## Fixtures

### Hook test fixtures (`fixtures/hooks/`)

Each subdirectory represents one test case and contains a `case.json` file:

```json
{
  "name": "Block dangerous rm -rf command",
  "hook_script": "fixtures/hooks/test-guard.sh",
  "event": {"tool_name": "Bash", "tool_input": {"command": "rm -rf /"}},
  "expected": {"exit_code": 2, "stderr_contains": ["blocked"]},
  "timeout_seconds": 5
}
```

Fields:
- `name` — human-readable test description
- `hook_script` — path to the hook script under test (relative to the plugin root)
- `event` — JSON payload fed to the script via stdin, simulating a Claude Code hook event
- `expected` — assertions: `exit_code` (required), `stdout_contains` (optional array), `stderr_contains` (optional array)
- `timeout_seconds` — maximum runtime before the test fails

`test_hooks.py` iterates all `fixtures/hooks/*/case.json` files, feeds the event payload to the script via stdin, and compares exit code and output against the expected values.

### Plugin samples (`fixtures/plugin-samples/`)

Two reference plugin directories used by validator tests:
- `valid-minimal/` — smallest valid plugin (passes all validators)
- `broken-schema/` — intentionally malformed `plugin.json` (exercises `validate_schema` error paths)

## Development

To work on anvil itself, run validators against the anvil directory:

```bash
python3 scripts/validate_schema.py . --json
python3 scripts/validate_structure.py . --json
python3 scripts/validate_hooks.py . --json
python3 scripts/validate_conventions.py . --json
python3 scripts/validate_consistency.py . --json
```

Or use `/anvil:check ~/personal/heurema/fabrica/anvil` from within Claude Code.

Run the hook test suite:

```bash
python3 scripts/test_hooks.py .
```

All validators share a common severity model and JSON output schema defined in `scripts/common.py`. Add new check IDs using the `report.error()`, `report.warn()`, or `report.info()` methods.

## See Also

Other [heurema](https://github.com/heurema) projects:

- **[sigil](https://github.com/heurema/sigil)** — risk-adaptive development pipeline with adversarial consensus code review
- **[herald](https://github.com/heurema/herald)** — daily curated news digest plugin for Claude Code
- **[teams-field-guide](https://github.com/heurema/teams-field-guide)** — comprehensive guide to Claude Code multi-agent teams
- **[codex-partner](https://github.com/heurema/codex-partner)** — using Codex CLI as second AI alongside Claude Code

## License

MIT
