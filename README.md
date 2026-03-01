# Anvil

> Scaffold, validate, test, and review Claude Code plugins — all locally, all in one tool.

Anvil is the official plugin development toolkit for the heurema ecosystem. It gives plugin authors three commands that cover the complete plugin lifecycle: scaffold a new plugin from heurema-standard templates, run six sequential validators to catch schema errors, missing files, and unsafe hook scripts before you publish, and execute fixture-driven hook tests to verify runtime behaviour. A built-in code-review agent applies a 21-item quality checklist and returns an explicit APPROVE or REQUEST CHANGES verdict. Everything runs locally — no network, no credentials.

```
$ /anvil:new my-plugin
$ /anvil:check ./my-plugin
$ /anvil:test  ./my-plugin
```

## Quick Start

**Install via Emporium (recommended)**

<!-- INSTALL:START — auto-synced from emporium/INSTALL_REFERENCE.md -->
```bash
claude plugin marketplace add heurema/emporium   # once
claude plugin install anvil@emporium
```
<!-- INSTALL:END -->

**Manual install**

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

Verify: `ls ~/.claude/plugins/anvil/commands/` should show `new.md`, `check.md`, and `test.md`. Open a new Claude Code session to activate.

**First use**

```bash
# Scaffold a new plugin interactively
/anvil:new my-plugin

# Then validate and test before committing
/anvil:check ./my-plugin
/anvil:test  ./my-plugin
```

## Key Features

- **Scaffolding** — `/anvil:new` generates a complete, conventions-compliant plugin skeleton (plugin.json, README, LICENSE, CHANGELOG, .gitignore) from maintained templates; optionally initialises a git repo and creates a GitHub repository under the heurema org.
- **Six-layer validation** — `/anvil:check` runs schema, structure, hooks, conventions, consistency, and install-docs validators in sequence and returns a single PASS/FAIL verdict with a JSON-aggregated report.
- **Fixture-driven hook testing** — `/anvil:test` executes `scripts/test_hooks.py` against your hook scripts and checks skill descriptions for presence, voice, length, and keywords.
- **AI code review** — The `anvil-reviewer` agent (sonnet, read-only) applies a 21-item checklist and gives an unambiguous APPROVE or REQUEST CHANGES verdict.
- **Zero network dependency** — all validation and scaffolding is local; the optional `gh repo create` step is explicit and opt-in.

## Privacy & Data

Anvil makes no network calls during validation or scaffolding. No plugin files, metadata, or diagnostic output leave your machine. The optional GitHub repository creation step in `/anvil:new` uses your local `gh` CLI and is gated behind an explicit confirmation prompt.

## Requirements

- Claude Code with plugin support
- Python 3.14+ (for validator scripts and test framework)
- `jq` (for hook validators)
- `gh` CLI — optional, only needed if you want `/anvil:new` to create a GitHub repository

## Documentation

- [How it works](docs/how-it-works.md) — architecture, components, data flow, trust boundaries, limitations
- [Reference](docs/reference.md) — command usage, scenarios, configuration, output format, troubleshooting

## See Also

Other [heurema](https://github.com/heurema) projects:

- **[sigil](https://github.com/heurema/sigil)** — risk-adaptive development pipeline with adversarial consensus code review
- **[herald](https://github.com/heurema/herald)** — daily curated news digest plugin for Claude Code
- **[teams-field-guide](https://github.com/heurema/teams-field-guide)** — comprehensive guide to Claude Code multi-agent teams
- **[arbiter](https://github.com/heurema/arbiter)** — multi-AI orchestrator (Codex + Gemini)

## License

MIT
