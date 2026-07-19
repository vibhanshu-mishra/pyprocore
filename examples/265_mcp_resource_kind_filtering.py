"""Filter MCP resources by kind without reading credentials."""

from pyprocore.mcp import list_mcp_resources


def main() -> None:
    """Print eval-suite resources using the kind filter."""
    resources = list_mcp_resources(kind="eval_suite")
    print(f"Found {len(resources)} eval suite resources:")
    for resource in resources[:10]:
        print(f"- {resource.uri}")
    if len(resources) > 10:
        print(f"...and {len(resources) - 10} more")


if __name__ == "__main__":
    main()
