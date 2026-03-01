# How Anvil Works

## Overview

Anvil is a Claude Code plugin, meaning it runs entirely within the Claude Code process on the developer's machine. It has no server component, no telemetry, and no network dependencies for its core functionality. All three commands invoke local Python scripts or local LLM inference via Claude Code's agent runtime.

## Components

### Commands (3)

Each command is a Markdown file in `commands/` that defines a Claude Code slash command. Commands use `@${CLAUDE_PLUGIN_ROOT}/` injection to load prompts, validator scripts, and templates from the plugin directory at runtime.

| Command | Entry point | Mode |
|---------|-------------|------|
| `/anvil:new [name]` | `commands/new.md` | Interactive (LLM-driven) |
| `/anvil:check [path]` | `commands/check.md` | Deterministic (script pipeline) |
| `/anvil:test [path]` | `commands/test.md` | Deterministic + LLM skill checks |

### Agent: anvil-reviewer

A read-only sonnet agent defined in `agents/anvil-reviewer.md`. It receives the plugin directory as context, applies a 21-item checklist covering schema completeness, README quality, hook security, and heurema conventions, and outputs a structured findings table with a final APPROVE or REQUEST CHANGES verdict. The agent cannot modify files — it only reads and evaluates.

### Skill: heurema-conventions

An auto-triggered skill in `skills/heurema-conventions/SKILL.md`. It is not user-invocable. Claude Code loads it automatically whenever the session context indicates the user is creating or editing plugin components (commands, skills, agents, hooks, `plugin.json`). The skill injects heurema-specific rules — injection syntax, prompt organisation, frontmatter requirements, hook safety patterns, shell portability rules — without requiring the developer to remember them.

### Validator scripts (6)

Python 3.14 scripts in `scripts/`. All share a common reporting interface defined in `scripts/common.py` that emits structured JSON when called with `--json`. Each validator operates on a plugin root directory path and returns a list of findings with `id`, `severity` (ERROR/WARN/INFO), and `message` fields.

| Script | Domain |
|--------|--------|
| `validate_schema.py` | plugin.json field presence, semver, name slug, CHANGELOG alignment |
| `validate_structure.py` | Required files on disk, declared components present |
| `validate_hooks.py` | Script executability, stdin JSON handling, shell safety patterns |
| `validate_conventions.py` | Injection syntax, prompt location, skill description quality |
| `validate_consistency.py` | Cross-file coherence (name, version, no duplicate commands) |
| `validate_install_docs.py` | README install block correctness |

### Templates (5)

Jinja-style template files in `templates/`. Filled by `/anvil:new` with values collected interactively: plugin name, description, author, keywords, and timestamp.

| Template | Output file |
|----------|------------|
| `plugin.json.tmpl` | `plugin.json` |
| `README.md.tmpl` | `README.md` |
| `LICENSE.tmpl` | `LICENSE` |
| `.gitignore.tmpl` | `.gitignore` |
| `CHANGELOG.md.tmpl` | `CHANGELOG.md` |

### Hook test framework

`scripts/test_hooks.py` is the test runner. It discovers all `fixtures/hooks/*/case.json` files, feeds each `event` payload to the specified hook script via stdin, captures stdout/stderr and exit code, and asserts against the `expected` block. Test cases are self-contained: each `case.json` specifies the script path, event, assertions, and timeout.

## Data Flow

### /anvil:new

```
User provides name
  -> LLM validates name (slug format, no conflicts)
  -> LLM collects description + keywords interactively
  -> LLM selects applicable component templates
  -> LLM fills templates and writes files to target directory
  -> Optional: git init (local subprocess)
  -> Optional: gh repo create (subprocess calling gh CLI -> GitHub API)
```

The only network call in the entire flow is the optional `gh repo create`, which uses the developer's existing `gh` auth token. It is gated behind an explicit yes/no prompt.

### /anvil:check

```
User provides path
  -> validate_schema.py path --json
  -> [if schema OK] validate_structure.py path --json
  -> [if schema OK] validate_hooks.py path --json
  -> [if schema OK] validate_conventions.py path --json
  -> [if schema OK] validate_consistency.py path --json
  -> validate_install_docs.py path --json
  -> LLM aggregates JSON results -> unified report -> PASS or FAIL
```

If `validate_schema` finds no `plugin.json` (check ID `schema.no_manifest`), the convention-dependent validators are skipped to avoid cascading false positives.

### /anvil:test

```
User provides path
  -> python3 scripts/test_hooks.py path  (subprocess)
  -> LLM reads each skills/*/SKILL.md
  -> LLM checks: presence, voice (third person), length (<1024 chars), keyword coverage
  -> LLM produces two-section report: Hook Tests + Skill Checks -> verdict
```

## Trust Boundaries

| Boundary | Detail |
|----------|--------|
| File system | Read access to the target plugin directory; write access only during /anvil:new scaffold |
| Network | None during check/test. GitHub API only during /anvil:new gh repo create, opt-in |
| Subprocess | Validator scripts and test_hooks.py run as local Python subprocesses; hook scripts under test run in sandboxed subprocess with timeout |
| LLM inference | Claude Code local inference for /anvil:new (interactive), /anvil:check (aggregation), /anvil:test (skill checks), and anvil-reviewer; no data sent to external LLM endpoints |
| Credentials | None stored or read by anvil; gh CLI manages its own auth |

## Limitations

- Anvil encodes heurema conventions only. It will produce false negatives for plugins following different structural conventions.
- `validate_hooks.py` performs static analysis on shell scripts — it does not execute them during validation. Behavioural correctness is tested only by `/anvil:test` via fixture cases.
- anvil-reviewer is LLM-based and non-deterministic. Its 21-item checklist is a prompt; results should be treated as a strong signal, not a formal proof.
- `/anvil:new` does not handle monorepo layouts or workspaces with non-standard plugin paths.
- Hook test fixture coverage depends entirely on the cases the plugin author writes. Anvil provides the runner; authors supply the fixtures.
