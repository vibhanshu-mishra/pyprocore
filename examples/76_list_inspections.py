"""List checklist-backed Procore inspections for a project.

PyProcore uses Procore checklist-style read endpoints for this beginner
example. Set PROCORE_COMPANY_ID and PROCORE_PROJECT_ID before running it.
"""

from __future__ import annotations

import os

from pyprocore.core.exceptions import ProcoreError
from pyprocore.services import list_inspections


def main() -> None:
    """Run the example."""
    company_id = os.getenv("PROCORE_COMPANY_ID")
    project_id = os.getenv("PROCORE_PROJECT_ID")
    if not company_id or not project_id:
        print("Set PROCORE_COMPANY_ID and PROCORE_PROJECT_ID before running this example.")
        return

    try:
        inspections = list_inspections(int(company_id), int(project_id))
    except ProcoreError as exc:
        print(f"Could not list inspections: {exc}")
        return

    print(f"Found {len(inspections)} inspections.")
    for inspection in inspections[:10]:
        title = inspection.title or inspection.name or "(untitled)"
        print(f"- {inspection.id}: {inspection.number or 'no number'} - {title}")


if __name__ == "__main__":
    main()
