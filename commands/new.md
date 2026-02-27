---
description: |
  Scaffold a new Claude Code plugin using heurema templates. Creates
  directory structure, plugin.json, README, LICENSE, CHANGELOG, and
  selected component directories. Use when starting a new plugin.
  Triggers: "new plugin", "create plugin", "scaffold", "anvil new", "/anvil:new"
argument-hint: "[plugin-name]"
allowed-tools: Bash, Read, Write, Glob
---

## /anvil:new — Plugin Scaffold

### Template sources (loaded at parse time)

plugin.json template:
@${CLAUDE_PLUGIN_ROOT}/templates/plugin.json.tmpl

README template:
@${CLAUDE_PLUGIN_ROOT}/templates/README.md.tmpl

LICENSE template:
@${CLAUDE_PLUGIN_ROOT}/templates/LICENSE.tmpl

.gitignore template:
@${CLAUDE_PLUGIN_ROOT}/templates/.gitignore.tmpl

CHANGELOG template:
@${CLAUDE_PLUGIN_ROOT}/templates/CHANGELOG.md.tmpl

---

### Step 1: Resolve plugin name

If `$ARGUMENTS` is non-empty, use it as the plugin name candidate. Otherwise ask:
> "What should the plugin be called? (lowercase slug, e.g. `my-plugin`)"

Validate the name against the pattern `^[a-z][a-z0-9]*(-[a-z0-9]+)*$`.

If validation fails, explain the rule and ask again. Do not proceed until the name is valid.

Call the validated value `PLUGIN_NAME`.

### Step 2: Conflict check

Run:
```bash
test -d "$HOME/personal/heurema/fabrica/{{PLUGIN_NAME}}" && echo "EXISTS" || echo "FREE"
```

(Replace `{{PLUGIN_NAME}}` with the actual name before running.)

If the result is `EXISTS`, stop immediately:
> "Directory already exists: ~/personal/heurema/fabrica/PLUGIN_NAME. Choose a different name or delete the existing directory first."

### Step 3: Gather metadata

Ask the following questions in sequence. Wait for each answer before proceeding.

1. **Description** — one sentence describing what the plugin does.
2. **Keywords** — comma-separated list (e.g. `claude, plugin, linting`). These will become JSON strings in `plugin.json`.

Store: `PLUGIN_DESCRIPTION`, `PLUGIN_KEYWORDS_RAW`.

Convert keywords to a JSON array fragment: split by comma, strip whitespace from each token, wrap each in double quotes, join with `, `. Example: `"claude", "plugin", "linting"`. Store as `PLUGIN_KEYWORDS_JSON`.

Compute dates:
- `PLUGIN_YEAR` — current 4-digit year (e.g. `2026`)
- `PLUGIN_DATE` — current date in YYYY-MM-DD format (e.g. `2026-02-27`)

Both values can be obtained from:
```bash
date +%Y
date +%Y-%m-%d
```

### Step 4: Select components

Ask the user which component directories to create. Present as a multi-select:

> "Which directories should be created? (enter numbers separated by spaces, or 'none')"
>
> 1. commands/
> 2. skills/
> 3. agents/
> 4. hooks/

Parse the response and build a list `COMPONENT_DIRS` of selected directory names. An answer of `none` or empty means no component directories are created beyond the root.

### Step 5: Create directory structure

Set `PLUGIN_ROOT` = `$HOME/personal/heurema/fabrica/PLUGIN_NAME`.

Run mkdir commands:
```bash
mkdir -p "$PLUGIN_ROOT"
```

For each selected component in `COMPONENT_DIRS`, run:
```bash
mkdir -p "$PLUGIN_ROOT/<component>"
```

### Step 6: Fill and write templates

For each template below, perform a simple string replacement on all placeholders:
- `{{NAME}}` → `PLUGIN_NAME`
- `{{DESCRIPTION}}` → `PLUGIN_DESCRIPTION`
- `{{KEYWORDS}}` → `PLUGIN_KEYWORDS_JSON`
- `{{YEAR}}` → `PLUGIN_YEAR`
- `{{DATE}}` → `PLUGIN_DATE`

Write the filled content to the target path using the Write tool.

| Template (loaded above) | Target path |
|-------------------------|-------------|
| plugin.json template    | `$PLUGIN_ROOT/plugin.json` |
| README template         | `$PLUGIN_ROOT/README.md` |
| LICENSE template        | `$PLUGIN_ROOT/LICENSE` |
| .gitignore template     | `$PLUGIN_ROOT/.gitignore` |
| CHANGELOG template      | `$PLUGIN_ROOT/CHANGELOG.md` |

### Step 7: Confirm result

List the created files:
```bash
find "$PLUGIN_ROOT" -not -path '*/.git/*' | sort
```

Report to the user:
> "Created PLUGIN_NAME at ~/personal/heurema/fabrica/PLUGIN_NAME"
>
> List the files and directories created.

### Step 8: Git init (optional)

Ask:
> "Initialize a git repository and create the initial commit? (yes/no)"

If yes:
```bash
cd "$PLUGIN_ROOT" && git init && git add . && git commit -m "chore: initial scaffold"
```

Report the result. If the user says no, skip silently.

### Step 9: GitHub repo (optional)

Ask:
> "Create a public GitHub repo under the heurema org and push? (yes/no)"

If yes, first verify git is initialized (if Step 8 was skipped, run `git init && git add . && git commit -m "chore: initial scaffold"` now). Then run:
```bash
gh repo create heurema/PLUGIN_NAME --public --source "$PLUGIN_ROOT" --remote origin --push
```

If the command succeeds, report the repo URL. If it fails, show the error and suggest the user run it manually.

If the user says no, remind them they can run it later:
> "You can create the repo later with: `gh repo create heurema/PLUGIN_NAME --public --source ~/personal/heurema/fabrica/PLUGIN_NAME --remote origin --push`"
