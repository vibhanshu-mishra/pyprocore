"""Demonstrate local scaffold path safety.

Unsafe output paths produce validation findings instead of writing files.
"""

from pathlib import Path

from pyprocore.plugins import scaffold_plugin_pack


def main() -> None:
    """Show path traversal rejection in dry-run mode."""
    result = scaffold_plugin_pack(
        "example_local_plugin",
        Path("../unsafe-output"),
        dry_run=True,
    )
    print(f"Findings: {len(result.findings)}")
    for finding in result.findings:
        print(f"{finding.severity}: {finding.message}")


if __name__ == "__main__":
    main()
