"""List company departments.

Set PROCORE_COMPANY_ID in your environment or .env file before running this
example.
"""

from __future__ import annotations

import os

from pyprocore.core.exceptions import ProcoreError
from pyprocore.services import list_departments


def main() -> None:
    """Run the example."""
    company_id = os.getenv("PROCORE_COMPANY_ID")
    if not company_id:
        print("Set PROCORE_COMPANY_ID before listing departments.")
        return

    try:
        departments = list_departments(int(company_id))
    except ProcoreError as exc:
        print(f"Could not list departments: {exc}")
        return

    print(f"Found {len(departments)} departments.")
    for department in departments[:10]:
        print(f"- {department.id}: {department.name}")


if __name__ == "__main__":
    main()
