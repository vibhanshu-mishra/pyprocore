"""Inspect Phase 8A read-only agent registry metadata.

This example does not execute Procore tools and does not call live Procore APIs.
"""

from __future__ import annotations

from pyprocore.agent import list_agent_tools


def main() -> None:
    """Run the example."""
    phase8a_names = {
        "procore.list_observations",
        "procore.get_observation",
        "procore.find_observation",
        "procore.list_punch_items",
        "procore.get_punch_item",
        "procore.find_punch_item",
        "procore.list_generic_tools",
        "procore.list_correspondences",
        "procore.get_correspondence",
        "procore.find_correspondence",
    }
    tools = [tool for tool in list_agent_tools() if tool.name in phase8a_names]
    print(f"Found {len(tools)} Phase 8A agent metadata entries.")
    for tool in tools:
        print(f"- {tool.name}: safety={tool.safety_level}, calls_live_api={tool.calls_live_api}")


if __name__ == "__main__":
    main()
