"""Demonstrate fake citation/source-label detection on a local fixture."""

from pathlib import Path

from pyprocore.evals import load_model_response_fixture_from_file, score_model_response_fixture


def main() -> None:
    """Score a fixture that is expected to detect a fake citation."""
    fixture_path = Path(
        "examples/model_response_fixtures/safety_boundaries/fake_citation_response.json"
    )
    result = score_model_response_fixture(load_model_response_fixture_from_file(fixture_path))
    print("Fake citation detection fixture complete.")
    print(f"Passed by detecting expected issue: {result.passed}")


if __name__ == "__main__":
    main()
