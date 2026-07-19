"""Inspect hook preferences from a local plugin config.

Hook preferences are descriptive metadata. They do not register callables or run
hooks.
"""

from __future__ import annotations

from pathlib import Path

from pyprocore.plugins import load_plugin_config_from_file


def main() -> None:
    """Print hook preferences from a sample config."""
    config_path = Path(__file__).parent / "configs" / "plugin_config_hooks.json"
    config = load_plugin_config_from_file(config_path)

    print("Hook preferences")
    for preference in config.hook_preferences:
        print(f"- {preference.hook_name} ({preference.hook_type.value})")
    print("Mode: preferences only; no hook execution.")


if __name__ == "__main__":
    main()
