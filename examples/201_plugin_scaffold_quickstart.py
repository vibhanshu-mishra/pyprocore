"""Preview a safe local plugin scaffold plan.

This example does not write files, import plugin modules, install packages, or
call Procore. It is a beginner-friendly way to see what Phase 11D would create.
"""

from pathlib import Path

from pyprocore.plugins import scaffold_plugin_pack


def main() -> None:
    """Build and print a dry-run scaffold summary."""
    result = scaffold_plugin_pack(
        "example_local_plugin",
        Path("./plugin-scaffold-preview"),
        dry_run=True,
    )
    print(f"Scaffold: {result.name}")
    print(f"Files planned: {result.planned_count}")
    print("No files were written.")


if __name__ == "__main__":
    main()
