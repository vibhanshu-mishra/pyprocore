"""Run the local RFI workflow golden eval suite.

This example uses bundled placeholder fixtures only. It does not call Procore,
call AI models, execute plugins, execute MCP, or execute Procore tools.
"""

from pyprocore.evals import run_builtin_eval_suites


def main() -> None:
    """Run the RFI workflow suite and print a beginner-friendly summary."""
    report = run_builtin_eval_suites(suite="rfi_workflow_golden")
    print("RFI workflow eval:")
    print(f"Status: {report.status.value}")
    print(f"Cases passed: {report.passed_cases}/{report.total_cases}")


if __name__ == "__main__":
    main()
