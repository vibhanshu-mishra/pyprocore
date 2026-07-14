"""Inspect Phase 8C read-only agent registry metadata.

This example does not execute Procore tools and does not call live Procore APIs.
"""

from __future__ import annotations

from pyprocore.agent import list_agent_tools


def main() -> None:
    """Run the example."""
    phase8c_names = {
        "procore.list_meetings",
        "procore.get_meeting",
        "procore.find_meeting",
        "procore.list_inspections",
        "procore.get_inspection",
        "procore.find_inspection",
        "procore.list_incidents",
        "procore.get_incident",
        "procore.get_project_incident_configuration",
        "procore.find_incident",
    }
    tools = [tool for tool in list_agent_tools() if tool.name in phase8c_names]
    print(f"Found {len(tools)} Phase 8C agent metadata entries.")
    for tool in tools:
        print(f"- {tool.name}: safety={tool.safety_level}, calls_live_api={tool.calls_live_api}")


if __name__ == "__main__":
    main()
