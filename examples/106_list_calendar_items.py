"""List read-only project calendar items.

Set PROCORE_PROJECT_ID and optionally PROCORE_COMPANY_ID before running.
This example makes a live Procore call only when executed directly.
"""

from __future__ import annotations

import os

from pyprocore import list_calendar_items
from pyprocore.core.exceptions import ProcoreAPIError


def main() -> None:
    """Run the calendar items example."""
    project_id = int(os.environ["PROCORE_PROJECT_ID"])
    company_id = int(os.environ["PROCORE_COMPANY_ID"]) if os.getenv("PROCORE_COMPANY_ID") else None
    try:
        items = list_calendar_items(company_id, project_id)
    except ProcoreAPIError as exc:
        print(f"Could not list calendar items: {exc}")
        return
    print(f"Found {len(items)} calendar item(s).")
    for item in items[:10]:
        print(f"- {item.id}: {item.name or item.title or item.start_date}")


if __name__ == "__main__":
    main()
