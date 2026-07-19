"""Evaluate placeholder agent manifest metadata.

This checks deterministic structure and disabled execution flags. It does not
execute agent tools or MCP calls.
"""

from pyprocore.evals import get_builtin_dataset, run_eval_suite


def main() -> None:
    """Run the bundled agent manifest eval dataset."""
    result = run_eval_suite(get_builtin_dataset("golden_agent_manifest_basic"))
    print(f"Agent manifest eval passed: {result.passed}")
    print(f"Score: {result.score}/{result.max_score}")


if __name__ == "__main__":
    main()
