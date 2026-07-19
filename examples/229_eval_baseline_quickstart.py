"""Create a safe local eval baseline from built-in deterministic fixtures.

This example does not call Procore, models, plugins, MCP servers, or tools.
It only snapshots local eval results into an in-memory baseline object.
"""

from pyprocore.evals import baseline_to_summary, build_eval_baseline, run_builtin_eval_suites


def main() -> None:
    """Run the baseline quickstart example."""
    report = run_builtin_eval_suites(suite="rfi_workflow_golden")
    baseline = build_eval_baseline(report, baseline_name="local-rfi-workflow-baseline")
    print(baseline_to_summary(baseline))


if __name__ == "__main__":
    main()
