"""Inspect Phase 8G agent registry metadata without executing tools."""

from __future__ import annotations

from pyprocore.agent import list_agent_tools


def main() -> None:
    """Print Phase 8G discovery-only agent tools."""
    phase8g_keywords = (
        "schedule",
        "task",
        "calendar",
        "coordination_issue",
        "form",
        "action_plan",
    )
    tools = [
        tool.name
        for tool in list_agent_tools()
        if any(keyword in tool.name for keyword in phase8g_keywords)
    ]
    print("Phase 8G tools are discovery-only; execution remains disabled.")
    for name in tools:
        print(f"- {name}")


if __name__ == "__main__":
    main()
