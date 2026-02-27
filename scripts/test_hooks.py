#!/usr/bin/env python3
"""Fixture-driven hook test runner."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import resolve_plugin_path, load_json_file

DEFAULT_TIMEOUT = 10


def discover_fixtures(plugin_path: Path) -> list[Path]:
    """Find all fixtures/hooks/*/case.json in the plugin."""
    fixtures_dir = plugin_path / "fixtures" / "hooks"
    if not fixtures_dir.is_dir():
        return []
    return sorted(fixtures_dir.glob("*/case.json"))


def run_case(plugin_path: Path, case_path: Path) -> tuple[bool, str]:
    """Run a single test case. Returns (passed, message)."""
    case = load_json_file(case_path)
    if case is None:
        return False, "Failed to load case.json"

    name = case.get("name", case_path.parent.name)
    hook_script = case.get("hook_script", "")
    event = case.get("event", {})
    expected = case.get("expected", {})
    timeout = case.get("timeout_seconds", DEFAULT_TIMEOUT)
    case_env = case.get("env", {})

    # Resolve hook script path
    script_path = plugin_path / hook_script
    if not script_path.exists():
        return False, f"{name}: hook_script not found: {hook_script}"
    if not os.access(script_path, os.X_OK):
        return False, f"{name}: hook_script not executable: {hook_script}"

    # Build environment
    env = os.environ.copy()
    env["CLAUDE_PLUGIN_ROOT"] = str(plugin_path)
    env.update(case_env)

    # Run: pipe event JSON to stdin
    try:
        result = subprocess.run(
            [str(script_path)],
            input=json.dumps(event),
            capture_output=True, text=True,
            timeout=timeout, env=env,
        )
    except subprocess.TimeoutExpired:
        return False, f"{name}: timed out after {timeout}s"
    except OSError as e:
        return False, f"{name}: execution error: {e}"

    # Assert exit code
    exp_code = expected.get("exit_code")
    if exp_code is not None and result.returncode != exp_code:
        return False, f"{name}: exit_code expected {exp_code}, got {result.returncode}"

    # Assert stdout/stderr patterns
    for field, stream in [("stdout_contains", result.stdout), ("stderr_contains", result.stderr)]:
        for pattern in expected.get(field, []):
            if pattern not in stream:
                return False, f"{name}: {field} — '{pattern}' not found"

    for field, stream in [("stdout_not_contains", result.stdout), ("stderr_not_contains", result.stderr)]:
        for pattern in expected.get(field, []):
            if pattern in stream:
                return False, f"{name}: {field} — '{pattern}' unexpectedly found"

    return True, f"{name}: PASS"


def main() -> int:
    plugin_path = resolve_plugin_path()
    fixtures = discover_fixtures(plugin_path)

    if not fixtures:
        print("No hook test fixtures found.")
        return 0

    passed = 0
    failed = 0
    for case_path in fixtures:
        ok, msg = run_case(plugin_path, case_path)
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {msg}")
        if ok:
            passed += 1
        else:
            failed += 1

    print(f"\n{passed + failed} tests: {passed} passed, {failed} failed")
    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
