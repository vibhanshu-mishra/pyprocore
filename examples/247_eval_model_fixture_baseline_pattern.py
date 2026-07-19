"""Create an in-memory baseline for an offline model-response fixture suite."""

from pyprocore.evals import (
    build_eval_baseline,
    compare_eval_report_to_baseline,
    run_builtin_eval_suites,
)


def main() -> None:
    """Create and compare a local baseline without writing files."""
    report = run_builtin_eval_suites(suite="model_fixture_rfi_review_golden")
    baseline = build_eval_baseline(report, baseline_name="sample-model-fixture-baseline")
    comparison = compare_eval_report_to_baseline(report, baseline)
    print(f"Baseline: {baseline.metadata.baseline_name}")
    print(f"Regression check passed: {comparison.passed}")


if __name__ == "__main__":
    main()
