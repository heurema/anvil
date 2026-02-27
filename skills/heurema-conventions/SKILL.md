---
name: heurema-conventions
description: |
  Heurema plugin development conventions. Auto-triggered when creating or
  editing Claude Code plugin components (commands, skills, agents, hooks,
  plugin.json) in the fabrica workspace. Reminds about file injection
  patterns, prompt organization, shell safety, and quality gates.
user-invocable: false
---

# Heurema Plugin Conventions

Quick reference for building plugins in the fabrica workspace.

## 1. File Injection

Use `@${CLAUDE_PLUGIN_ROOT}/path` for static file injection inside commands.
Content is loaded at command parse time — no runtime Read calls needed.

```markdown
@${CLAUDE_PLUGIN_ROOT}/lib/prompts/review.md
```

Never use the Read tool to load plugin-internal files at runtime.

## 2. Prompt Organization

Keep prompt templates in `lib/prompts/` separate from command logic.
Reference them from commands via `@${CLAUDE_PLUGIN_ROOT}/lib/prompts/<name>.md`.

```
lib/
  prompts/
    review.md
    summary.md
```

## 3. Agent Structure

Agents live in `agents/` with YAML frontmatter.

Required fields: `name`, `description`, `model`, `tools`
Optional fields: `maxTurns`, `color`, `skills`, `memory`

```yaml
---
name: reviewer
description: Reviews plugin code for security and correctness.
model: claude-sonnet-4-6
tools: [Read, Glob, Grep]
maxTurns: 20
---
```

## 4. Skill Structure

Skills live in `skills/<name>/SKILL.md`.

- Description: third person, keyword-rich, under 1024 chars
- Auto-triggered skills: `user-invocable: false`
- User-facing skills: `user-invocable: true`

## 5. Hook Safety

```json
{
  "hooks": [{
    "event": "PostToolUse",
    "command": "${CLAUDE_PLUGIN_ROOT}/scripts/hook.sh"
  }]
}
```

Rules:
- Use `${CLAUDE_PLUGIN_ROOT}` for all script paths — no hardcoded absolute paths
- Scripts must be executable (`chmod +x`)
- Read JSON from stdin: `jq` or `python3 -c 'import json,sys; d=json.load(sys.stdin)'`
- Never interpolate stdin data into shell strings
- No `eval`, no unquoted variable expansions

## 6. Shell Portability

- Pass data via stdin or temp files, not interpolation
- Avoid GNU-only flags (`--count`, `--null-data`); use POSIX alternatives
- Test on macOS (zsh default) and Linux (bash default)

## 7. Quality Gate

Before publishing a plugin:

1. Run `/anvil:check` — all validators must report 0 errors
2. Run `/anvil:test` — all hook fixtures must pass
3. Multi-reviewer team + Codex audit — target score 8+/10

Do not publish with open ERRORs.

## 8. Git

Conventional Commits format:

```
feat: add heurema-conventions skill
fix: correct path resolution in validate_hooks
docs: update README with install instructions
chore: bump version to 1.1.0
```

No AI branding in commits or PR descriptions.

## 9. Plugin Manifest

Location: `.claude-plugin/plugin.json`

```json
{
  "name": "anvil",
  "version": "1.0.0",
  "description": "Claude Code plugin validator and linter for the fabrica workspace.",
  "author": "heurema",
  "license": "MIT"
}
```

- `name` must match the plugin directory name exactly
- `version` follows semver (MAJOR.MINOR.PATCH)
