"""Run the local async export golden eval suite.

This checks deterministic export row and manifest shapes using placeholder
fixtures only. It never calls live services.
"""

from pyprocore.evals import run_builtin_eval_suites


def main() -> None:
    """Run async export evals and print the local result."""
    report = run_builtin_eval_suites(suite="async_export_golden")
    print("Async export eval:")
    print(f"Status: {report.status.value}")
    print(f"Score: {report.score}/{report.max_score}")


if __name__ == "__main__":
    main()
