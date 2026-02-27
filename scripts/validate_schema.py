#!/usr/bin/env python3
"""Validate plugin.json schema and CHANGELOG semver."""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import Report, resolve_plugin_path, load_json_file

SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
SLUG_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
CHANGELOG_VERSION_RE = re.compile(r"##\s*\[(\d+\.\d+\.\d+)\]")
REQUIRED_FIELDS = ["name", "version", "description", "author", "license"]


def validate(plugin_path: Path, report: Report) -> None:
    pj_path = plugin_path / ".claude-plugin" / "plugin.json"
    pj = load_json_file(pj_path)

    if pj is None:
        report.error("schema.no_manifest", "No .claude-plugin/plugin.json found")
        return

    # Required fields
    for field in REQUIRED_FIELDS:
        if field not in pj or pj[field] is None:
            report.error("schema.missing_field", f"plugin.json missing required field: {field}", field=field)

    # Name slug
    name = pj.get("name", "")
    if isinstance(name, str) and name and not SLUG_RE.match(name):
        report.error("schema.invalid_name", f"plugin.json name is not a valid slug: {name}", name=name)

    # Name matches directory
    if isinstance(name, str) and name and name != plugin_path.name:
        report.warn("schema.name_mismatch", "plugin.json name doesn't match directory name",
                     plugin_json=name, directory=plugin_path.name)

    # Version semver
    version = pj.get("version")
    if isinstance(version, str) and not SEMVER_RE.match(version):
        report.error("schema.invalid_version", f"plugin.json version is not valid semver: {version}")
    elif not isinstance(version, str) and version is not None:
        report.error("schema.version_type", f"plugin.json version is not a string: {type(version).__name__}")

    # CHANGELOG version alignment
    changelog_path = plugin_path / "CHANGELOG.md"
    if changelog_path.exists() and isinstance(version, str):
        text = changelog_path.read_text(encoding="utf-8")
        m = CHANGELOG_VERSION_RE.search(text)
        if m:
            cl_version = m.group(1)
            if cl_version != version:
                report.error("schema.version_drift", "plugin.json version doesn't match CHANGELOG",
                             plugin_json=version, changelog=cl_version)
        else:
            report.warn("schema.no_changelog_version", "CHANGELOG.md has no version entry")
    elif not changelog_path.exists():
        report.warn("schema.no_changelog", "No CHANGELOG.md found")


if __name__ == "__main__":
    plugin_path = resolve_plugin_path()
    report = Report(str(plugin_path))
    validate(plugin_path, report)
    if "--json" in sys.argv:
        print(report.to_json())
    else:
        report.print_human()
    sys.exit(1 if report.has_errors else 0)
