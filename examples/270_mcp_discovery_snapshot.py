"""Build a local MCP discovery snapshot.

The snapshot is local JSON metadata only. It does not call Procore, load
credentials, or execute MCP tools.
"""

from __future__ import annotations

from pyprocore.mcp import build_mcp_discovery_snapshot, summarize_mcp_discovery_snapshot


def main() -> None:
    """Print a beginner-friendly MCP snapshot summary."""
    snapshot = build_mcp_discovery_snapshot()
    summary = summarize_mcp_discovery_snapshot(snapshot)
    print("MCP discovery snapshot built locally.")
    print(f"Server: {summary['server_name']}")
    print(f"Resources: {summary['resource_count']}")
    print(f"Prompts: {summary['prompt_count']}")
    print(f"Contract passed: {summary['contract_passed']}")


if __name__ == "__main__":
    main()
