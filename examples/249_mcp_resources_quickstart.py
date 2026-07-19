"""List local PyProcore MCP resources without calling Procore."""

from pyprocore.mcp import list_mcp_resources


def main() -> None:
    """Print discovery-only MCP resource metadata."""
    resources = list_mcp_resources()
    print(f"Found {len(resources)} local MCP resources.")
    for resource in resources:
        print(f"- {resource.uri} ({resource.kind.value})")
    print("No Procore API calls, model calls, or tool execution were performed.")


if __name__ == "__main__":
    main()
