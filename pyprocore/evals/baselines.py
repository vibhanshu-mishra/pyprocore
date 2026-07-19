"""Local baseline helpers for deterministic PyProcore eval reports."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from pyprocore.core.exceptions import ValidationError
from pyprocore.evals.models import (
    EvalBaseline,
    EvalBaselineCase,
    EvalBaselineMetadata,
    EvalBaselineSuite,
    EvalFinding,
    EvalReport,
    EvalSeverity,
)
from pyprocore.evals.runner import sample_eval_report
from pyprocore.evals.scoring import SECRET_LIKE_KEYS

BASELINE_SCHEMA_VERSION = "1"
UNSAFE_BASELINE_SUFFIXES = {".py", ".sh", ".ps1", ".command", ".bat", ".exe"}


def build_eval_baseline(
    report: EvalReport,
    *,
    baseline_name: str = "pyprocore-local-baseline",
    notes: str | None = None,
) -> EvalBaseline:
    """Build a local deterministic baseline from an eval report.

    Args:
        report: Eval report to snapshot.
        baseline_name: Human-readable baseline name.
        notes: Optional maintainer notes.

    Returns:
        JSON-serializable baseline.
    """
    suites = [_suite_to_baseline(suite) for suite in report.suites]
    metadata = EvalBaselineMetadata(
        baseline_name=_redact_secret_text(baseline_name),
        created_at=datetime.now(timezone.utc),
        pyprocore_version=report.pyprocore_version,
        suite_count=report.total_suites,
        case_count=report.total_cases,
        total_score=report.score,
        max_score=report.max_score,
        pass_count=report.passed_cases,
        fail_count=report.failed_cases,
        warning_count=report.warnings,
        notes=_redact_secret_text(notes) if notes else None,
    )
    return EvalBaseline(metadata=metadata, suites=suites)


def build_eval_baseline_from_report(
    report: EvalReport,
    *,
    baseline_name: str = "pyprocore-local-baseline",
    notes: str | None = None,
) -> EvalBaseline:
    """Build a local deterministic baseline from an eval report."""
    return build_eval_baseline(report, baseline_name=baseline_name, notes=notes)


def load_eval_baseline_from_dict(data: dict[str, Any]) -> EvalBaseline:
    """Load and validate an eval baseline from a dictionary.

    Args:
        data: JSON-like dictionary.

    Raises:
        ValidationError: If the baseline shape or safety checks fail.

    Returns:
        Validated eval baseline.
    """
    try:
        baseline = EvalBaseline.model_validate(data)
    except PydanticValidationError as exc:
        raise ValidationError(f"Invalid eval baseline: {_redact_secret_text(str(exc))}") from exc
    findings = validate_eval_baseline(baseline)
    errors = [finding for finding in findings if finding.severity == EvalSeverity.FAILURE]
    if errors:
        messages = "; ".join(_redact_secret_text(finding.message) for finding in errors)
        raise ValidationError(f"Invalid eval baseline: {messages}")
    return baseline


def load_eval_baseline_from_file(path: Path | str) -> EvalBaseline:
    """Load and validate a local JSON eval baseline file."""
    baseline_path = validate_local_eval_json_path(path, must_exist=True)
    try:
        data = json.loads(baseline_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Invalid JSON eval baseline: {baseline_path}") from exc
    if not isinstance(data, dict):
        raise ValidationError("Eval baseline JSON must be an object.")
    return load_eval_baseline_from_dict(data)


def validate_eval_baseline(baseline: EvalBaseline) -> list[EvalFinding]:
    """Validate one local deterministic eval baseline."""
    findings: list[EvalFinding] = []
    if baseline.schema_version != BASELINE_SCHEMA_VERSION:
        findings.append(
            EvalFinding(
                severity=EvalSeverity.FAILURE,
                message=f"Unsupported eval baseline schema version: {baseline.schema_version}.",
                check="baseline_schema",
            )
        )
    if not baseline.suites:
        findings.append(
            EvalFinding(
                severity=EvalSeverity.FAILURE,
                message="Eval baseline must contain at least one suite.",
                check="baseline_suites",
            )
        )
    seen_suites: set[str] = set()
    for suite in baseline.suites:
        if suite.suite_name in seen_suites:
            findings.append(
                EvalFinding(
                    severity=EvalSeverity.FAILURE,
                    message=f"Duplicate baseline suite: {suite.suite_name}.",
                    check="baseline_suites",
                )
            )
        seen_suites.add(suite.suite_name)
        seen_cases: set[str] = set()
        for case in suite.cases:
            if case.case_id in seen_cases:
                findings.append(
                    EvalFinding(
                        severity=EvalSeverity.FAILURE,
                        message=f"Duplicate baseline case: {case.case_id}.",
                        case_id=case.case_id,
                        check="baseline_cases",
                    )
                )
            seen_cases.add(case.case_id)
    _scan_baseline_for_secrets(baseline, findings)
    return findings or [
        EvalFinding(
            severity=EvalSeverity.PASS,
            message="Eval baseline is valid for local deterministic comparison.",
            check="baseline_validation",
        )
    ]


def write_eval_baseline_json(
    baseline: EvalBaseline,
    output_path: Path | str,
    *,
    pretty: bool = True,
) -> Path:
    """Write an eval baseline to a safe local JSON path."""
    path = validate_local_eval_json_path(output_path, must_exist=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(eval_baseline_to_json(baseline, pretty=pretty) + "\n", encoding="utf-8")
    return path


def eval_baseline_to_json(baseline: EvalBaseline, *, pretty: bool = True) -> str:
    """Serialize an eval baseline to deterministic JSON text."""
    return json.dumps(
        baseline.model_dump(mode="json"),
        indent=2 if pretty else None,
        sort_keys=True,
    )


def baseline_to_summary(baseline: EvalBaseline) -> str:
    """Return a concise human-readable baseline summary."""
    metadata = baseline.metadata
    return "\n".join(
        [
            "PyProcore eval baseline.",
            f"Name: {metadata.baseline_name}",
            f"Mode: {metadata.mode}",
            f"Suites: {metadata.suite_count}",
            f"Cases: {metadata.case_count}",
            f"Score: {metadata.total_score}/{metadata.max_score}",
            f"Failures: {metadata.fail_count}",
            f"Warnings: {metadata.warning_count}",
            "Local deterministic artifact only; no Procore, model, plugin, MCP, or tool execution.",
        ]
    )


def sample_eval_baseline() -> EvalBaseline:
    """Return a safe sample baseline from built-in placeholder eval data."""
    return build_eval_baseline(sample_eval_report(), baseline_name="sample-eval-baseline")


def validate_local_eval_json_path(path: Path | str, *, must_exist: bool) -> Path:
    """Validate a local JSON eval artifact path.

    Args:
        path: Path to validate.
        must_exist: Whether the file must already exist.

    Raises:
        ValidationError: If the path is remote, traverses upward, is executable, or invalid.

    Returns:
        Validated local path.
    """
    eval_path = Path(path)
    path_text = str(eval_path)
    if "://" in path_text or path_text.casefold().startswith(("http:", "https:")):
        raise ValidationError("Eval artifact path must be local, not a URL.")
    if any(part == ".." for part in eval_path.parts):
        raise ValidationError("Eval artifact path must not contain path traversal.")
    if eval_path.suffix in UNSAFE_BASELINE_SUFFIXES:
        raise ValidationError("Eval artifact path must not point to an executable file.")
    if eval_path.suffix != ".json":
        raise ValidationError("Eval artifact path must end with .json.")
    if must_exist and not eval_path.exists():
        raise ValidationError(f"Eval artifact file not found: {eval_path}")
    return eval_path


def _suite_to_baseline(suite: Any) -> EvalBaselineSuite:
    """Convert one eval suite result into a baseline suite."""
    cases = [_case_to_baseline(case) for case in suite.cases]
    return EvalBaselineSuite(
        suite_name=suite.suite_name,
        dataset_name=suite.dataset_name,
        status=suite.status,
        passed=suite.passed,
        total_cases=suite.total_cases,
        passed_cases=suite.passed_cases,
        failed_cases=suite.failed_cases,
        warnings=suite.warnings,
        score=suite.score,
        max_score=suite.max_score,
        cases=cases,
    )


def _case_to_baseline(case: Any) -> EvalBaselineCase:
    """Convert one eval case result into a baseline case."""
    warnings = sum(1 for finding in case.findings if finding.severity == EvalSeverity.WARNING)
    failures = sum(1 for finding in case.findings if finding.severity == EvalSeverity.FAILURE)
    messages = [_redact_secret_text(finding.message) for finding in case.findings[:20]]
    return EvalBaselineCase(
        case_id=case.case_id,
        case_type=case.case_type,
        status=case.status,
        passed=case.passed,
        score=case.score,
        max_score=case.max_score,
        finding_count=len(case.findings),
        warning_count=warnings,
        failure_count=failures,
        finding_messages=messages,
    )


def _scan_baseline_for_secrets(baseline: EvalBaseline, findings: list[EvalFinding]) -> None:
    """Append validation findings for raw secret-like baseline text."""
    text = json.dumps(baseline.model_dump(mode="json"), sort_keys=True).casefold()
    present = [key for key in SECRET_LIKE_KEYS if key in text]
    if present:
        findings.append(
            EvalFinding(
                severity=EvalSeverity.FAILURE,
                message="Eval baseline contains secret-like text: [REDACTED].",
                check="baseline_redaction",
            )
        )


def _redact_secret_text(value: str) -> str:
    """Redact secret-like fragments from local eval metadata."""
    result = value
    for key in SECRET_LIKE_KEYS:
        result = result.replace(key, "[REDACTED]")
        result = result.replace(key.upper(), "[REDACTED]")
    return result
