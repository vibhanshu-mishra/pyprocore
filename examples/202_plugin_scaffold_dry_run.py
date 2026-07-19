"""Run a local plugin scaffold dry-run.

Dry-run mode renders a plan in memory and never writes files.
"""

from pathlib import Path

from pyprocore.plugins import PluginTemplateKind, scaffold_plugin_pack


def main() -> None:
    """Preview a README-only scaffold."""
    result = scaffold_plugin_pack(
        "readme_only_plugin",
        Path("./plugin-readme-preview"),
        kind=PluginTemplateKind.README,
        dry_run=True,
    )
    print(f"Dry run: {result.dry_run}")
    print(f"Planned files: {result.planned_count}")
    for file in result.files:
        print(file.path)


if __name__ == "__main__":
    main()
