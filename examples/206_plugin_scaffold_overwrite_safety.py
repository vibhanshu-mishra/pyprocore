"""Demonstrate overwrite safety for local plugin scaffolds.

Existing files are skipped unless overwrite=True is passed explicitly.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

from pyprocore.plugins import scaffold_plugin_config


def main() -> None:
    """Show skip behavior when a scaffold file already exists."""
    with TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        scaffold_plugin_config("example_local_plugin", output_dir, dry_run=False)
        second = scaffold_plugin_config("example_local_plugin", output_dir, dry_run=False)
        print(f"Second run skipped: {second.skipped_count}")
        replaced = scaffold_plugin_config(
            "example_local_plugin",
            output_dir,
            overwrite=True,
            dry_run=False,
        )
        print(f"Overwrite run written: {replaced.written_count}")


if __name__ == "__main__":
    main()
