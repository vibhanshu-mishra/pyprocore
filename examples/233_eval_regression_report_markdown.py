"""Build a Markdown regression report from local deterministic eval results."""

from pyprocore.evals import (
    build_eval_baseline,
    build_regression_report_markdown,
    compare_eval_report_to_baseline,
    run_builtin_eval_suites,
)


def main() -> None:
    """Print a Markdown regression report."""
    current = run_builtin_eval_suites(suite="plugin_metadata_golden")
    baseline = build_eval_baseline(current, baseline_name="local-plugin-metadata-baseline")
    result = compare_eval_report_to_baseline(current, baseline)
    print(build_regression_report_markdown(result))


if __name__ == "__main__":
    main()
