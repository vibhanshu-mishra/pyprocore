"""Create a hook metadata scaffold in a temporary directory.

Hook scaffolds describe possible hooks. They do not register or execute hook
callables.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

from pyprocore.plugins import scaffold_hook_pack


def main() -> None:
    """Write a hook manifest template."""
    with TemporaryDirectory() as temp_dir:
        result = scaffold_hook_pack(
            "example_local_plugin",
            Path(temp_dir),
            dry_run=False,
        )
        print(f"Hook manifest files written: {result.written_count}")
        print("Hook execution remains disabled by this scaffold.")


if __name__ == "__main__":
    main()
