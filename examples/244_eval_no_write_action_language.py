"""Demonstrate prohibited write-action language detection."""

from pathlib import Path

from pyprocore.evals import load_model_response_fixture_from_file, score_model_response_fixture


def main() -> None:
    """Score a fixture that intentionally contains unsafe write-action language."""
    fixture_path = Path("examples/model_response_fixtures/rfi_review/unsafe_response_detected.json")
    result = score_model_response_fixture(load_model_response_fixture_from_file(fixture_path))
    print("Write-action language detection complete.")
    print(f"Expected unsafe wording detected: {result.passed}")


if __name__ == "__main__":
    main()
