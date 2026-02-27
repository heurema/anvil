#!/usr/bin/env python3
"""Validate heurema-specific plugin conventions."""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import Report, resolve_plugin_path

FIRST_PERSON_RE = re.compile(r'\b(I |You |My |Your )', re.IGNORECASE)
SECRET_PATTERNS = re.compile(r'(api[_-]?key|token|password|secret)\s*[:=]', re.IGNORECASE)
HARDCODED_PATH_RE = re.compile(r'/Users/|/home/')
TEMPLATE_EXTENSIONS = {".tmpl", ".template", ".j2"}


def validate(plugin_path: Path, report: Report) -> None:
    # Commands: check for @${CLAUDE_PLUGIN_ROOT} file injection
    cmd_dir = plugin_path / "commands"
    if cmd_dir.is_dir():
        for f in cmd_dir.glob("*.md"):
            content = f.read_text(encoding="utf-8")
            # Check for runtime Read of plugin files (anti-pattern)
            if "Read tool" in content and "${CLAUDE_PLUGIN_ROOT}" not in content:
                report.info("conventions.no_static_injection",
                            f"Command {f.name} may use runtime Read instead of @${{CLAUDE_PLUGIN_ROOT}}",
                            file=str(f.relative_to(plugin_path)))

    # Skills: description checks
    skills_dir = plugin_path / "skills"
    if skills_dir.is_dir():
        for d in skills_dir.iterdir():
            if not d.is_dir():
                continue
            skill_file = d / "SKILL.md"
            if not skill_file.exists():
                continue  # structure validator handles this
            content = skill_file.read_text(encoding="utf-8")

            # Extract description from frontmatter
            desc = _extract_frontmatter_field(content, "description")
            if not desc:
                report.warn("conventions.skill_no_description",
                            f"Skill {d.name} has no description in frontmatter", skill=d.name)
                continue

            if len(desc) > 1024:
                report.warn("conventions.skill_description_long",
                            f"Skill {d.name} description exceeds 1024 chars ({len(desc)})",
                            skill=d.name)

            if FIRST_PERSON_RE.search(desc):
                report.warn("conventions.skill_first_person",
                            f"Skill {d.name} description uses first/second person",
                            skill=d.name)

            # Keywords from directory name should appear in description
            keywords = d.name.replace("-", " ").split()
            missing = [k for k in keywords if k.lower() not in desc.lower()]
            if missing:
                report.info("conventions.skill_missing_keywords",
                            f"Skill {d.name} description missing keywords: {', '.join(missing)}",
                            skill=d.name)

    # Agents: required frontmatter fields
    agents_dir = plugin_path / "agents"
    if agents_dir.is_dir():
        for f in agents_dir.glob("*.md"):
            content = f.read_text(encoding="utf-8")
            for field in ("name", "description", "model", "tools"):
                if not _extract_frontmatter_field(content, field):
                    report.warn("conventions.agent_missing_field",
                                f"Agent {f.name} missing frontmatter field: {field}",
                                file=f.name, field=field)

    # Global: no hardcoded paths or secrets (skip templates)
    for f in plugin_path.rglob("*"):
        if not f.is_file() or f.suffix in TEMPLATE_EXTENSIONS:
            continue
        if ".git" in f.parts or "__pycache__" in f.parts:
            continue
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except (OSError, UnicodeDecodeError):
            continue

        rel = str(f.relative_to(plugin_path))

        if HARDCODED_PATH_RE.search(content):
            report.warn("conventions.hardcoded_path",
                        f"Hardcoded user path in {rel}", file=rel)

        if SECRET_PATTERNS.search(content) and f.suffix not in (".md", ".txt"):
            report.warn("conventions.possible_secret",
                        f"Possible secret pattern in {rel}", file=rel)


def _extract_frontmatter_field(content: str, field: str) -> str:
    """Extract a field value from YAML frontmatter (simple parser)."""
    if not content.startswith("---"):
        return ""
    end = content.find("---", 3)
    if end == -1:
        return ""
    fm = content[3:end]
    for line in fm.split("\n"):
        if line.strip().startswith(f"{field}:"):
            value = line.split(":", 1)[1].strip()
            if value == "|" or value == ">":
                # Multi-line value: collect indented lines
                lines = []
                idx = fm.find(line) + len(line) + 1
                for sub_line in fm[idx:].split("\n"):
                    if sub_line and (sub_line[0] == " " or sub_line[0] == "\t"):
                        lines.append(sub_line.strip())
                    else:
                        break
                return " ".join(lines)
            return value.strip('"').strip("'")
    return ""


if __name__ == "__main__":
    plugin_path = resolve_plugin_path()
    report = Report(str(plugin_path))
    validate(plugin_path, report)
    if "--json" in sys.argv:
        print(report.to_json())
    else:
        report.print_human()
    sys.exit(1 if report.has_errors else 0)
