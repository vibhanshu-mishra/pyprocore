"""Inspect Phase 8D read-only agent registry metadata.

This example does not execute Procore tools and does not call live Procore APIs.
"""

from __future__ import annotations

from pyprocore.agent import list_agent_tools


def main() -> None:
    """Run the example."""
    phase8d_names = {
        "procore.list_company_users",
        "procore.get_company_user",
        "procore.find_company_user",
        "procore.list_project_users",
        "procore.get_project_user",
        "procore.find_project_user",
        "procore.list_vendors",
        "procore.get_vendor",
        "procore.find_vendor",
        "procore.list_departments",
        "procore.get_department",
        "procore.find_department",
        "procore.list_project_distribution_groups",
        "procore.get_project_distribution_group",
        "procore.find_project_distribution_group",
        "procore.list_locations",
        "procore.get_location",
        "procore.find_location",
    }
    tools = [tool for tool in list_agent_tools() if tool.name in phase8d_names]
    print(f"Found {len(tools)} Phase 8D agent metadata entries.")
    for tool in tools:
        print(f"- {tool.name}: safety={tool.safety_level}, calls_live_api={tool.calls_live_api}")


if __name__ == "__main__":
    main()
