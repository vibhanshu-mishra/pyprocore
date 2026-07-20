"""Summarize Phase 15C MCP compatibility and discovery polish."""

from __future__ import annotations

from pyprocore.mcp import build_mcp_compatibility_report, build_mcp_contract_report


def main() -> None:
    """Print a short Phase 15C summary."""
    contract = build_mcp_contract_report()
    report = build_mcp_compatibility_report()
    print("Phase 15C MCP compatibility summary")
    print(f"- Contract passed: {contract['passed']}")
    print(f"- Compatibility status: {report.status.value}")
    print("- MCP remains discovery-only.")
    print("- Tool execution remains disabled.")


if __name__ == "__main__":
    main()
