#!/usr/bin/env python3
"""Validate plugin directory structure and file naming."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import Report, resolve_plugin_path

COMPONENT_DIRS = ("commands", "skills", "agents", "hooks")
ALLOWED_IN_CLAUDE_PLUGIN = {"plugin.json", "marketplace.json"}


def validate(plugin_path: Path, report: Report) -> None:
    # .claude-plugin/ must exist
    cp_dir = plugin_path / ".claude-plugin"
    if not cp_dir.is_dir():
        report.error("structure.no_claude_plugin", "Missing .claude-plugin/ directory")
        return

    # Only allowed files inside .claude-plugin/
    for f in cp_dir.iterdir():
        if f.name not in ALLOWED_IN_CLAUDE_PLUGIN:
            report.warn("structure.unexpected_manifest_file",
                        f"Unexpected file in .claude-plugin/: {f.name}", file=f.name)

    # At least one component directory
    has_component = any((plugin_path / d).is_dir() for d in COMPONENT_DIRS)
    if not has_component:
        report.warn("structure.no_components",
                     "No component directories found (commands/, skills/, agents/, hooks/)")

    # README with content
    readme = plugin_path / "README.md"
    if not readme.exists():
        report.error("structure.no_readme", "Missing README.md")
    elif readme.stat().st_size < 50:
        report.warn("structure.empty_readme", "README.md appears empty or minimal")

    # LICENSE
    if not (plugin_path / "LICENSE").exists():
        report.warn("structure.no_license", "Missing LICENSE file")

    # Commands must be .md
    cmd_dir = plugin_path / "commands"
    if cmd_dir.is_dir():
        for f in cmd_dir.iterdir():
            if f.is_file() and f.suffix != ".md":
                report.warn("structure.command_not_md",
                            f"Command file is not .md: {f.name}", file=str(f.relative_to(plugin_path)))

    # Skills must have SKILL.md entrypoint
    skills_dir = plugin_path / "skills"
    if skills_dir.is_dir():
        for d in skills_dir.iterdir():
            if d.is_dir() and not (d / "SKILL.md").exists():
                report.error("structure.skill_no_entrypoint",
                             f"Skill {d.name}/ missing SKILL.md entrypoint", skill=d.name)

    # Agents must be .md with frontmatter
    agents_dir = plugin_path / "agents"
    if agents_dir.is_dir():
        for f in agents_dir.iterdir():
            if f.is_file() and f.suffix != ".md":
                report.warn("structure.agent_not_md",
                            f"Agent file is not .md: {f.name}", file=f.name)
            elif f.is_file() and f.suffix == ".md":
                content = f.read_text(encoding="utf-8")
                if not content.startswith("---"):
                    report.warn("structure.agent_no_frontmatter",
                                f"Agent {f.name} missing YAML frontmatter", file=f.name)


if __name__ == "__main__":
    plugin_path = resolve_plugin_path()
    report = Report(str(plugin_path))
    validate(plugin_path, report)
    if "--json" in sys.argv:
        print(report.to_json())
    else:
        report.print_human()
    sys.exit(1 if report.has_errors else 0)
