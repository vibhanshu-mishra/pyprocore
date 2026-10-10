"""Assertions for narrowly scoped GitHub Actions pin updates."""

from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path

_PINNED_LINE = re.compile(r"^(\s*-?\s*uses:\s+)([^@\s]+)@([0-9a-f]{40})\s+#\s+(v[\w.-]+)\s*$")
_EXPECTED_PINS = {
    ".github/workflows/openqodex.yml": [
        (
            "actions/checkout",
            "3d3c42e5aac5ba805825da76410c181273ba90b1",
            "v7",
        ),
        (
            "openqodex/openqodex",
            "2f2fa9e48c1f62a6123997eb14111140d8e22a74",
            "v0",
        ),
    ],
    ".github/workflows/security-scans.yml": [
        (
            "actions/checkout",
            "3d3c42e5aac5ba805825da76410c181273ba90b1",
            "v7",
        ),
        (
            "gitleaks/gitleaks-action",
            "e0c47f4f8be36e29cdc102c57e68cb5cbf0e8d1e",
            "v3",
        ),
        (
            "actions/checkout",
            "3d3c42e5aac5ba805825da76410c181273ba90b1",
            "v7",
        ),
        (
            "actions/checkout",
            "3d3c42e5aac5ba805825da76410c181273ba90b1",
            "v7",
        ),
        (
            "aquasecurity/trivy-action",
            "ed142fd0673e97e23eac54620cfb913e5ce36c25",
            "v0.36.0",
        ),
    ],
}


def _normalize_pins(content: str) -> tuple[list[tuple[str, str, str]], str]:
    """Normalize SHA references to their documented tags for comparison."""
    actual_pins: list[tuple[str, str, str]] = []
    normalized_lines: list[str] = []
    for line in content.splitlines(keepends=True):
        match = _PINNED_LINE.match(line.rstrip("\r\n"))
        if match:
            prefix, action, sha, tag = match.groups()
            actual_pins.append((action, sha, tag))
            newline = "\r\n" if line.endswith("\r\n") else "\n"
            normalized_lines.append(f"{prefix}{action}@{tag}{newline}")
        else:
            normalized_lines.append(line)
    return actual_pins, "".join(normalized_lines)


def assert_workflow_changes_are_pin_only(
    test_case: unittest.TestCase,
    project_root: Path,
) -> None:
    """Require workflow diffs to contain only the expected full-SHA pins."""
    changed = subprocess.run(
        ["git", "diff", "--name-only", "HEAD", "--", ".github/workflows"],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )
    test_case.assertEqual(changed.returncode, 0, changed.stderr)
    test_case.assertLessEqual(set(changed.stdout.splitlines()), set(_EXPECTED_PINS))

    for relative_path, expected_pins in _EXPECTED_PINS.items():
        baseline = subprocess.run(
            ["git", "show", f"HEAD:{relative_path}"],
            cwd=project_root,
            check=False,
            capture_output=True,
            text=True,
        )
        test_case.assertEqual(baseline.returncode, 0, baseline.stderr)
        current_text = (project_root / relative_path).read_text(encoding="utf-8")
        actual_pins, normalized_current = _normalize_pins(current_text)
        _, normalized_baseline = _normalize_pins(baseline.stdout)

        test_case.assertEqual(actual_pins, expected_pins, relative_path)
        test_case.assertEqual(normalized_current, normalized_baseline, relative_path)
