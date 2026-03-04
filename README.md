# Anvil

<div align="center">

**Scaffold, validate, and test Claude Code plugins**

[![Claude Code Plugin](https://img.shields.io/badge/Claude_Code-plugin-5b21b6?style=flat-square)](https://skill7.dev)
[![Version](https://img.shields.io/badge/version-0.1.0-5b21b6?style=flat-square)]()
[![License](https://img.shields.io/badge/license-MIT-5b21b6?style=flat-square)](LICENSE)

<br>

```bash
claude plugin marketplace add heurema/emporium   # once
claude plugin install anvil@emporium
```

</div>

## What it does

Anvil is the official plugin development toolkit for the heurema ecosystem. It covers the complete plugin lifecycle: scaffold a new plugin from heurema-standard templates, run six sequential validators to catch schema errors, missing files, and unsafe hook scripts before you publish, and execute fixture-driven hook tests to verify runtime behaviour. A built-in code-review agent applies a 21-item quality checklist and returns an explicit APPROVE or REQUEST CHANGES verdict. Everything runs locally — no network, no credentials.

## Install

<!-- INSTALL:START -- auto-synced from emporium/INSTALL_REFERENCE.md -->
```bash
claude plugin marketplace add heurema/emporium
claude plugin install anvil@emporium
```
<!-- INSTALL:END -->

<details>
<summary>Manual install (from source)</summary>

```bash
git clone https://github.com/heurema/anvil.git ~/.claude/plugins/anvil
```

Then add to `~/.claude/settings.json`:

```json
{
  "permissions": {
    "allow": ["Bash(~/.claude/plugins/anvil/hooks/*)"]
  }
}
```

Open a new Claude Code session to activate.

</details>

## Quick start

```
/anvil:new my-plugin
/anvil:check ./my-plugin
/anvil:test  ./my-plugin
```

## Commands

| Command | What it does |
|---------|-------------|
| `/anvil:new` | Scaffold a complete plugin skeleton from heurema-standard templates |
| `/anvil:check` | Run six sequential validators and return a single PASS/FAIL verdict |
| `/anvil:test` | Execute fixture-driven hook tests to verify runtime behaviour |

## Features

- **Scaffolding** — `/anvil:new` generates a conventions-compliant plugin skeleton (plugin.json, README, LICENSE, CHANGELOG, .gitignore); optionally initialises a git repo and creates a GitHub repository under the heurema org.
- **Six-layer validation** — `/anvil:check` runs schema, structure, hooks, conventions, consistency, and install-docs validators in sequence and aggregates results into a JSON report.
- **Fixture-driven hook testing** — `/anvil:test` executes `scripts/test_hooks.py` against your hook scripts and checks skill descriptions for presence, voice, length, and keywords.
- **AI code review** — The `anvil-reviewer` agent (sonnet, read-only) applies a 21-item checklist and gives an unambiguous APPROVE or REQUEST CHANGES verdict.
- **Zero network dependency** — all validation and scaffolding is local; the optional `gh repo create` step is explicit and opt-in.

## Requirements

- Claude Code with plugin support
- Python 3.14+ (for validator scripts and test framework)
- `jq` (for hook validators)
- `gh` CLI — optional, only needed if you want `/anvil:new` to create a GitHub repository

## Privacy

Anvil makes no network calls during validation or scaffolding. No plugin files, metadata, or diagnostic output leave your machine. The optional GitHub repository creation step in `/anvil:new` uses your local `gh` CLI and is gated behind an explicit confirmation prompt.

## See also

- [skill7.dev](https://skill7.dev) — plugin catalog and docs
- [emporium](https://github.com/heurema/emporium) — the heurema marketplace
- [forge](https://github.com/heurema/forge) — plugin publishing and release pipeline
- [signum](https://github.com/heurema/signum) — risk-adaptive development pipeline with adversarial consensus code review

## License

[MIT](LICENSE)
