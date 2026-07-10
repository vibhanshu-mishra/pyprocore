"""List Procore specification sets for a project.

Set PROCORE_PROJECT_ID and PROCORE_COMPANY_ID in your environment or .env file
before running this example. This script makes a live Procore API call.
"""

from __future__ import annotations

import os

from pyprocore.core.exceptions import ProcoreError
from pyprocore.services import list_specification_sets


def main() -> None:
    """Run the specification set listing example."""
    project_id = os.getenv("PROCORE_PROJECT_ID")
    company_id = os.getenv("PROCORE_COMPANY_ID")
    if not project_id:
        print("Set PROCORE_PROJECT_ID before running this example.")
        return

    try:
        sets = list_specification_sets(
            int(project_id),
            company_id=int(company_id) if company_id else None,
        )
    except ValueError:
        print("PROCORE_PROJECT_ID and PROCORE_COMPANY_ID must be numbers.")
        return
    except ProcoreError as exc:
        print(f"Could not list specification sets: {exc}")
        return

    print(f"Found {len(sets)} specification set(s).")
    for specification_set in sets:
        print(f"- {specification_set.id}: {specification_set.name or 'Unnamed set'}")


if __name__ == "__main__":
    main()
