"""Print PyProcore MCP discovery safety boundaries."""

from pyprocore.mcp import read_mcp_resource_payload


def main() -> None:
    """Show the safety flags that keep MCP discovery read-only."""
    payload = read_mcp_resource_payload("pyprocore://safety/boundaries")
    safety = payload["payload"]
    print(f"Discovery only: {safety['discovery_only']}")
    print(f"MCP execution enabled: {safety['mcp_execution_enabled']}")
    print(f"Procore tool execution enabled: {safety['procore_tool_execution_enabled']}")
    print(f"External model calls enabled: {safety['calls_external_model_api']}")


if __name__ == "__main__":
    main()
