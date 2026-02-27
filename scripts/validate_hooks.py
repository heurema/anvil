#!/usr/bin/env python3
"""Validate hook scripts: schema, permissions, dangerous patterns."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import Report, resolve_plugin_path, load_json_file

DANGEROUS_PATTERNS = [
    (re.compile(r'\beval\s'), "eval usage"),
    (re.compile(r'(?<!\$)\$\([^)]*\)(?!["\'])'), "unquoted command substitution"),
    (re.compile(r'/Users/|/home/'), "hardcoded user path"),
]

VALID_EVENTS = {
    "PreToolUse", "PostToolUse", "Stop", "SubagentStop",
    "SessionStart", "SessionEnd", "UserPromptSubmit",
    "PreCompact", "Notification",
}


def validate(plugin_path: Path, report: Report) -> None:
    hooks_json_path = plugin_path / "hooks" / "hooks.json"
    hooks_data = load_json_file(hooks_json_path)

    if hooks_data is None:
        if (plugin_path / "hooks").is_dir():
            report.warn("hooks.no_hooks_json", "hooks/ directory exists but no hooks.json found")
        return  # no hooks, nothing to validate

    if not isinstance(hooks_data, dict):
        report.error("hooks.invalid_schema", "hooks.json must be a JSON object")
        return

    hooks_field = hooks_data.get("hooks", [])

    # Normalize two formats:
    # Array format: {"hooks": [{"event": "SessionStart", "matcher": "...", "hooks": [...]}]}
    # Object format: {"hooks": {"SessionStart": [{"matcher": "...", "hooks": [...]}]}}
    normalized: list[tuple[str, dict]] = []  # (event_name, hook_entry)

    if isinstance(hooks_field, list):
        for hook in hooks_field:
            normalized.append((hook.get("event", ""), hook))
    elif isinstance(hooks_field, dict):
        for event_name, entries in hooks_field.items():
            if isinstance(entries, list):
                for entry in entries:
                    normalized.append((event_name, entry))
    else:
        report.error("hooks.invalid_hooks_field", "hooks.hooks must be an array or object")
        return

    for i, (event, hook) in enumerate(normalized):
        prefix = f"hooks[{i}]"

        # Event name
        if event not in VALID_EVENTS:
            report.warn("hooks.unknown_event", f"{prefix}: unknown event '{event}'", event=event)

        # Matcher
        if "matcher" not in hook and "pattern" not in hook:
            report.info("hooks.no_matcher", f"{prefix}: no matcher/pattern — hook matches all")

        # Command/script
        for sub_hook in hook.get("hooks", []):
            cmd = sub_hook.get("command", "")

            # Script reference should use ${CLAUDE_PLUGIN_ROOT}
            if cmd and "/" in cmd and "${CLAUDE_PLUGIN_ROOT}" not in cmd:
                report.warn("hooks.no_plugin_root",
                            f"{prefix}: command path doesn't use ${{CLAUDE_PLUGIN_ROOT}}",
                            command=cmd[:80])

            # Resolve and check script existence
            if "${CLAUDE_PLUGIN_ROOT}" in cmd:
                script_rel = cmd.replace("${CLAUDE_PLUGIN_ROOT}", "").lstrip("/").split()[0]
                script_path = plugin_path / script_rel
                if not script_path.exists():
                    report.error("hooks.missing_script",
                                 f"{prefix}: referenced script not found: {script_rel}",
                                 script=script_rel)
                elif not os.access(script_path, os.X_OK):
                    report.error("hooks.not_executable",
                                 f"{prefix}: script not executable: {script_rel}",
                                 script=script_rel)
                else:
                    # Check script content for dangerous patterns
                    content = script_path.read_text(encoding="utf-8", errors="replace")
                    for pattern, desc in DANGEROUS_PATTERNS:
                        if pattern.search(content):
                            report.warn("hooks.dangerous_pattern",
                                        f"{prefix}: {script_rel} contains {desc}",
                                        script=script_rel, pattern=desc)

            # Timeout
            timeout = sub_hook.get("timeout")
            if timeout is not None:
                if not isinstance(timeout, (int, float)) or timeout < 1 or timeout > 600:
                    report.warn("hooks.bad_timeout",
                                f"{prefix}: timeout should be 1-600 seconds, got {timeout}")


if __name__ == "__main__":
    plugin_path = resolve_plugin_path()
    report = Report(str(plugin_path))
    validate(plugin_path, report)
    if "--json" in sys.argv:
        print(report.to_json())
    else:
        report.print_human()
    sys.exit(1 if report.has_errors else 0)
