"""List Procore drawings for a project.

Set PROCORE_PROJECT_ID in your environment or .env file before running this
example. Optionally set PROCORE_DRAWING_AREA_ID or PROCORE_DRAWING_DISCIPLINE_ID
to filter the list.
"""

from __future__ import annotations

import os

from pyprocore.core.exceptions import ProcoreError
from pyprocore.services import list_drawings


def main() -> None:
    """Run the drawing listing example."""
    project_id = os.getenv("PROCORE_PROJECT_ID")
    area_id = os.getenv("PROCORE_DRAWING_AREA_ID")
    discipline_id = os.getenv("PROCORE_DRAWING_DISCIPLINE_ID")
    company_id = os.getenv("PROCORE_COMPANY_ID")
    if not project_id:
        print("Set PROCORE_PROJECT_ID before running this example.")
        return

    try:
        drawings = list_drawings(
            int(project_id),
            company_id=int(company_id) if company_id else None,
            drawing_area_id=int(area_id) if area_id else None,
            discipline_id=int(discipline_id) if discipline_id else None,
            current=True,
        )
    except ProcoreError as exc:
        print(f"Could not list drawings: {exc}")
        return

    print(f"Found {len(drawings)} drawing(s).")
    for drawing in drawings:
        label = drawing.title or drawing.name or "Untitled drawing"
        print(f"- {drawing.id}: {drawing.number or 'No number'} - {label}")


if __name__ == "__main__":
    main()
