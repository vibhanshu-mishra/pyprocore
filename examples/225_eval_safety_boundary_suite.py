"""Run the local safety-boundary golden eval suite.

This confirms the fixture-level boundaries for tool execution, MCP execution,
plugin execution, model calls, and remote dataset fetching remain disabled.
"""

from pyprocore.evals import run_builtin_eval_suites


def main() -> None:
    """Run safety-boundary evals and print the local result."""
    report = run_builtin_eval_suites(suite="safety_boundaries_golden")
    print("Safety-boundary eval:")
    print(f"Status: {report.status.value}")
    print(f"Cases passed: {report.passed_cases}/{report.total_cases}")


if __name__ == "__main__":
    main()
