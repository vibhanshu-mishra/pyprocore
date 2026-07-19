"""Summarize Phase 13B workflow-specific golden eval support.

Phase 13B adds deeper deterministic fixtures for PyProcore workflow artifacts.
Everything runs locally and safely with placeholder data.
"""

from pyprocore.evals import list_builtin_eval_suites


def main() -> None:
    """Print the Phase 13B workflow suite names."""
    phase13b_names = {
        "rfi_workflow_golden",
        "submittal_workflow_golden",
        "async_export_golden",
        "async_batch_golden",
        "ai_workflow_package_golden",
        "plugin_metadata_golden",
        "plugin_config_golden",
        "safety_boundaries_golden",
    }
    suites = [suite for suite in list_builtin_eval_suites() if suite.name in phase13b_names]
    print("Phase 13B workflow-specific eval suites:")
    for suite in suites:
        print(f"- {suite.name}: {suite.case_count} case(s)")
    print("Mode: local deterministic fixtures only.")


if __name__ == "__main__":
    main()
