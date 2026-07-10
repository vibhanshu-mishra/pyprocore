"""List Procore specification section revisions for a project.

Set PROCORE_PROJECT_ID and PROCORE_COMPANY_ID in your environment or .env file.
Optionally set PROCORE_SPECIFICATION_SECTION_ID to narrow the revision list.
"""

from __future__ import annotations

import os

from pyprocore.core.exceptions import ProcoreError
from pyprocore.services import list_specification_section_revisions


def main() -> None:
    """Run the specification revision listing example."""
    project_id = os.getenv("PROCORE_PROJECT_ID")
    company_id = os.getenv("PROCORE_COMPANY_ID")
    section_id = os.getenv("PROCORE_SPECIFICATION_SECTION_ID")
    if not project_id:
        print("Set PROCORE_PROJECT_ID before running this example.")
        return

    try:
        revisions = list_specification_section_revisions(
            int(project_id),
            company_id=int(company_id) if company_id else None,
            specification_section_id=int(section_id) if section_id else None,
            per_page=1000,
        )
    except ValueError:
        print("Project, company, and section IDs must be numbers.")
        return
    except ProcoreError as exc:
        print(f"Could not list specification revisions: {exc}")
        return

    print(f"Found {len(revisions)} specification revision(s).")
    for revision in revisions:
        print(
            f"- {revision.id}: section={revision.specification_section_id or 'unknown'} "
            f"revision={revision.revision_number or 'unknown'}"
        )


if __name__ == "__main__":
    main()
