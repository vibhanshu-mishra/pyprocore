"""Evaluate an offline engineering assistant style fixture."""

from pathlib import Path

from pyprocore.evals import load_model_response_fixture_from_file, score_model_response_fixture


def main() -> None:
    """Score the local engineering assistant response fixture."""
    fixture_path = Path(
        "examples/model_response_fixtures/engineering_assistant/passing_response.json"
    )
    result = score_model_response_fixture(load_model_response_fixture_from_file(fixture_path))
    print(f"Engineering assistant fixture status: {result.status.value}")
    print("No live or model calls were made.")


if __name__ == "__main__":
    main()
