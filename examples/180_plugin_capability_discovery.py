"""Find registered plugin manifests by capability.

This example filters built-in plugin metadata locally. It does not import plugin
modules, install packages, or contact Procore.
"""

from pyprocore.plugins import PluginCapability, PluginRegistry, discover_builtin_plugins


def main() -> None:
    """Print metadata-only exporter plugins."""
    registry = PluginRegistry(discover_builtin_plugins().discovered)
    exporters = registry.find_plugins_by_capability(PluginCapability.EXPORTER)

    print("Exporter-capable plugin manifests")
    for plugin in exporters:
        print(f"- {plugin.name}: {plugin.description}")
    print("Mode: metadata discovery only.")


if __name__ == "__main__":
    main()
