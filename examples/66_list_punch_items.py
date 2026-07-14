"""List Procore punch items for a project."""

from __future__ import annotations

import os

from pyprocore.core.exceptions import ProcoreError
from pyprocore.services import list_punch_items


def main() -> None:
    """Run the example."""
    company_id = os.getenv("PROCORE_COMPANY_ID")
    project_id = os.getenv("PROCORE_PROJECT_ID")
    if not company_id or not project_id:
        print("Set PROCORE_COMPANY_ID and PROCORE_PROJECT_ID before running this example.")
        return

    try:
        punch_items = list_punch_items(int(company_id), int(project_id))
    except ProcoreError as exc:
        print(f"Could not list punch items: {exc}")
        return

    print(f"Found {len(punch_items)} punch items.")
    for punch_item in punch_items[:10]:
        title = punch_item.title or punch_item.name or "(untitled)"
        print(f"- {punch_item.id}: {punch_item.number or 'no number'} - {title}")


if __name__ == "__main__":
    main()
