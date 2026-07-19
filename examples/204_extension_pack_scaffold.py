"""Create an extension-pack scaffold in a temporary directory.

Extension-pack scaffolds are JSON metadata only.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

from pyprocore.plugins import scaffold_extension_pack


def main() -> None:
    """Write a local extension-pack template."""
    with TemporaryDirectory() as temp_dir:
        result = scaffold_extension_pack(
            "example_local_plugin",
            Path(temp_dir),
            dry_run=False,
        )
        print(f"Extension-pack files written: {result.written_count}")
        for file in result.files:
            print(file.path)


if __name__ == "__main__":
    main()
