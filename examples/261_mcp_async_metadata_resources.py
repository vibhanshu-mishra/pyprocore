"""List Phase 15B MCP async metadata resources without making network calls."""

from pyprocore.mcp import list_mcp_resources


def main() -> None:
    """Print local async-related MCP resource URIs."""
    print("Async metadata resources:")
    for resource in list_mcp_resources():
        if "async" in resource.tags:
            print(f"- {resource.uri} ({resource.kind.value})")


if __name__ == "__main__":
    main()
