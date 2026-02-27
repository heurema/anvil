#!/usr/bin/env python3
"""Validate install instructions in README.md match plugin.json and CLI conventions."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import Report, resolve_plugin_path, load_json_file

# Patterns for extracting fenced code blocks and install commands
FENCE_RE = re.compile(r"^```", re.MULTILINE)
MARKETPLACE_ADD_RE = re.compile(r"claude\s+plugin\s+marketplace\s+add\b")
PLUGIN_INSTALL_RE = re.compile(r"claude\s+plugin\s+install\s+(\S+)")
INSTALL_WITH_MARKETPLACE_RE = re.compile(r"claude\s+plugin\s+install\s+(\S+)@(\S+)")


def _extract_code_blocks(text: str) -> list[str]:
    """Extract content of all fenced code blocks from markdown."""
    blocks: list[str] = []
    lines = text.split("\n")
    in_block = False
    current: list[str] = []
    for line in lines:
        if FENCE_RE.match(line.strip()):
            if in_block:
                blocks.append("\n".join(current))
                current = []
                in_block = False
            else:
                in_block = True
                current = []
        elif in_block:
            current.append(line)
    return blocks


def validate(plugin_path: Path, report: Report) -> None:
    readme_path = plugin_path / "README.md"

    # Check README exists
    if not readme_path.exists() or readme_path.stat().st_size == 0:
        report.error("install_docs.no_readme", "README.md missing or empty")
        return

    text = readme_path.read_text(encoding="utf-8")
    code_blocks = _extract_code_blocks(text)
    all_code = "\n".join(code_blocks)

    # Check for any claude plugin command in code blocks
    has_claude_plugin = any("claude plugin" in block for block in code_blocks)
    if not has_claude_plugin:
        report.error("install_docs.no_install_block", "No fenced code block containing 'claude plugin'")
        return

    # Check for marketplace add
    has_marketplace_add = bool(MARKETPLACE_ADD_RE.search(all_code))
    if not has_marketplace_add:
        report.error("install_docs.no_marketplace_add", "Missing 'claude plugin marketplace add' line in code blocks")

    # Check for plugin install
    install_matches = PLUGIN_INSTALL_RE.findall(all_code)
    if not install_matches:
        report.error("install_docs.no_plugin_install", "Missing 'claude plugin install' line in code blocks")
        return

    # Load plugin.json for name verification
    pj_path = plugin_path / ".claude-plugin" / "plugin.json"
    pj = load_json_file(pj_path)
    plugin_name = pj.get("name", "") if isinstance(pj, dict) else ""

    # Check name matches plugin.json
    if plugin_name:
        name_found = False
        for arg in install_matches:
            # arg is like "sigil@emporium" or "sigil"
            install_name = arg.split("@")[0]
            if install_name == plugin_name:
                name_found = True
                break
        if not name_found:
            report.error(
                "install_docs.name_mismatch",
                f"Plugin name in install command doesn't match plugin.json name '{plugin_name}'",
                readme_names=", ".join(install_matches),
                plugin_json=plugin_name,
            )

    # Check for @marketplace-name suffix
    has_marketplace_suffix = bool(INSTALL_WITH_MARKETPLACE_RE.search(all_code))
    if not has_marketplace_suffix:
        report.error(
            "install_docs.missing_marketplace_suffix",
            "Install command missing '@marketplace-name' suffix (e.g. 'plugin install name@emporium')",
        )

    # CLI validation (optional)
    claude_bin = shutil.which("claude")
    if claude_bin:
        manifest = pj_path if pj_path.exists() else plugin_path
        try:
            result = subprocess.run(
                [claude_bin, "plugin", "validate", str(manifest)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                stderr = result.stderr.strip()[:200] if result.stderr else ""
                report.error(
                    "install_docs.cli_validate_fail",
                    f"'claude plugin validate' failed (exit {result.returncode})",
                    stderr=stderr,
                )
        except (subprocess.TimeoutExpired, OSError) as exc:
            report.info("install_docs.cli_validate_skip", f"claude CLI error: {exc}")
    else:
        report.info("install_docs.cli_validate_skip", "claude CLI not in PATH, skipping manifest validation")


if __name__ == "__main__":
    plugin_path = resolve_plugin_path()
    report = Report(str(plugin_path))
    validate(plugin_path, report)
    if "--json" in sys.argv:
        print(report.to_json())
    else:
        report.print_human()
    sys.exit(1 if report.has_errors else 0)
