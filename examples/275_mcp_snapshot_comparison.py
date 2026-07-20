"""Compare two local MCP discovery snapshots.

This example compares a snapshot to itself so it is safe and deterministic.
"""

from __future__ import annotations

from pyprocore.mcp import build_mcp_discovery_snapshot, compare_mcp_discovery_snapshots


def main() -> None:
    """Print a local snapshot comparison summary."""
    snapshot = build_mcp_discovery_snapshot()
    comparison = compare_mcp_discovery_snapshots(snapshot, snapshot)
    print("MCP snapshot comparison complete.")
    print(f"Compatible: {comparison['compatible']}")
    print(f"Resources added: {len(comparison['resources_added'])}")
    print(f"Prompts removed: {len(comparison['prompts_removed'])}")


if __name__ == "__main__":
    main()
