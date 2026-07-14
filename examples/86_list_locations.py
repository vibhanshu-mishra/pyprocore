"""List project locations.

Set PROCORE_COMPANY_ID and PROCORE_PROJECT_ID in your environment or .env file.
"""

from __future__ import annotations

import os

from pyprocore.core.exceptions import ProcoreError
from pyprocore.services import list_locations


def main() -> None:
    """Run the example."""
    company_id = os.getenv("PROCORE_COMPANY_ID")
    project_id = os.getenv("PROCORE_PROJECT_ID")
    if not company_id or not project_id:
        print("Set PROCORE_COMPANY_ID and PROCORE_PROJECT_ID before listing locations.")
        return

    try:
        locations = list_locations(int(company_id), int(project_id))
    except ProcoreError as exc:
        print(f"Could not list locations: {exc}")
        return

    print(f"Found {len(locations)} locations.")
    for location in locations[:10]:
        print(f"- {location.id}: {location.full_name or location.name}")


if __name__ == "__main__":
    main()
