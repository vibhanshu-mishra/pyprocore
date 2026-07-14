"""List Procore incidents for a project.

Set PROCORE_COMPANY_ID and PROCORE_PROJECT_ID in your environment or `.env`
before running this example.
"""

from __future__ import annotations

import os

from pyprocore.core.exceptions import ProcoreError
from pyprocore.services import list_incidents


def main() -> None:
    """Run the example."""
    company_id = os.getenv("PROCORE_COMPANY_ID")
    project_id = os.getenv("PROCORE_PROJECT_ID")
    if not company_id or not project_id:
        print("Set PROCORE_COMPANY_ID and PROCORE_PROJECT_ID before running this example.")
        return

    try:
        incidents = list_incidents(int(company_id), int(project_id))
    except ProcoreError as exc:
        print(f"Could not list incidents: {exc}")
        return

    print(f"Found {len(incidents)} incidents.")
    for incident in incidents[:10]:
        title = incident.title or incident.name or "(untitled)"
        print(f"- {incident.id}: {incident.number or 'no number'} - {title}")


if __name__ == "__main__":
    main()
