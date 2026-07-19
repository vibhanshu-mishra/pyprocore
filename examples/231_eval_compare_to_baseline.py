"""Compare current deterministic eval results to a local baseline.

This example builds the baseline in memory, so it is useful for learning the API.
"""

from pyprocore.evals import (
    build_eval_baseline,
    compare_eval_report_to_baseline,
    run_builtin_eval_suites,
    summarize_eval_regressions,
)


def main() -> None:
    """Compare one current suite to a matching baseline."""
    current = run_builtin_eval_suites(suite="async_export_golden")
    baseline = build_eval_baseline(current, baseline_name="local-async-export-baseline")
    result = compare_eval_report_to_baseline(current, baseline)
    print(summarize_eval_regressions(result))


if __name__ == "__main__":
    main()
