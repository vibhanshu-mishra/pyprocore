"""Load a safe local plugin configuration template.

This example does not require Procore credentials. It does not install plugins,
load plugin code, or call the Procore API.
"""

from __future__ import annotations

from pyprocore.plugins import export_plugin_config_template, validate_plugin_config


def main() -> None:
    """Print a starter plugin configuration summary."""
    config = export_plugin_config_template()
    result = validate_plugin_config(config)

    print("Plugin config quickstart")
    print(f"Valid: {result.valid}")
    print(f"Enabled plugins: {', '.join(config.enabled_plugins)}")
    print("Mode: metadata preferences only.")


if __name__ == "__main__":
    main()
