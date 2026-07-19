"""Run safety-boundary golden evals.

This example checks local safety language around disabled Procore, model,
plugin, MCP, and tool execution.
"""

from pyprocore.evals import get_builtin_dataset, run_eval_suite


def main() -> None:
    """Run the bundled safety-boundary eval dataset."""
    result = run_eval_suite(get_builtin_dataset("golden_safety_boundaries_basic"))
    print(f"Safety-boundary eval passed: {result.passed}")
    for finding in result.findings:
        if finding.severity.value != "pass":
            print(f"- {finding.severity.value}: {finding.message}")


if __name__ == "__main__":
    main()
