"""Show the safe response for an unknown MCP resource URI."""

from __future__ import annotations

from pyprocore.mcp import safe_mcp_resource_not_found


def main() -> None:
    """Print a safe unknown-resource response."""
    response = safe_mcp_resource_not_found("pyprocore://missing")
    print(response["message"])
    print(f"URI: {response['uri']}")
    print(f"Discovery only: {response['safety']['discovery_only']}")


if __name__ == "__main__":
    main()
