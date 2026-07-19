"""Score a local submittal model-response fixture from JSON."""

from pathlib import Path

from pyprocore.evals import load_model_response_fixture_from_file, score_model_response_fixture


def main() -> None:
    """Load and score the sample submittal response fixture."""
    fixture_path = Path("examples/model_response_fixtures/submittal_review/passing_response.json")
    fixture = load_model_response_fixture_from_file(fixture_path)
    result = score_model_response_fixture(fixture)
    print("Submittal fixture eval complete.")
    print(f"Passed: {result.passed}")


if __name__ == "__main__":
    main()
