"""Build a JSON regression report from local deterministic eval results."""

from pyprocore.evals import (
    build_eval_baseline,
    build_regression_report_json,
    compare_eval_report_to_baseline,
    run_builtin_eval_suites,
)


def main() -> None:
    """Print a JSON regression report."""
    current = run_builtin_eval_suites(suite="ai_workflow_package_golden")
    baseline = build_eval_baseline(current, baseline_name="local-ai-workflow-baseline")
    result = compare_eval_report_to_baseline(current, baseline)
    print(build_regression_report_json(result))


if __name__ == "__main__":
    main()
