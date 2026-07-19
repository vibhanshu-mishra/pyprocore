"""List Phase 15B MCP plugin metadata resources without executing plugins."""

from pyprocore.mcp import list_mcp_resources


def main() -> None:
    """Print local plugin-related MCP resource URIs."""
    print("Plugin metadata resources:")
    for resource in list_mcp_resources():
        if "plugins" in resource.tags:
            print(f"- {resource.uri} ({resource.kind.value})")


if __name__ == "__main__":
    main()
