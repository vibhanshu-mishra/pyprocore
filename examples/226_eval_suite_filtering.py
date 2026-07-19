"""List workflow-specific eval suites and run one by name.

Suite filtering is useful when you only changed one workflow area and want
quick local feedback.
"""

from pyprocore.evals import list_builtin_eval_suites, run_builtin_eval_suites


def main() -> None:
    """Show workflow suites and run one filtered suite."""
    workflow_suites = [
        suite.name for suite in list_builtin_eval_suites() if suite.name.endswith("_golden")
    ]
    print("Workflow-specific suites:")
    for suite_name in workflow_suites:
        print(f"- {suite_name}")

    report = run_builtin_eval_suites(suite="rfi_workflow_golden")
    print(f"\nFiltered run status: {report.status.value}")


if __name__ == "__main__":
    main()
