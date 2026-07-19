"""Run a built-in offline model-response fixture eval suite.

This example does not call Procore, a model provider, plugins, MCP, or tools.
It evaluates static local sample responses with deterministic safety checks.
"""

from pyprocore.evals import run_builtin_eval_suites


def main() -> None:
    """Run the quickstart model-response fixture suite."""
    report = run_builtin_eval_suites(suite="model_fixture_rfi_review_golden")
    print("Offline model-response fixture eval complete.")
    print(f"Status: {report.status.value}")
    print(f"Score: {report.score}/{report.max_score}")


if __name__ == "__main__":
    main()
