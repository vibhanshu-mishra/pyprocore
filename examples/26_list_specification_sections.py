"""List Procore specification sections for a project.

Set PROCORE_PROJECT_ID and PROCORE_COMPANY_ID in your environment or .env file
before running this example. Optional filters include PROCORE_SPECIFICATION_SET_ID,
PROCORE_SPECIFICATION_AREA_ID, and PROCORE_SPECIFICATION_DIVISION_ID.
"""

from __future__ import annotations

import os

from pyprocore.core.exceptions import ProcoreError
from pyprocore.services import list_specification_sections


def main() -> None:
    """Run the specification section listing example."""
    project_id = os.getenv("PROCORE_PROJECT_ID")
    company_id = os.getenv("PROCORE_COMPANY_ID")
    set_id = os.getenv("PROCORE_SPECIFICATION_SET_ID")
    area_id = os.getenv("PROCORE_SPECIFICATION_AREA_ID")
    division_id = os.getenv("PROCORE_SPECIFICATION_DIVISION_ID")
    if not project_id:
        print("Set PROCORE_PROJECT_ID before running this example.")
        return

    try:
        sections = list_specification_sections(
            int(project_id),
            company_id=int(company_id) if company_id else None,
            specification_set_id=int(set_id) if set_id else None,
            specification_area_id=int(area_id) if area_id else None,
            division_id=int(division_id) if division_id else None,
            sort="number",
        )
    except ValueError:
        print("Project, company, set, area, and division IDs must be numbers.")
        return
    except ProcoreError as exc:
        print(f"Could not list specification sections: {exc}")
        return

    print(f"Found {len(sections)} specification section(s).")
    for section in sections:
        print(f"- {section.id}: {section.number or 'No number'} - {section.title or 'Untitled'}")


if __name__ == "__main__":
    main()
