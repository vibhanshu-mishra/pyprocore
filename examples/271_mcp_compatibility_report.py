"""Build a JSON MCP compatibility report.

Use this when checking what local MCP metadata PyProcore exposes to integrators.
No live Procore access is required.
"""

from __future__ import annotations

from pyprocore.mcp import build_mcp_compatibility_report


def main() -> None:
    """Print a compact compatibility report summary."""
    report = build_mcp_compatibility_report()
    print("MCP compatibility report:")
    print(f"- Status: {report.status.value}")
    print(f"- Discovery only: {report.discovery_only}")
    print(f"- Resource kinds: {len(report.resource_count_by_kind)}")
    print(f"- Prompt kinds: {len(report.prompt_count_by_kind)}")


if __name__ == "__main__":
    main()
