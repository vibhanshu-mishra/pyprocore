"""Build a local report for all offline model-response fixture suites."""

from pyprocore.evals import run_builtin_eval_suites

MODEL_FIXTURE_SUITES = [
    "model_fixture_rfi_review_golden",
    "model_fixture_submittal_review_golden",
    "model_fixture_project_context_qa_golden",
    "model_fixture_drawing_spec_comparison_golden",
    "model_fixture_engineering_assistant_golden",
    "model_fixture_field_issue_summary_golden",
    "model_fixture_change_risk_review_golden",
    "model_fixture_safety_boundaries_golden",
]


def main() -> None:
    """Run each model-response fixture suite and print a compact report."""
    for suite_name in MODEL_FIXTURE_SUITES:
        report = run_builtin_eval_suites(suite=suite_name)
        print(f"{suite_name}: {report.status.value} ({report.score}/{report.max_score})")


if __name__ == "__main__":
    main()
