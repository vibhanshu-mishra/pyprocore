"""Apply default and strict threshold policies to local deterministic evals."""

from pyprocore.evals import (
    build_eval_baseline,
    compare_eval_report_to_baseline,
    default_eval_threshold_policy,
    run_builtin_eval_suites,
    strict_eval_threshold_policy,
)


def main() -> None:
    """Compare a suite with default and strict local threshold policies."""
    current = run_builtin_eval_suites(suite="safety_boundaries_golden")
    baseline = build_eval_baseline(current, baseline_name="local-safety-baseline")
    default_result = compare_eval_report_to_baseline(
        current,
        baseline,
        policy=default_eval_threshold_policy(),
    )
    strict_result = compare_eval_report_to_baseline(
        current,
        baseline,
        policy=strict_eval_threshold_policy(),
    )
    print(f"Default policy status: {default_result.status.value}")
    print(f"Strict policy status: {strict_result.status.value}")


if __name__ == "__main__":
    main()
