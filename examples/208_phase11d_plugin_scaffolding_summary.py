"""Summarize Phase 11D plugin scaffolding safety boundaries.

This example is local and deterministic. It does not call Procore, external AI
services, or plugin code.
"""

from pyprocore.plugins import export_plugin_scaffold_sample_plan


def main() -> None:
    """Print the sample scaffold plan summary."""
    plan = export_plugin_scaffold_sample_plan()
    print("Phase 11D plugin scaffolding")
    print(f"Files planned: {len(plan.files)}")
    print("Generated files are templates only.")
    print("No plugin installation, remote fetching, loading, or execution is enabled.")


if __name__ == "__main__":
    main()
