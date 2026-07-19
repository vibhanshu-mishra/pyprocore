"""Validate a local JSON plugin configuration file.

This example reads the safe sample JSON file under examples/configs. It never
executes plugin code and does not require live Procore access.
"""

from __future__ import annotations

from pathlib import Path

from pyprocore.plugins import load_plugin_config_from_file, validate_plugin_config


def main() -> None:
    """Validate the sample plugin configuration."""
    config_path = Path(__file__).parent / "configs" / "plugin_config_minimal.json"
    config = load_plugin_config_from_file(config_path)
    result = validate_plugin_config(config)

    print(f"Validated: {config_path.name}")
    print(f"Valid: {result.valid}")
    if result.errors:
        print("Errors:")
        for error in result.errors:
            print(f"- {error}")


if __name__ == "__main__":
    main()
