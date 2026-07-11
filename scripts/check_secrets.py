#!/usr/bin/env python3
"""Scan project files for likely committed secrets without printing values."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

SKIPPED_PARTS: Final[set[str]] = {
    ".git",
    ".venv",
    "site",
    "downloads",
    "logs",
    "pyprocore-runs",
    "webhook-events",
    "project-context",
    "ai-export",
    "__pycache__",
}
TEXT_SUFFIXES: Final[set[str]] = {
    ".cfg",
    ".css",
    ".dockerignore",
    ".env",
    ".example",
    ".gitignore",
    ".ini",
    ".json",
    ".md",
    ".py",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
SAFE_VALUE_MARKERS: Final[tuple[str, ...]] = (
    "your_",
    "your-",
    "example",
    "placeholder",
    "changeme",
    "change_me",
    "dummy",
    "fake",
    "test",
    "mock",
    "sample",
    "local",
    "redacted",
    "xxxx",
    "YOUR_CODE_HERE",
)
SECRET_KEYS: Final[tuple[str, ...]] = (
    "PROCORE_CLIENT_SECRET",
    "access_token",
    "refresh_token",
    "client_secret",
    "api_key",
)


@dataclass(frozen=True)
class SecretFinding:
    """A likely secret finding safe to print in terminal output."""

    path: Path
    line_number: int
    kind: str
    severity: str


def discover_files(root: Path) -> list[Path]:
    """Return tracked project files when git is available, otherwise local files."""
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return [
            path
            for path in root.rglob("*")
            if path.is_file() and _should_scan(path.relative_to(root))
        ]

    return [
        root / line
        for line in result.stdout.splitlines()
        if line.strip() and _should_scan(Path(line))
    ]


def scan_files(paths: list[Path], root: Path | None = None) -> list[SecretFinding]:
    """Scan files and return likely secret findings.

    Args:
        paths: Files to scan.
        root: Optional project root used to print relative paths.

    Returns:
        Findings that should fail the check.
    """
    findings: list[SecretFinding] = []
    base = root or Path.cwd()
    for path in paths:
        if not path.exists() or not path.is_file():
            continue
        relative_path = _relative_to(path, base)
        if not _should_scan(relative_path):
            continue
        if path.name == "token_store.json":
            findings.append(SecretFinding(relative_path, 1, "token_store.json", "fail"))
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        except OSError as exc:
            print(f"WARN: Could not read {relative_path}: {exc}")
            continue

        findings.extend(_scan_content(relative_path, content))
    return findings


def main(argv: list[str] | None = None) -> int:
    """Run the secret scanner CLI."""
    parser = argparse.ArgumentParser(description="Scan project files for likely secrets.")
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Optional file paths to scan. Defaults to tracked project files.",
    )
    args = parser.parse_args(argv)

    root = Path.cwd()
    paths = [path if path.is_absolute() else root / path for path in args.paths]
    if not paths:
        paths = discover_files(root)

    findings = scan_files(paths, root=root)
    if findings:
        print("FAIL: Likely committed secrets were found.")
        for finding in findings:
            print(
                "FAIL: "
                f"{finding.path}:{finding.line_number} "
                f"contains likely {finding.kind}. Value hidden."
            )
        print(
            "Secret check summary: "
            f"0 passed, 0 warnings, {len(findings)} failure"
            f"{'' if len(findings) == 1 else 's'}."
        )
        return 1

    print(f"PASS: Scanned {len(paths)} file{'' if len(paths) == 1 else 's'} for secrets.")
    print("Secret check summary: 1 passed, 0 warnings, 0 failures.")
    return 0


def _scan_content(path: Path, content: str) -> list[SecretFinding]:
    """Scan one text payload for likely secrets."""
    findings: list[SecretFinding] = []
    for line_number, line in enumerate(content.splitlines(), start=1):
        if "-----BEGIN" in line and "PRIVATE KEY-----" in line:
            findings.append(SecretFinding(path, line_number, "private key", "fail"))
            continue
        bearer_match = re.search(r"Authorization\s*:\s*Bearer\s+([A-Za-z0-9._~+/=-]+)", line)
        if bearer_match and _looks_real_secret(bearer_match.group(1)):
            findings.append(SecretFinding(path, line_number, "Authorization bearer token", "fail"))
            continue

        key_value = _extract_key_value(line)
        if key_value is None:
            continue
        key, value = key_value
        if key in SECRET_KEYS and _looks_real_secret(value):
            findings.append(SecretFinding(path, line_number, key, "fail"))
    return findings


def _extract_key_value(line: str) -> tuple[str, str] | None:
    """Extract simple env, JSON, YAML, or Python secret assignments."""
    env_match = re.search(
        r"\b([A-Z0-9_]*SECRET|PROCORE_CLIENT_SECRET)\s*=\s*['\"]?([^'\"\s#]+)", line
    )
    if env_match:
        return env_match.group(1), env_match.group(2)

    quoted_match = re.search(
        r"['\"](access_token|refresh_token|client_secret|api_key)['\"]\s*[:=]\s*['\"]([^'\"]+)['\"]",
        line,
        flags=re.IGNORECASE,
    )
    if quoted_match:
        return quoted_match.group(1).lower(), quoted_match.group(2)

    yaml_match = re.search(
        r"\b(access_token|refresh_token|client_secret|api_key)\s*:\s*['\"]?([^'\"\s#]+)",
        line,
        flags=re.IGNORECASE,
    )
    if yaml_match:
        return yaml_match.group(1).lower(), yaml_match.group(2)

    return None


def _looks_real_secret(value: str) -> bool:
    """Return whether a value looks more like a real secret than a placeholder."""
    cleaned = value.strip().strip(",")
    if len(cleaned) < 16:
        return False
    lowered = cleaned.lower()
    if any(marker.lower() in lowered for marker in SAFE_VALUE_MARKERS):
        return False
    if re.fullmatch(r"\{[^}]+\}", cleaned):
        return False
    if re.fullmatch(r"\$[{(]?[A-Z0-9_]+[})]?", cleaned):
        return False
    return bool(re.search(r"[A-Za-z]", cleaned) and re.search(r"[0-9]", cleaned))


def _should_scan(relative_path: Path) -> bool:
    """Return whether a relative file path should be scanned."""
    if any(part in SKIPPED_PARTS for part in relative_path.parts):
        return False
    if relative_path.suffix in TEXT_SUFFIXES:
        return True
    return relative_path.name in {
        ".dockerignore",
        ".gitignore",
        ".pre-commit-config.yaml",
        "Dockerfile",
        "Makefile",
    }


def _relative_to(path: Path, root: Path) -> Path:
    """Return path relative to root when possible."""
    try:
        return path.resolve().relative_to(root.resolve())
    except ValueError:
        return path


if __name__ == "__main__":
    raise SystemExit(main())
