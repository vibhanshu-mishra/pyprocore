"""Create and print a safe sample golden dataset.

This example does not call Procore, does not call an AI model, and does not
require credentials. It only builds local deterministic fixture metadata.
"""

from pyprocore.evals import golden_dataset_to_json, sample_golden_dataset


def main() -> None:
    """Print a beginner-friendly sample golden dataset."""
    dataset = sample_golden_dataset()
    print("Sample golden dataset:")
    print(golden_dataset_to_json(dataset))


if __name__ == "__main__":
    main()
