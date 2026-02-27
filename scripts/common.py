#!/usr/bin/env python3
"""Shared severity model, JSON report schema, and path helpers for anvil validators."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

ANVIL_VERSION = "0.1.0"


@dataclass
class Finding:
    check_id: str
    severity: str  # ERROR, WARN, INFO
    message: str
    sources: dict[str, str] = field(default_factory=dict)


@dataclass
class Report:
    plugin_path: str
    findings: list[Finding] = field(default_factory=list)

    def add(self, check_id: str, severity: str, message: str, **sources: str) -> None:
        self.findings.append(Finding(check_id, severity, message, sources))

    def error(self, check_id: str, message: str, **sources: str) -> None:
        self.add(check_id, "ERROR", message, **sources)

    def warn(self, check_id: str, message: str, **sources: str) -> None:
        self.add(check_id, "WARN", message, **sources)

    def info(self, check_id: str, message: str, **sources: str) -> None:
        self.add(check_id, "INFO", message, **sources)

    @property
    def summary(self) -> dict[str, int]:
        counts = {"error": 0, "warn": 0, "info": 0}
        for f in self.findings:
            counts[f.severity.lower()] = counts.get(f.severity.lower(), 0) + 1
        return counts

    @property
    def has_errors(self) -> bool:
        return any(f.severity == "ERROR" for f in self.findings)

    def to_json(self) -> str:
        return json.dumps({
            "tool": "anvil",
            "version": ANVIL_VERSION,
            "plugin_path": self.plugin_path,
            "findings": [asdict(f) for f in self.findings],
            "summary": self.summary,
            "exit_code": 1 if self.has_errors else 0,
        }, indent=2)

    def print_human(self) -> None:
        if not self.findings:
            print("All checks passed.")
            return
        by_sev = {"ERROR": [], "WARN": [], "INFO": []}
        for f in self.findings:
            by_sev.setdefault(f.severity, []).append(f)
        for sev in ("ERROR", "WARN", "INFO"):
            items = by_sev.get(sev, [])
            if items:
                print(f"\n{'=' * 50}")
                print(f"  {sev} ({len(items)})")
                print(f"{'=' * 50}")
                for f in items:
                    src = ""
                    if f.sources:
                        src = " (" + ", ".join(f"{k}={v}" for k, v in f.sources.items()) + ")"
                    print(f"  [{f.check_id}] {f.message}{src}")
        s = self.summary
        print(f"\n{len(self.findings)} findings: {s['error']} error, {s['warn']} warn, {s['info']} info")


def resolve_plugin_path(argv: list[str] | None = None) -> Path:
    """Get plugin path from argv[1] or cwd."""
    args = argv if argv is not None else sys.argv
    if len(args) > 1:
        p = Path(args[1]).resolve()
        # Filter out flags like --json
        if not str(p).startswith("-"):
            return p
    return Path.cwd().resolve()


def load_json_file(path: Path) -> dict | list | None:
    """Load JSON file, return None if missing or malformed."""
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
