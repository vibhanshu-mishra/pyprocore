"""List RFIs for a Procore project.

Set PROCORE_PROJECT_ID before running. Optionally set PROCORE_RFI_STATUS to
filter by status. This script makes a live Procore API call.
"""

from __future__ import annotations

import os

from pyprocore.core.exceptions import ProcoreError
from pyprocore.services import list_rfis


def main() -> None:
    """Run the RFI listing example."""
    project_id_text = os.getenv("PROCORE_PROJECT_ID")
    if not project_id_text:
        print("Set PROCORE_PROJECT_ID before running this example.")
        return

    try:
        project_id = int(project_id_text)
        status = os.getenv("PROCORE_RFI_STATUS")
        rfis = list_rfis(project_id, status=status)
    except ValueError:
        print("PROCORE_PROJECT_ID must be a number.")
        return
    except ProcoreError as error:
        print(f"Could not list RFIs: {error}")
        print("Check the project ID and your Procore permissions.")
        return

    if not rfis:
        print(f"No RFIs were returned for project {project_id}.")
        return

    filter_text = f" with status {status!r}" if status else ""
    print(f"RFIs for project {project_id}{filter_text}:")
    for rfi in rfis:
        print(f"- {rfi.id}: #{rfi.number or 'No number'} - {rfi.subject or 'No subject'}")


if __name__ == "__main__":
    main()
