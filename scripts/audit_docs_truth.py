"""Audit documentation for release-status and agent-layer truth claims."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Finding:
    """One documentation truth-audit finding."""

    level: str
    path: Path
    message: str


FAIL_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"final release readiness", re.IGNORECASE),
        "Internal final-readiness wording should not appear in public docs.",
    ),
    (
        re.compile(r"local token warning", re.IGNORECASE),
        "Internal local token warning wording should not appear in public docs.",
    ),
    (
        re.compile(r"GitHub token limitation", re.IGNORECASE),
        "Internal GitHub token limitation wording should not appear in public docs.",
    ),
    (
        re.compile(r"2\.1\.0 release candidate", re.IGNORECASE),
        "`2.1.0` is already released, not a release candidate.",
    ),
    (
        re.compile(r"2\.1\.0 has not been published", re.IGNORECASE),
        "`2.1.0` has already been published.",
    ),
    (
        re.compile(r"GitHub release not yet created", re.IGNORECASE),
        "GitHub release status wording is stale or ambiguous.",
    ),
    (
        re.compile(r"not yet created", re.IGNORECASE),
        "Avoid internal release-state wording in public docs.",
    ),
    (
        re.compile(r"2\.2\.0 has been published", re.IGNORECASE),
        "`2.2.0` is prepared but not yet published.",
    ),
    (
        re.compile(r"2\.1\.0 includes Phase 7", re.IGNORECASE),
        "Phase 7 is prepared for `2.2.0`, not the published `2.1.0` package.",
    ),
    (
        re.compile(r"Phase 7 is planned", re.IGNORECASE),
        "Completed Phase 7 infrastructure should not be described as only planned.",
    ),
    (
        re.compile(r"\btool execution enabled\b", re.IGNORECASE),
        "Tool execution remains disabled.",
    ),
    (
        re.compile(r"\bMCP execution enabled\b", re.IGNORECASE),
        "The MCP adapter remains discovery-only.",
    ),
    (
        re.compile(r"Open Agent API complete", re.IGNORECASE),
        "Avoid overstating Open Agent API status.",
    ),
    (
        re.compile(r"live Procore verification complete", re.IGNORECASE),
        "Live Procore verification remains environment-specific.",
    ),
)

WARN_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"\brelease candidate\b", re.IGNORECASE),
        "Check whether release-candidate wording is current.",
    ),
)


def iter_docs_files() -> list[Path]:
    """Return documentation files included in the truth audit."""
    files = [PROJECT_ROOT / "README.md", PROJECT_ROOT / "CHANGELOG.md"]
    files.extend(sorted((PROJECT_ROOT / "docs").rglob("*.md")))
    files.append(PROJECT_ROOT / "examples" / "README.md")
    return [path for path in files if path.exists()]


def audit_file(path: Path) -> list[Finding]:
    """Audit one file and return findings."""
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    for pattern, message in FAIL_PATTERNS:
        if pattern.search(text):
            findings.append(Finding("FAIL", path, message))
    for pattern, message in WARN_PATTERNS:
        if pattern.search(text) and "release-candidate" not in text:
            findings.append(Finding("WARN", path, message))
    return findings


def audit_removed_internal_docs() -> list[Finding]:
    """Return findings for public docs that should not exist."""
    internal_public_docs = (PROJECT_ROOT / "docs" / "final-release-readiness.md",)
    return [
        Finding("FAIL", path, "Internal readiness report should not be tracked as public docs.")
        for path in internal_public_docs
        if path.exists()
    ]


def main() -> int:
    """Run the documentation truth audit."""
    findings = audit_removed_internal_docs()
    findings.extend(finding for path in iter_docs_files() for finding in audit_file(path))
    failures = [finding for finding in findings if finding.level == "FAIL"]
    warnings = [finding for finding in findings if finding.level == "WARN"]

    for finding in findings:
        relative_path = finding.path.relative_to(PROJECT_ROOT)
        print(f"{finding.level}: {relative_path}: {finding.message}")

    if not findings:
        print("PASS: Documentation truth audit found no stale release-status claims.")
    print(
        f"Docs truth audit summary: {len(failures)} failures, "
        f"{len(warnings)} warnings, {len(iter_docs_files())} files scanned."
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
