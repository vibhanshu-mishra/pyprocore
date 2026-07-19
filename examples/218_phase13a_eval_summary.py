"""Summarize Phase 13A deterministic golden eval support.

This is a local summary example. It does not call Procore, call AI models,
execute plugins, execute MCP, or execute Procore tools.
"""

from pyprocore.evals import list_builtin_eval_suites


def main() -> None:
    """Print the bundled Phase 13A eval suite names."""
    suites = list_builtin_eval_suites()
    print("Phase 13A golden eval suites:")
    for suite in suites:
        print(f"- {suite.name}: {suite.case_count} case(s)")
    print("Mode: local deterministic fixtures only.")


if __name__ == "__main__":
    main()
