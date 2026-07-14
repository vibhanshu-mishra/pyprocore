"""List Procore change events for a project.

Set PROCORE_COMPANY_ID and PROCORE_PROJECT_ID in your environment or .env
before running this example against a real Procore account.
"""

from __future__ import annotations

import os

from pyprocore.core.exceptions import ProcoreAPIError
from pyprocore.services.financials import list_change_events


def main() -> None:
    """Run the example."""
    company_id = int(os.environ["PROCORE_COMPANY_ID"])
    project_id = int(os.environ["PROCORE_PROJECT_ID"])
    try:
        events = list_change_events(company_id, project_id)
    except ProcoreAPIError as error:
        print(f"Could not list change events: {error}")
        return
    print(f"Found {len(events)} change events.")
    for event in events[:10]:
        print(f"- {event.number or event.id}: {event.title or event.name}")


if __name__ == "__main__":
    main()
