"""List Procore Generic Tool correspondence items for a project.

Correspondence-like data in Procore is exposed through Generic Tools. List the
project's Generic Tools first, then provide PROCORE_GENERIC_TOOL_ID.
"""

from __future__ import annotations

import os

from pyprocore.core.exceptions import ProcoreError
from pyprocore.services import list_correspondences, list_generic_tools


def main() -> None:
    """Run the example."""
    company_id = os.getenv("PROCORE_COMPANY_ID")
    project_id = os.getenv("PROCORE_PROJECT_ID")
    generic_tool_id = os.getenv("PROCORE_GENERIC_TOOL_ID")
    if not company_id or not project_id:
        print("Set PROCORE_COMPANY_ID and PROCORE_PROJECT_ID before running this example.")
        return

    try:
        if not generic_tool_id:
            tools = list_generic_tools(int(company_id), int(project_id))
            print("Set PROCORE_GENERIC_TOOL_ID to list correspondence items.")
            print(f"Found {len(tools)} Generic Tools:")
            for tool in tools[:10]:
                print(f"- {tool.id}: {tool.name or tool.title or '(unnamed)'}")
            return

        items = list_correspondences(int(company_id), int(project_id), int(generic_tool_id))
    except ProcoreError as exc:
        print(f"Could not list correspondence items: {exc}")
        return

    print(f"Found {len(items)} correspondence items.")
    for item in items[:10]:
        title = item.subject or item.title or item.name or "(untitled)"
        print(f"- {item.id}: {item.number or 'no number'} - {title}")


if __name__ == "__main__":
    main()
