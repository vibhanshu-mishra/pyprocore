"""Show Phase 8E financial tools in the local agent registry.

This example does not call Procore. The registry is discovery-only, and tool
execution remains disabled.
"""

from __future__ import annotations

from pyprocore.agent import list_agent_tools


def main() -> None:
    """Run the example."""
    phase8e_tools = [
        tool
        for tool in list_agent_tools()
        if any(keyword in tool.name for keyword in ("change_event", "budget", "cost", "commitment"))
    ]
    print(f"Found {len(phase8e_tools)} Phase 8E-style agent registry entries.")
    for tool in phase8e_tools:
        print(f"- {tool.name}: {tool.title}")


if __name__ == "__main__":
    main()
