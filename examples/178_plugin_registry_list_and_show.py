"""List and show safe plugin manifests using the local registry.

This example registers built-in metadata-only manifests. It does not install or
execute plugins and does not require Procore credentials.
"""

from pyprocore.plugins import PluginRegistry, discover_builtin_plugins


def main() -> None:
    """List built-in plugin manifests and print one detail record."""
    discovery = discover_builtin_plugins()
    registry = PluginRegistry(discovery.discovered)
    plugins = registry.list_plugins()

    print(f"Registered plugin manifests: {len(plugins)}")
    for plugin in plugins:
        print(f"- {plugin.name}: {plugin.description}")

    if plugins:
        first = registry.get_plugin(plugins[0].name)
        print("")
        print(f"First plugin: {first.name}")
        print(f"Capabilities: {', '.join(item.value for item in first.capabilities)}")


if __name__ == "__main__":
    main()
