"""List Phase 15B MCP AI workflow metadata resources."""

from pyprocore.mcp import list_mcp_resources


def main() -> None:
    """Print local AI workflow MCP resource URIs."""
    print("AI workflow metadata resources:")
    for resource in list_mcp_resources():
        if "ai-workflows" in resource.tags:
            print(f"- {resource.uri} ({resource.kind.value})")


if __name__ == "__main__":
    main()
