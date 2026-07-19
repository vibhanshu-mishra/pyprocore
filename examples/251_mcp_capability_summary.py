"""Show the discovery-only MCP capability summary."""

from pyprocore.mcp import build_mcp_capability_summary


def main() -> None:
    """Print a beginner-friendly capability summary."""
    summary = build_mcp_capability_summary()
    print(f"Server: {summary.server_name}")
    print(f"Resources: {summary.resource_count}")
    print(f"Prompts: {summary.prompt_count}")
    print(f"Tools: {summary.tool_summary.total_tools}")
    print(f"MCP execution enabled: {summary.safety.mcp_execution_enabled}")
    print(f"Live Procore calls during discovery: {summary.safety.calls_live_procore_api}")


if __name__ == "__main__":
    main()
