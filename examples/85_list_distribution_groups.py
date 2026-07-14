"""List project distribution groups.

Set PROCORE_COMPANY_ID and PROCORE_PROJECT_ID in your environment or .env file.
"""

from __future__ import annotations

import os

from pyprocore.core.exceptions import ProcoreError
from pyprocore.services import list_project_distribution_groups


def main() -> None:
    """Run the example."""
    company_id = os.getenv("PROCORE_COMPANY_ID")
    project_id = os.getenv("PROCORE_PROJECT_ID")
    if not company_id or not project_id:
        print("Set PROCORE_COMPANY_ID and PROCORE_PROJECT_ID before listing groups.")
        return

    try:
        groups = list_project_distribution_groups(int(company_id), int(project_id))
    except ProcoreError as exc:
        print(f"Could not list distribution groups: {exc}")
        return

    print(f"Found {len(groups)} distribution groups.")
    for group in groups[:10]:
        print(f"- {group.id}: {group.name}")


if __name__ == "__main__":
    main()
