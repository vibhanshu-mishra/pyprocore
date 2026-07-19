"""List Phase 15B MCP eval metadata resources without running evals."""

from pyprocore.mcp import list_mcp_resources


def main() -> None:
    """Print local eval-related MCP resource URIs."""
    print("Local eval metadata resources:")
    for resource in list_mcp_resources():
        if "evals" in resource.tags:
            print(f"- {resource.uri} ({resource.kind.value})")


if __name__ == "__main__":
    main()
