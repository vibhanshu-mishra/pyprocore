"""Summarize Phase 11C plugin config and extension-pack support.

This example runs locally and only inspects typed metadata models.
"""

from __future__ import annotations

from pyprocore.plugins import export_extension_pack_template, export_plugin_config_template


def main() -> None:
    """Print a short Phase 11C summary."""
    config = export_plugin_config_template()
    extension_pack = export_extension_pack_template()

    print("Phase 11C: Plugin Configuration and Local Extension Packs")
    print(f"Config enabled plugins: {len(config.enabled_plugins)}")
    print(f"Extension-pack included plugins: {len(extension_pack.included_plugins)}")
    print("Mode: local JSON metadata only.")


if __name__ == "__main__":
    main()
