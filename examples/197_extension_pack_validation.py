"""Validate a local JSON extension-pack manifest.

This example reads sample metadata from examples/configs and performs validation
without executing plugin code.
"""

from __future__ import annotations

from pathlib import Path

from pyprocore.plugins import (
    load_extension_pack_manifest_from_file,
    validate_extension_pack_manifest,
)


def main() -> None:
    """Validate the sample extension-pack manifest."""
    pack_path = Path(__file__).parent / "configs" / "plugin_extension_pack_sample.json"
    extension_pack = load_extension_pack_manifest_from_file(pack_path)
    result = validate_extension_pack_manifest(extension_pack)

    print(f"Validated: {pack_path.name}")
    print(f"Valid: {result.valid}")
    print("Mode: metadata validation only.")


if __name__ == "__main__":
    main()
