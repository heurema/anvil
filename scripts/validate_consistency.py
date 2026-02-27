#!/usr/bin/env python3
"""Thin adapter: delegates to fabrica/scripts/check_consistency.py."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import Report, resolve_plugin_path

SEVERITY_MAP = {"CRITICAL": "ERROR", "HIGH": "ERROR", "MEDIUM": "WARN", "LOW": "INFO"}


def validate(plugin_path: Path, report: Report) -> None:
    # Detect fabrica root
    fabrica_root = os.environ.get("FABRICA_ROOT")
    if fabrica_root:
        fabrica_root = Path(fabrica_root)
    else:
        # Heuristic: parent of plugin dir in fabrica workspace
        fabrica_root = plugin_path.parent

    script = fabrica_root / "scripts" / "check_consistency.py"
    if not script.exists():
        report.info("consistency.no_script",
                    "fabrica/scripts/check_consistency.py not found — skipping cross-repo checks",
                    fabrica_root=str(fabrica_root))
        return

    # Run check_consistency.py with --json
    try:
        result = subprocess.run(
            [sys.executable, str(script), "--json"],
            capture_output=True, text=True, timeout=30,
            cwd=str(fabrica_root),
        )
    except subprocess.TimeoutExpired:
        report.warn("consistency.timeout", "check_consistency.py timed out (30s)")
        return
    except OSError as e:
        report.warn("consistency.exec_error", f"Failed to run check_consistency.py: {e}")
        return

    # Parse JSON output
    try:
        findings = json.loads(result.stdout)
    except json.JSONDecodeError:
        if result.returncode != 0:
            report.warn("consistency.parse_error",
                        "Could not parse check_consistency.py output",
                        stderr=result.stderr[:200] if result.stderr else "")
        return

    # Filter to findings relevant to this plugin
    plugin_name = plugin_path.name
    for f in findings:
        if f.get("plugin") != plugin_name:
            continue
        severity = SEVERITY_MAP.get(f.get("severity", ""), "INFO")
        report.add(
            f"consistency.{f.get('severity', 'unknown').lower()}",
            severity,
            f.get("message", "Unknown finding"),
            **f.get("sources", {}),
        )


if __name__ == "__main__":
    plugin_path = resolve_plugin_path()
    report = Report(str(plugin_path))
    validate(plugin_path, report)
    if "--json" in sys.argv:
        print(report.to_json())
    else:
        report.print_human()
    sys.exit(1 if report.has_errors else 0)
