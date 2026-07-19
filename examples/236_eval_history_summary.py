"""Summarize local deterministic eval history snapshots."""

from pyprocore.evals import (
    build_eval_history_markdown,
    build_eval_history_snapshot,
    run_builtin_eval_suites,
    summarize_eval_history,
)


def main() -> None:
    """Build and print a small in-memory history summary."""
    report = run_builtin_eval_suites(suite="submittal_workflow_golden")
    snapshot = build_eval_history_snapshot(report, label="local-submittal-check")
    summary = summarize_eval_history([snapshot])
    print(build_eval_history_markdown(summary))


if __name__ == "__main__":
    main()
