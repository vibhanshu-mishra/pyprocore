"""Run local release-readiness checks for PyProcore.

The script performs static local checks only. It does not publish packages,
contact PyPI, call Procore, run Docker, or require network access.
"""

from __future__ import annotations

import importlib
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = [
    "pyproject.toml",
    "README.md",
    "CHANGELOG.md",
    "LICENSE",
    ".gitignore",
    ".dockerignore",
]
REQUIRED_METADATA = [
    "name",
    "version",
    "description",
    "readme",
    "requires-python",
    "license",
    "authors",
    "keywords",
    "classifiers",
    "dependencies",
    "urls",
]
REQUIRED_URLS = ["Homepage", "Repository", "Issues", "Changelog", "Documentation"]
SECRET_PATHS = [
    ".env",
    "token_store.json",
    "pyprocore/auth/token_store.json",
]


@dataclass(frozen=True)
class CheckResult:
    """One release-readiness check result."""

    status: str
    message: str


def main() -> int:
    """Run release-readiness checks and return an operating-system exit code."""
    results = run_checks()
    for result in results:
        print(f"{result.status}: {result.message}")

    failures = [result for result in results if result.status == "FAIL"]
    warnings = [result for result in results if result.status == "WARN"]
    print()
    print(
        f"Release readiness summary: "
        f"{len(results) - len(failures) - len(warnings)} passed, "
        f"{len(warnings)} warnings, {len(failures)} failures."
    )
    return 1 if failures else 0


def run_checks() -> list[CheckResult]:
    """Return all release-readiness check results."""
    results: list[CheckResult] = []
    results.extend(check_required_files())
    pyproject = load_pyproject(results)
    if pyproject is not None:
        results.extend(check_metadata(pyproject))
    results.extend(check_license())
    results.extend(check_imports())
    results.extend(check_project_folders())
    results.extend(check_secret_files())
    return results


def check_required_files() -> list[CheckResult]:
    """Check that release-critical files exist."""
    results: list[CheckResult] = []
    for relative_path in REQUIRED_FILES:
        path = PROJECT_ROOT / relative_path
        if path.exists():
            results.append(CheckResult("PASS", f"{relative_path} exists."))
        else:
            results.append(CheckResult("FAIL", f"{relative_path} is missing."))
    return results


def load_pyproject(results: list[CheckResult]) -> dict[str, Any] | None:
    """Load pyproject.toml and append a check result."""
    path = PROJECT_ROOT / "pyproject.toml"
    try:
        payload = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except tomllib.TOMLDecodeError as exc:
        results.append(CheckResult("FAIL", f"pyproject.toml is invalid TOML: {exc}"))
        return None
    results.append(CheckResult("PASS", "pyproject.toml parses successfully."))
    return payload


def check_metadata(pyproject: dict[str, Any]) -> list[CheckResult]:
    """Check required package metadata fields."""
    project = pyproject.get("project")
    if not isinstance(project, dict):
        return [CheckResult("FAIL", "pyproject.toml is missing [project] metadata.")]

    results: list[CheckResult] = []
    for field in REQUIRED_METADATA:
        value = project.get(field)
        if value:
            results.append(CheckResult("PASS", f"pyproject metadata has {field}."))
        else:
            results.append(CheckResult("FAIL", f"pyproject metadata is missing {field}."))

    urls = project.get("urls")
    if isinstance(urls, dict):
        for url_name in REQUIRED_URLS:
            if urls.get(url_name):
                results.append(CheckResult("PASS", f"project URL exists: {url_name}."))
            else:
                results.append(CheckResult("WARN", f"project URL is missing: {url_name}."))

    classifiers = project.get("classifiers", [])
    if isinstance(classifiers, list) and any("Typing :: Typed" == item for item in classifiers):
        results.append(CheckResult("PASS", "package declares typed support."))
    else:
        results.append(CheckResult("WARN", "package does not declare Typing :: Typed."))

    return results


def check_license() -> list[CheckResult]:
    """Check license file status."""
    path = PROJECT_ROOT / "LICENSE"
    if path.exists():
        return [CheckResult("PASS", "LICENSE file exists.")]
    return [
        CheckResult("WARN", "LICENSE file is missing; confirm license metadata before release.")
    ]


def check_imports() -> list[CheckResult]:
    """Check package and CLI imports without running CLI commands."""
    sys.path.insert(0, str(PROJECT_ROOT))
    results: list[CheckResult] = []
    for module_name in ["pyprocore", "pyprocore.app"]:
        try:
            importlib.import_module(module_name)
        except Exception as exc:  # pragma: no cover - defensive release diagnostics
            results.append(CheckResult("FAIL", f"Could not import {module_name}: {exc}"))
        else:
            results.append(CheckResult("PASS", f"Imported {module_name}."))
    return results


def check_project_folders() -> list[CheckResult]:
    """Check docs, examples, tests, and source folders."""
    results: list[CheckResult] = []
    for relative_path in ["pyprocore", "tests", "examples", "docs", "scripts"]:
        path = PROJECT_ROOT / relative_path
        if path.exists() and path.is_dir():
            results.append(CheckResult("PASS", f"{relative_path}/ exists."))
        else:
            results.append(CheckResult("FAIL", f"{relative_path}/ is missing."))
    return results


def check_secret_files() -> list[CheckResult]:
    """Warn about local secret files and fail if they are tracked by git."""
    tracked_files = tracked_git_files()
    results: list[CheckResult] = []
    for relative_path in SECRET_PATHS:
        path = PROJECT_ROOT / relative_path
        if relative_path in tracked_files:
            results.append(CheckResult("FAIL", f"Secret-like file is tracked: {relative_path}."))
        elif path.exists():
            results.append(CheckResult("WARN", f"Local secret-like file exists: {relative_path}."))
        else:
            results.append(
                CheckResult("PASS", f"Secret-like file absent from checkout: {relative_path}.")
            )
    return results


def tracked_git_files() -> set[str]:
    """Return git-tracked files when git metadata is available."""
    try:
        completed = subprocess.run(
            ["git", "ls-files"],
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return set()
    if completed.returncode != 0:
        return set()
    return {line.strip() for line in completed.stdout.splitlines() if line.strip()}


if __name__ == "__main__":
    raise SystemExit(main())
