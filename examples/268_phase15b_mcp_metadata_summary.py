"""Print a compact Phase 15B MCP metadata summary."""

from pyprocore.mcp import build_mcp_capability_summary


def main() -> None:
    """Print discovery-only MCP capability highlights."""
    summary = build_mcp_capability_summary()
    print("Phase 15B MCP metadata summary:")
    print(f"- resources: {summary.resource_count}")
    print(f"- prompts: {summary.prompt_count}")
    print(f"- tool execution enabled: {summary.tool_summary.execution_enabled}")
    print(f"- model calls enabled: {summary.disabled_execution_status['external_model_calls']}")
    print("- metadata areas:")
    for item in summary.safety_boundaries:
        print(f"  - {item}")


if __name__ == "__main__":
    main()
