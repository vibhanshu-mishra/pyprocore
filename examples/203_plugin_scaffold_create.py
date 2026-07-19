"""Create a safe local plugin scaffold in a temporary directory.

This writes static template files only. It does not execute generated files or
call Procore.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

from pyprocore.plugins import scaffold_plugin_pack


def main() -> None:
    """Create a scaffold under a temporary folder."""
    with TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir) / "example_local_plugin"
        result = scaffold_plugin_pack(
            "example_local_plugin",
            output_dir,
            dry_run=False,
        )
        print(f"Output: {result.output_dir}")
        print(f"Written: {result.written_count}")
        print("Temporary files are removed when this example exits.")


if __name__ == "__main__":
    main()
