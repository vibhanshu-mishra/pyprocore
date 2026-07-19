"""Run the local async batch golden eval suite.

The suite validates dry-run batch plan and manifest fixtures without making
network requests or writing project exports.
"""

from pyprocore.evals import run_builtin_eval_suites


def main() -> None:
    """Run async batch evals and print the local result."""
    report = run_builtin_eval_suites(suite="async_batch_golden")
    print("Async batch eval:")
    print(f"Status: {report.status.value}")
    print(f"Cases passed: {report.passed_cases}/{report.total_cases}")


if __name__ == "__main__":
    main()
