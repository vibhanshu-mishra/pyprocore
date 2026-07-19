"""Score a local RFI model-response fixture from JSON.

The fixture is a saved sample response. This script never generates text and
never calls Procore or any model provider.
"""

from pathlib import Path

from pyprocore.evals import load_model_response_fixture_from_file, score_model_response_fixture


def main() -> None:
    """Load and score the sample RFI response fixture."""
    fixture_path = Path("examples/model_response_fixtures/rfi_review/passing_response.json")
    fixture = load_model_response_fixture_from_file(fixture_path)
    result = score_model_response_fixture(fixture)
    print(f"Fixture: {result.fixture_name}")
    print(f"Passed: {result.passed}")
    print(f"Score: {result.score}/{result.max_score}")


if __name__ == "__main__":
    main()
