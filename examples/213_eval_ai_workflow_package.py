"""Evaluate model-agnostic AI workflow package metadata.

This example validates local package shape only. It does not call an AI model
and does not send project data anywhere.
"""

from pyprocore.evals import get_builtin_dataset, run_eval_suite


def main() -> None:
    """Run the bundled AI workflow package eval dataset."""
    result = run_eval_suite(get_builtin_dataset("golden_ai_workflow_package_basic"))
    print(f"AI workflow package eval passed: {result.passed}")
    print("External model calls were not made.")


if __name__ == "__main__":
    main()
