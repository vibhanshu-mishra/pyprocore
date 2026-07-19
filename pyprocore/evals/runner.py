"""Local deterministic eval runner for PyProcore golden datasets."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path

from pyprocore.evals.builtin_datasets import (
    get_all_builtin_datasets,
    get_builtin_dataset,
    list_builtin_dataset_names,
)
from pyprocore.evals.datasets import load_golden_dataset_from_file, validate_golden_dataset
from pyprocore.evals.models import (
    EvalCaseResult,
    EvalFinding,
    EvalReport,
    EvalScore,
    EvalSeverity,
    EvalStatus,
    EvalSuite,
    EvalSuiteResult,
    GoldenDataset,
    GoldenDatasetCase,
)
from pyprocore.evals.scoring import (
    contains_text_score,
    does_not_contain_text_score,
    exact_match_score,
    forbidden_keys_score,
    json_serializable_score,
    manifest_integrity_score,
    redaction_score,
    required_keys_score,
    required_values_score,
    row_count_score,
    safety_boundary_score,
)
from pyprocore.evals.workflow_scoring import (
    allowed_capability_score,
    allowed_hook_type_score,
    expected_field_set_score,
    forbidden_phrase_score,
    manifest_status_score,
    no_mutation_instruction_score,
    no_secret_like_value_score,
    path_within_output_dir_score,
    placeholder_only_score,
    required_phrase_score,
)


def list_builtin_eval_suites() -> list[EvalSuite]:
    """Return metadata for all built-in deterministic eval suites."""
    suites: list[EvalSuite] = []
    for dataset in get_all_builtin_datasets():
        suites.append(
            EvalSuite(
                name=dataset.metadata.name,
                description=dataset.metadata.description,
                dataset_name=dataset.metadata.name,
                case_count=len(dataset.cases),
            )
        )
    return suites


def run_builtin_eval_suites(suite: str | None = None) -> EvalReport:
    """Run built-in deterministic eval suites.

    Args:
        suite: Optional built-in suite name.

    Returns:
        Eval report for one or all built-in suites.
    """
    datasets = [get_builtin_dataset(suite)] if suite else get_all_builtin_datasets()
    return build_eval_report([run_eval_suite(dataset) for dataset in datasets])


def run_eval_suite(dataset: GoldenDataset) -> EvalSuiteResult:
    """Run one local deterministic eval suite from a golden dataset."""
    validation_findings = validate_golden_dataset(dataset)
    validation_errors = [
        finding for finding in validation_findings if finding.severity == EvalSeverity.FAILURE
    ]
    if validation_errors:
        return _suite_result_from_validation_errors(dataset, validation_errors)
    case_results = [run_eval_case(case) for case in dataset.cases]
    return _build_suite_result(dataset, case_results)


def run_eval_case(case: GoldenDatasetCase) -> EvalCaseResult:
    """Run one deterministic eval case."""
    artifact = case.input.artifact
    expected = case.expected
    scores: list[EvalScore] = []
    if expected.exact is not None:
        scores.append(exact_match_score(artifact, expected.exact, case_id=case.id))
    if expected.required_keys:
        scores.append(required_keys_score(artifact, expected.required_keys, case_id=case.id))
    if expected.forbidden_keys:
        scores.append(forbidden_keys_score(artifact, expected.forbidden_keys, case_id=case.id))
    if expected.contains_text:
        scores.append(contains_text_score(artifact, expected.contains_text, case_id=case.id))
    if expected.does_not_contain_text:
        scores.append(
            does_not_contain_text_score(
                artifact,
                expected.does_not_contain_text,
                case_id=case.id,
            )
        )
    if expected.row_count is not None:
        scores.append(row_count_score(artifact, expected.row_count, case_id=case.id))
    if expected.required_values:
        scores.append(required_values_score(artifact, expected.required_values, case_id=case.id))
    if expected.json_serializable:
        scores.append(json_serializable_score(artifact, case_id=case.id))
    if expected.redaction_required:
        scores.append(redaction_score(artifact, case_id=case.id))
    if expected.manifest_required_keys:
        scores.append(
            manifest_integrity_score(
                artifact,
                expected.manifest_required_keys,
                case_id=case.id,
            )
        )
    if expected.expected_fields:
        scores.append(
            expected_field_set_score(
                artifact,
                expected.expected_fields,
                case_id=case.id,
            )
        )
    if expected.required_phrases:
        scores.append(required_phrase_score(artifact, expected.required_phrases, case_id=case.id))
    if expected.forbidden_phrases:
        scores.append(forbidden_phrase_score(artifact, expected.forbidden_phrases, case_id=case.id))
    if expected.output_dir and expected.output_paths:
        scores.append(
            path_within_output_dir_score(
                expected.output_dir,
                expected.output_paths,
                case_id=case.id,
            )
        )
    if expected.manifest_status:
        scores.append(manifest_status_score(artifact, expected.manifest_status, case_id=case.id))
    if expected.allowed_capabilities:
        scores.append(
            allowed_capability_score(
                artifact,
                expected.allowed_capabilities,
                case_id=case.id,
            )
        )
    if expected.allowed_hook_types:
        scores.append(
            allowed_hook_type_score(
                artifact,
                expected.allowed_hook_types,
                case_id=case.id,
            )
        )
    if expected.placeholder_only:
        scores.append(placeholder_only_score(artifact, case_id=case.id))
    if expected.no_mutation_instructions:
        scores.append(no_mutation_instruction_score(artifact, case_id=case.id))
    if expected.no_secret_like_values:
        scores.append(no_secret_like_value_score(artifact, case_id=case.id))
    scores.append(safety_boundary_score(artifact, case_id=case.id))
    return _case_result_from_scores(case, scores)


def run_golden_dataset_file(path: Path | str) -> EvalReport:
    """Load and run one local JSON golden dataset file."""
    return build_eval_report([run_eval_suite(load_golden_dataset_from_file(path))])


def build_eval_report(suites: Iterable[EvalSuiteResult]) -> EvalReport:
    """Build an aggregate deterministic eval report."""
    from pyprocore import __version__

    suite_list = list(suites)
    passed_suites = sum(1 for suite in suite_list if suite.passed)
    failed_suites = len(suite_list) - passed_suites
    total_cases = sum(suite.total_cases for suite in suite_list)
    passed_cases = sum(suite.passed_cases for suite in suite_list)
    failed_cases = sum(suite.failed_cases for suite in suite_list)
    warnings = sum(suite.warnings for suite in suite_list)
    score = sum(suite.score for suite in suite_list)
    max_score = sum(suite.max_score for suite in suite_list)
    status = EvalStatus.PASS if failed_suites == 0 else EvalStatus.FAIL
    if status == EvalStatus.PASS and warnings:
        status = EvalStatus.WARNING
    return EvalReport(
        generated_at=datetime.now(timezone.utc),
        pyprocore_version=__version__,
        status=status,
        passed=failed_suites == 0,
        total_suites=len(suite_list),
        passed_suites=passed_suites,
        failed_suites=failed_suites,
        total_cases=total_cases,
        passed_cases=passed_cases,
        failed_cases=failed_cases,
        warnings=warnings,
        score=score,
        max_score=max_score,
        suites=suite_list,
    )


def sample_eval_report() -> EvalReport:
    """Return a deterministic sample report from built-in placeholder datasets."""
    return run_builtin_eval_suites(suite=list_builtin_dataset_names()[0])


def evaluate_export_rows_case(case: GoldenDatasetCase) -> EvalCaseResult:
    """Evaluate one export-rows case."""
    return run_eval_case(case)


def evaluate_agent_manifest_case(case: GoldenDatasetCase) -> EvalCaseResult:
    """Evaluate one agent-manifest case."""
    return run_eval_case(case)


def evaluate_ai_workflow_package_case(case: GoldenDatasetCase) -> EvalCaseResult:
    """Evaluate one AI-workflow-package case."""
    return run_eval_case(case)


def evaluate_async_batch_plan_case(case: GoldenDatasetCase) -> EvalCaseResult:
    """Evaluate one async-batch-plan case."""
    return run_eval_case(case)


def evaluate_plugin_manifest_case(case: GoldenDatasetCase) -> EvalCaseResult:
    """Evaluate one plugin-manifest case."""
    return run_eval_case(case)


def evaluate_plugin_config_case(case: GoldenDatasetCase) -> EvalCaseResult:
    """Evaluate one plugin-config case."""
    return run_eval_case(case)


def evaluate_safety_boundary_case(case: GoldenDatasetCase) -> EvalCaseResult:
    """Evaluate one safety-boundary case."""
    return run_eval_case(case)


def _case_result_from_scores(
    case: GoldenDatasetCase,
    scores: list[EvalScore],
) -> EvalCaseResult:
    """Build one case result from deterministic scores."""
    score = sum(item.points for item in scores)
    max_score = sum(item.max_points for item in scores)
    findings = [finding for item in scores for finding in item.findings]
    failed = any(not item.passed for item in scores)
    warnings = any(finding.severity == EvalSeverity.WARNING for finding in findings)
    status = EvalStatus.FAIL if failed else EvalStatus.WARNING if warnings else EvalStatus.PASS
    return EvalCaseResult(
        case_id=case.id,
        case_type=case.case_type,
        status=status,
        passed=not failed,
        score=score,
        max_score=max_score,
        findings=findings,
    )


def _build_suite_result(
    dataset: GoldenDataset,
    cases: list[EvalCaseResult],
) -> EvalSuiteResult:
    """Build one suite result from case results."""
    findings = [finding for case in cases for finding in case.findings]
    failed_cases = sum(1 for case in cases if not case.passed)
    warning_count = sum(1 for finding in findings if finding.severity == EvalSeverity.WARNING)
    status = (
        EvalStatus.FAIL
        if failed_cases
        else EvalStatus.WARNING if warning_count else EvalStatus.PASS
    )
    return EvalSuiteResult(
        suite_name=dataset.metadata.name,
        dataset_name=dataset.metadata.name,
        status=status,
        passed=failed_cases == 0,
        total_cases=len(cases),
        passed_cases=len(cases) - failed_cases,
        failed_cases=failed_cases,
        warnings=warning_count,
        score=sum(case.score for case in cases),
        max_score=sum(case.max_score for case in cases),
        findings=findings,
        cases=cases,
    )


def _suite_result_from_validation_errors(
    dataset: GoldenDataset,
    findings: list[EvalFinding],
) -> EvalSuiteResult:
    """Build a failed suite result from dataset validation errors."""
    return EvalSuiteResult(
        suite_name=dataset.metadata.name,
        dataset_name=dataset.metadata.name,
        status=EvalStatus.FAIL,
        passed=False,
        total_cases=len(dataset.cases),
        passed_cases=0,
        failed_cases=len(dataset.cases),
        warnings=0,
        score=0,
        max_score=max(1, len(dataset.cases)),
        findings=findings,
        cases=[],
    )
