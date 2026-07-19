"""Regression comparison helpers for deterministic PyProcore eval reports."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from pyprocore.core.exceptions import ValidationError
from pyprocore.evals.baselines import (
    build_eval_baseline,
    load_eval_baseline_from_file,
    validate_local_eval_json_path,
)
from pyprocore.evals.models import (
    EvalBaseline,
    EvalBaselineCase,
    EvalBaselineSuite,
    EvalComparisonResult,
    EvalRegressionFinding,
    EvalRegressionResult,
    EvalRegressionSeverity,
    EvalReport,
    EvalScoreDelta,
    EvalStatus,
    EvalThresholdPolicy,
)
from pyprocore.evals.runner import run_builtin_eval_suites


def default_eval_threshold_policy() -> EvalThresholdPolicy:
    """Return the default local eval regression threshold policy."""
    return EvalThresholdPolicy()


def strict_eval_threshold_policy() -> EvalThresholdPolicy:
    """Return a strict policy intended for local release-candidate checks."""
    return EvalThresholdPolicy(
        minimum_score_ratio=1.0,
        allow_new_warnings=False,
        allow_new_failures=False,
        max_allowed_failures=0,
        max_allowed_warnings=0,
        fail_on_missing_suite=True,
        fail_on_missing_case=True,
        fail_on_score_drop=True,
        warning_on_new_suite=True,
        notes="Strict local deterministic regression policy.",
    )


def validate_eval_threshold_policy(policy: EvalThresholdPolicy) -> list[EvalRegressionFinding]:
    """Validate threshold policy values."""
    findings: list[EvalRegressionFinding] = []
    if policy.minimum_score_ratio is not None and not 0 <= policy.minimum_score_ratio <= 1:
        findings.append(
            EvalRegressionFinding(
                severity=EvalRegressionSeverity.FAILURE,
                message="minimum_score_ratio must be between 0.0 and 1.0.",
                check="threshold_policy",
            )
        )
    if policy.minimum_total_score is not None and policy.minimum_total_score < 0:
        findings.append(
            EvalRegressionFinding(
                severity=EvalRegressionSeverity.FAILURE,
                message="minimum_total_score must not be negative.",
                check="threshold_policy",
            )
        )
    if policy.max_allowed_failures < 0:
        findings.append(
            EvalRegressionFinding(
                severity=EvalRegressionSeverity.FAILURE,
                message="max_allowed_failures must not be negative.",
                check="threshold_policy",
            )
        )
    if policy.max_allowed_warnings is not None and policy.max_allowed_warnings < 0:
        findings.append(
            EvalRegressionFinding(
                severity=EvalRegressionSeverity.FAILURE,
                message="max_allowed_warnings must not be negative.",
                check="threshold_policy",
            )
        )
    return findings


def compare_eval_result_to_baseline(
    report: EvalReport,
    baseline: EvalBaseline,
    *,
    policy: EvalThresholdPolicy | None = None,
) -> EvalComparisonResult:
    """Compare a deterministic eval report to a local baseline."""
    regression = compare_eval_report_to_baseline(report, baseline, policy=policy)
    return EvalComparisonResult(regression=regression)


def compare_eval_report_to_baseline(
    report: EvalReport,
    baseline: EvalBaseline,
    *,
    policy: EvalThresholdPolicy | None = None,
) -> EvalRegressionResult:
    """Compare a deterministic eval report to a local baseline."""
    active_policy = policy or default_eval_threshold_policy()
    findings = detect_eval_regressions(report, baseline, policy=active_policy)
    findings.extend(apply_threshold_policy(report, baseline, active_policy))
    failed = any(finding.severity == EvalRegressionSeverity.FAILURE for finding in findings)
    warning = any(finding.severity == EvalRegressionSeverity.WARNING for finding in findings)
    status = EvalStatus.FAIL if failed else EvalStatus.WARNING if warning else EvalStatus.PASS
    if not findings:
        findings.append(
            EvalRegressionFinding(
                severity=EvalRegressionSeverity.PASS,
                message="Current deterministic eval report matches the baseline thresholds.",
                check="regression_summary",
            )
        )
    return EvalRegressionResult(
        generated_at=datetime.now(timezone.utc),
        passed=not failed,
        status=status,
        baseline_name=baseline.metadata.baseline_name,
        pyprocore_version=report.pyprocore_version,
        suite_count=report.total_suites,
        case_count=report.total_cases,
        score=report.score,
        max_score=report.max_score,
        baseline_score=baseline.metadata.total_score,
        baseline_max_score=baseline.metadata.max_score,
        findings=findings,
        threshold_policy=active_policy,
    )


def detect_eval_regressions(
    report: EvalReport,
    baseline: EvalBaseline,
    *,
    policy: EvalThresholdPolicy | None = None,
) -> list[EvalRegressionFinding]:
    """Detect deterministic regressions between current eval results and a baseline."""
    active_policy = policy or default_eval_threshold_policy()
    findings: list[EvalRegressionFinding] = []
    current_suites = {suite.suite_name: suite for suite in report.suites}
    baseline_suites = {suite.suite_name: suite for suite in baseline.suites}

    for suite_name, baseline_suite in baseline_suites.items():
        current_suite = current_suites.get(suite_name)
        if current_suite is None:
            findings.append(
                EvalRegressionFinding(
                    severity=(
                        EvalRegressionSeverity.FAILURE
                        if active_policy.fail_on_missing_suite
                        else EvalRegressionSeverity.WARNING
                    ),
                    message=f"Baseline suite is missing from current results: {suite_name}.",
                    suite_name=suite_name,
                    check="missing_suite",
                )
            )
            continue
        findings.extend(_compare_suite(current_suite, baseline_suite, policy=active_policy))

    for suite_name in sorted(set(current_suites) - set(baseline_suites)):
        severity = (
            EvalRegressionSeverity.WARNING
            if active_policy.warning_on_new_suite
            else EvalRegressionSeverity.INFO
        )
        findings.append(
            EvalRegressionFinding(
                severity=severity,
                message=(
                    "Current results include a new suite not present in baseline: " f"{suite_name}."
                ),
                suite_name=suite_name,
                check="new_suite",
            )
        )
    return findings


def apply_threshold_policy(
    report: EvalReport,
    baseline: EvalBaseline,
    policy: EvalThresholdPolicy,
) -> list[EvalRegressionFinding]:
    """Apply local score and count thresholds to an eval report."""
    findings = validate_eval_threshold_policy(policy)
    if findings:
        return findings
    results: list[EvalRegressionFinding] = []
    if policy.minimum_total_score is not None and report.score < policy.minimum_total_score:
        results.append(
            EvalRegressionFinding(
                severity=EvalRegressionSeverity.FAILURE,
                message=(
                    "Current eval score is below the configured minimum total score: "
                    f"{report.score} < {policy.minimum_total_score}."
                ),
                check="minimum_total_score",
            )
        )
    if policy.minimum_score_ratio is not None:
        ratio = report.score / report.max_score if report.max_score else 0.0
        if ratio < policy.minimum_score_ratio:
            results.append(
                EvalRegressionFinding(
                    severity=EvalRegressionSeverity.FAILURE,
                    message=(
                        "Current eval score ratio is below the configured minimum: "
                        f"{ratio:.3f} < {policy.minimum_score_ratio:.3f}."
                    ),
                    check="minimum_score_ratio",
                )
            )
    if not policy.allow_new_failures and report.failed_cases > baseline.metadata.fail_count:
        results.append(
            EvalRegressionFinding(
                severity=EvalRegressionSeverity.FAILURE,
                message="Current eval report has more failed cases than the baseline.",
                check="new_failures",
            )
        )
    if report.failed_cases > policy.max_allowed_failures:
        results.append(
            EvalRegressionFinding(
                severity=EvalRegressionSeverity.FAILURE,
                message=(
                    "Current eval report exceeds max_allowed_failures: "
                    f"{report.failed_cases} > {policy.max_allowed_failures}."
                ),
                check="max_allowed_failures",
            )
        )
    if not policy.allow_new_warnings and report.warnings > baseline.metadata.warning_count:
        results.append(
            EvalRegressionFinding(
                severity=EvalRegressionSeverity.FAILURE,
                message="Current eval report has more warnings than the baseline.",
                check="new_warnings",
            )
        )
    if policy.max_allowed_warnings is not None and report.warnings > policy.max_allowed_warnings:
        results.append(
            EvalRegressionFinding(
                severity=EvalRegressionSeverity.FAILURE,
                message=(
                    "Current eval report exceeds max_allowed_warnings: "
                    f"{report.warnings} > {policy.max_allowed_warnings}."
                ),
                check="max_allowed_warnings",
            )
        )
    return results


def summarize_eval_regressions(result: EvalRegressionResult) -> str:
    """Return a concise human-readable regression summary."""
    failures = sum(1 for item in result.findings if item.severity == EvalRegressionSeverity.FAILURE)
    warnings = sum(1 for item in result.findings if item.severity == EvalRegressionSeverity.WARNING)
    return "\n".join(
        [
            "PyProcore eval regression comparison.",
            f"Baseline: {result.baseline_name}",
            f"Status: {result.status.value}",
            f"Score: {result.score}/{result.max_score}",
            f"Baseline score: {result.baseline_score}/{result.baseline_max_score}",
            f"Failures: {failures}",
            f"Warnings: {warnings}",
            "Mode: local deterministic comparison only; no Procore, model, plugin, "
            "MCP, or tool execution.",
        ]
    )


def build_regression_report_json(result: EvalRegressionResult, *, pretty: bool = True) -> str:
    """Serialize a regression result to deterministic JSON text."""
    return json.dumps(
        result.model_dump(mode="json"),
        indent=2 if pretty else None,
        sort_keys=True,
    )


def build_regression_report_markdown(result: EvalRegressionResult) -> str:
    """Render a regression result as Markdown."""
    lines = [
        "# PyProcore Eval Regression Report",
        "",
        f"Status: `{result.status.value}`",
        f"Baseline: `{result.baseline_name}`",
        f"Mode: `{result.mode}`",
        f"Score: {result.score}/{result.max_score}",
        f"Baseline score: {result.baseline_score}/{result.baseline_max_score}",
        "",
        "| Severity | Suite | Case | Check | Message |",
        "| --- | --- | --- | --- | --- |",
    ]
    for finding in result.findings:
        lines.append(
            f"| `{finding.severity.value}` | `{finding.suite_name or ''}` | "
            f"`{finding.case_id or ''}` | `{finding.check or ''}` | "
            f"{finding.message} |"
        )
    lines.extend(
        [
            "",
            "Mode: local deterministic comparison only; no live Procore calls, "
            "model calls, plugin execution, MCP execution, or tool execution occurred.",
            "",
        ]
    )
    return "\n".join(lines)


def write_regression_report_json(
    result: EvalRegressionResult,
    output_path: Path | str,
    *,
    pretty: bool = True,
) -> Path:
    """Write a regression report JSON file to a safe local path."""
    path = validate_local_eval_json_path(output_path, must_exist=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_regression_report_json(result, pretty=pretty) + "\n", encoding="utf-8")
    return path


def write_regression_report_markdown(
    result: EvalRegressionResult,
    output_path: Path | str,
) -> Path:
    """Write a regression report Markdown file to a safe local path."""
    path = _validate_markdown_output_path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_regression_report_markdown(result), encoding="utf-8")
    return path


def compare_current_to_baseline_file(
    baseline_path: Path | str,
    *,
    suite: str | None = None,
    policy: EvalThresholdPolicy | None = None,
) -> EvalRegressionResult:
    """Run current built-in evals and compare them to a local baseline file."""
    baseline = load_eval_baseline_from_file(baseline_path)
    current = run_builtin_eval_suites(suite=suite)
    return compare_eval_report_to_baseline(current, baseline, policy=policy)


def _compare_suite(
    current_suite: object,
    baseline_suite: EvalBaselineSuite,
    *,
    policy: EvalThresholdPolicy,
) -> list[EvalRegressionFinding]:
    """Compare one current suite result to one baseline suite."""
    findings: list[EvalRegressionFinding] = []
    delta = EvalScoreDelta(
        baseline_score=baseline_suite.score,
        current_score=getattr(current_suite, "score"),
        baseline_max_score=baseline_suite.max_score,
        current_max_score=getattr(current_suite, "max_score"),
    )
    if policy.fail_on_score_drop and delta.current_score < delta.baseline_score:
        findings.append(
            EvalRegressionFinding(
                severity=EvalRegressionSeverity.FAILURE,
                message=f"Suite score decreased for {baseline_suite.suite_name}.",
                suite_name=baseline_suite.suite_name,
                check="suite_score_drop",
                score_delta=delta,
            )
        )
    if delta.current_max_score != delta.baseline_max_score:
        findings.append(
            EvalRegressionFinding(
                severity=EvalRegressionSeverity.WARNING,
                message=f"Suite max score changed for {baseline_suite.suite_name}.",
                suite_name=baseline_suite.suite_name,
                check="suite_max_score_changed",
                score_delta=delta,
            )
        )
    current_cases = {case.case_id: case for case in getattr(current_suite, "cases")}
    baseline_cases = {case.case_id: case for case in baseline_suite.cases}
    for case_id, baseline_case in baseline_cases.items():
        current_case = current_cases.get(case_id)
        if current_case is None:
            findings.append(
                EvalRegressionFinding(
                    severity=(
                        EvalRegressionSeverity.FAILURE
                        if policy.fail_on_missing_case
                        else EvalRegressionSeverity.WARNING
                    ),
                    message=f"Baseline case is missing from current results: {case_id}.",
                    suite_name=baseline_suite.suite_name,
                    case_id=case_id,
                    check="missing_case",
                )
            )
            continue
        findings.extend(_compare_case(current_case, baseline_case, baseline_suite.suite_name))
    for case_id in sorted(set(current_cases) - set(baseline_cases)):
        findings.append(
            EvalRegressionFinding(
                severity=EvalRegressionSeverity.INFO,
                message=f"Current suite includes a new case not present in baseline: {case_id}.",
                suite_name=baseline_suite.suite_name,
                case_id=case_id,
                check="new_case",
            )
        )
    return findings


def _compare_case(
    current_case: object,
    baseline_case: EvalBaselineCase,
    suite_name: str,
) -> list[EvalRegressionFinding]:
    """Compare one current case result to one baseline case."""
    findings: list[EvalRegressionFinding] = []
    delta = EvalScoreDelta(
        baseline_score=baseline_case.score,
        current_score=getattr(current_case, "score"),
        baseline_max_score=baseline_case.max_score,
        current_max_score=getattr(current_case, "max_score"),
    )
    current_status = getattr(current_case, "status")
    if baseline_case.status == EvalStatus.PASS and current_status == EvalStatus.FAIL:
        findings.append(
            EvalRegressionFinding(
                severity=EvalRegressionSeverity.FAILURE,
                message="Case changed from pass to fail.",
                suite_name=suite_name,
                case_id=baseline_case.case_id,
                check="case_pass_to_fail",
                score_delta=delta,
            )
        )
    if baseline_case.status == EvalStatus.PASS and current_status == EvalStatus.WARNING:
        findings.append(
            EvalRegressionFinding(
                severity=EvalRegressionSeverity.WARNING,
                message="Case changed from pass to warning.",
                suite_name=suite_name,
                case_id=baseline_case.case_id,
                check="case_pass_to_warning",
                score_delta=delta,
            )
        )
    if delta.current_score < delta.baseline_score:
        findings.append(
            EvalRegressionFinding(
                severity=EvalRegressionSeverity.FAILURE,
                message="Case score decreased.",
                suite_name=suite_name,
                case_id=baseline_case.case_id,
                check="case_score_drop",
                score_delta=delta,
            )
        )
    if delta.current_max_score != delta.baseline_max_score:
        findings.append(
            EvalRegressionFinding(
                severity=EvalRegressionSeverity.WARNING,
                message="Case max score changed.",
                suite_name=suite_name,
                case_id=baseline_case.case_id,
                check="case_max_score_changed",
                score_delta=delta,
            )
        )
    return findings


def _validate_markdown_output_path(path: Path | str) -> Path:
    """Validate a local Markdown report output path."""
    output_path = Path(path)
    path_text = str(output_path)
    if "://" in path_text or path_text.casefold().startswith(("http:", "https:")):
        raise ValidationError("Eval report output path must be local, not a URL.")
    if any(part == ".." for part in output_path.parts):
        raise ValidationError("Eval report output path must not contain path traversal.")
    if output_path.suffix != ".md":
        raise ValidationError("Eval report output path must end with .md.")
    return output_path


def sample_regression_result() -> EvalRegressionResult:
    """Return a safe sample regression result from built-in placeholder eval data."""
    report = run_builtin_eval_suites(suite="golden_export_rows_basic")
    baseline = build_eval_baseline(report, baseline_name="sample-regression-baseline")
    return compare_eval_report_to_baseline(report, baseline)
