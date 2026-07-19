"""Evaluate a small export-rows golden dataset.

Use this pattern when checking CSV/JSONL export row shape with placeholder or
test data. No live Procore calls are made.
"""

from pyprocore.evals import get_builtin_dataset, run_eval_suite


def main() -> None:
    """Run the bundled export rows dataset."""
    dataset = get_builtin_dataset("golden_export_rows_basic")
    result = run_eval_suite(dataset)
    print(f"Dataset: {dataset.metadata.name}")
    print(f"Passed: {result.passed}")
    print(f"Cases: {result.passed_cases}/{result.total_cases}")


if __name__ == "__main__":
    main()
