"""Summarize plugin configuration against built-in plugin metadata.

This example performs local metadata filtering only. It does not load or run
plugins.
"""

from __future__ import annotations

from pathlib import Path

from pyprocore.plugins import (
    PluginRegistry,
    discover_builtin_plugins,
    load_plugin_config_from_file,
    merge_plugin_config_with_registry_metadata,
)


def main() -> None:
    """Print configured plugin metadata matches."""
    config_path = Path(__file__).parent / "configs" / "plugin_config_enterprise.json"
    config = load_plugin_config_from_file(config_path)
    registry = PluginRegistry(discover_builtin_plugins().discovered)
    summary = merge_plugin_config_with_registry_metadata(config, registry.list_plugins())

    print("Configured plugin metadata summary")
    print(f"Matched plugins: {len(summary.matched_plugins)}")
    for name in summary.matched_plugins:
        print(f"- {name}")
    print("Mode: metadata filtering only.")


if __name__ == "__main__":
    main()
