"""Fetch one Procore specification section by project ID and section ID.

Set PROCORE_PROJECT_ID and PROCORE_SPECIFICATION_SECTION_ID before running.
This example uses PyProcore's conservative list-and-match lookup because the
direct specification section show endpoint is pending live verification.
"""

from __future__ import annotations

import os

from pyprocore.core.exceptions import ProcoreError
from pyprocore.services import get_specification_section


def main() -> None:
    """Run the get-specification-section example."""
    project_id = os.getenv("PROCORE_PROJECT_ID")
    section_id = os.getenv("PROCORE_SPECIFICATION_SECTION_ID")
    company_id = os.getenv("PROCORE_COMPANY_ID")
    if not project_id or not section_id:
        print(
            "Set PROCORE_PROJECT_ID and PROCORE_SPECIFICATION_SECTION_ID "
            "before running this example."
        )
        return

    try:
        section = get_specification_section(
            int(project_id),
            int(section_id),
            company_id=int(company_id) if company_id else None,
        )
    except ValueError:
        print("PROCORE_PROJECT_ID, PROCORE_COMPANY_ID, and section ID must be numbers.")
        return
    except ProcoreError as exc:
        print(f"Could not fetch the specification section: {exc}")
        return

    print("Specification section details:")
    print(f"- ID: {section.id}")
    print(f"- Number: {section.number or 'No number'}")
    print(f"- Title: {section.title or 'Untitled'}")
    print(f"- Current revision ID: {section.current_revision_id or 'Not provided'}")


if __name__ == "__main__":
    main()
