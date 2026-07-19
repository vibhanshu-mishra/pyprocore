"""Inspect metadata-only plugin resources exposed through MCP discovery."""

from pyprocore.mcp import read_mcp_resource_payload


def main() -> None:
    """Print plugin metadata safety information."""
    manifest = read_mcp_resource_payload("pyprocore://plugins/manifest")
    hooks = read_mcp_resource_payload("pyprocore://plugins/hooks")
    print(f"Plugin manifest mode: {manifest['payload']['mode']}")
    print(f"Plugin hook mode: {hooks['payload']['mode']}")
    print(f"Plugin execution enabled: {manifest['safety']['executes_plugins']}")
    print("No plugin code was run.")


if __name__ == "__main__":
    main()
