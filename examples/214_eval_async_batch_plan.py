"""Evaluate a safe placeholder async batch plan.

This checks local plan metadata and dry-run-friendly shape. It does not start
async HTTP calls or contact Procore.
"""

from pyprocore.evals import get_builtin_dataset, run_eval_suite


def main() -> None:
    """Run the bundled async batch plan eval dataset."""
    result = run_eval_suite(get_builtin_dataset("golden_async_batch_plan_basic"))
    print(f"Async batch plan eval passed: {result.passed}")
    print(f"Score: {result.score}/{result.max_score}")


if __name__ == "__main__":
    main()
