"""Inspect Phase 8F agent registry metadata without executing tools."""

from __future__ import annotations

from pyprocore.agent import list_agent_tools


def main() -> None:
    """Print Phase 8F discovery-only agent tools."""
    phase8f_keywords = ("contract", "invoice", "payment", "billing", "tax", "cost_type")
    tools = [
        tool.name
        for tool in list_agent_tools()
        if any(keyword in tool.name for keyword in phase8f_keywords)
    ]
    print("Phase 8F tools are discovery-only; execution remains disabled.")
    for name in tools:
        print(f"- {name}")


if __name__ == "__main__":
    main()
