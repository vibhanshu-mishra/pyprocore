"""Run the local AI workflow package golden eval suite.

The fixture checks prompt-package structure and safety language. It does not
call any AI provider or external model endpoint.
"""

from pyprocore.evals import run_builtin_eval_suites


def main() -> None:
    """Run AI workflow package evals and print a short summary."""
    report = run_builtin_eval_suites(suite="ai_workflow_package_golden")
    print("AI workflow package eval:")
    print(f"Status: {report.status.value}")
    print(f"Score: {report.score}/{report.max_score}")


if __name__ == "__main__":
    main()
