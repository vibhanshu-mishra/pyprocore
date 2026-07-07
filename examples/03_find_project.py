"""Find one Procore project by name or project number.

Set PROCORE_PROJECT_NAME or PROCORE_PROJECT_NUMBER. Set PROCORE_COMPANY_ID if
you want to search a specific company. This script makes a live Procore API call.
"""

from __future__ import annotations

import os

from pyprocore.core.exceptions import ProcoreError
from pyprocore.services import find_project


def main() -> None:
    """Run the project resolver example."""
    project_name = os.getenv("PROCORE_PROJECT_NAME")
    project_number = os.getenv("PROCORE_PROJECT_NUMBER")
    company_id_text = os.getenv("PROCORE_COMPANY_ID")

    if not project_name and not project_number:
        print("Set PROCORE_PROJECT_NAME or PROCORE_PROJECT_NUMBER before running.")
        return

    try:
        company_id = int(company_id_text) if company_id_text else None
        project = find_project(project_name, number=project_number, company_id=company_id)
    except ValueError as error:
        print(f"Project search input is not valid: {error}")
        return
    except ProcoreError as error:
        print(f"Could not find a single matching project: {error}")
        print("Try a more specific name or number.")
        return

    print("Found project:")
    print(f"- ID: {project.id}")
    print(f"- Name: {project.name or 'Unnamed project'}")
    print(f"- Number: {project.project_number or 'No project number'}")


if __name__ == "__main__":
    main()
