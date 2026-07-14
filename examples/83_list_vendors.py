"""List company vendors.

Set PROCORE_COMPANY_ID in your environment or .env file before running this
example.
"""

from __future__ import annotations

import os

from pyprocore.core.exceptions import ProcoreError
from pyprocore.services import list_vendors


def main() -> None:
    """Run the example."""
    company_id = os.getenv("PROCORE_COMPANY_ID")
    if not company_id:
        print("Set PROCORE_COMPANY_ID before listing vendors.")
        return

    try:
        vendors = list_vendors(int(company_id))
    except ProcoreError as exc:
        print(f"Could not list vendors: {exc}")
        return

    print(f"Found {len(vendors)} vendors.")
    for vendor in vendors[:10]:
        print(f"- {vendor.id}: {vendor.name}")


if __name__ == "__main__":
    main()
