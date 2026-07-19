"""Use local deterministic eval baselines as a release-readiness pattern.

This pattern is local-only. It does not publish, call Procore, or call AI models.
"""

from pyprocore.evals import (
    build_eval_baseline,
    compare_eval_report_to_baseline,
    run_builtin_eval_suites,
    strict_eval_threshold_policy,
    summarize_eval_regressions,
)


def main() -> None:
    """Compare all built-in evals with a strict local threshold policy."""
    current = run_builtin_eval_suites()
    baseline = build_eval_baseline(current, baseline_name="local-release-readiness-baseline")
    result = compare_eval_report_to_baseline(
        current,
        baseline,
        policy=strict_eval_threshold_policy(),
    )
    print(summarize_eval_regressions(result))


if __name__ == "__main__":
    main()
