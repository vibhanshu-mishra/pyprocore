"""Summarize Phase 13D offline model-response fixture evals."""

from pyprocore.evals import list_builtin_eval_suites


def main() -> None:
    """Print built-in Phase 13D suite names."""
    suites = [
        suite for suite in list_builtin_eval_suites() if suite.name.startswith("model_fixture_")
    ]
    print("Phase 13D offline model-response fixture suites:")
    for suite in suites:
        print(f"- {suite.name}: {suite.case_count} cases")
    print("All checks are local and deterministic.")


if __name__ == "__main__":
    main()
