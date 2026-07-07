"""List projects for a Procore company.

Set PROCORE_COMPANY_ID in your environment or `.env` file before running.
This script makes a live Procore API call when you run it.
"""

from __future__ import annotations

import os

from pyprocore.core.exceptions import ProcoreError
from pyprocore.services import list_projects


def main() -> None:
    """Run the project listing example."""
    company_id_text = os.getenv("PROCORE_COMPANY_ID")
    if not company_id_text:
        print("Set PROCORE_COMPANY_ID before running this example.")
        return

    try:
        company_id = int(company_id_text)
        projects = list_projects(company_id)
    except ValueError:
        print("PROCORE_COMPANY_ID must be a number.")
        return
    except ProcoreError as error:
        print(f"Could not list projects: {error}")
        print("Check your company ID, OAuth token, and Procore permissions.")
        return

    if not projects:
        print(f"No projects were returned for company {company_id}.")
        return

    print(f"Projects for company {company_id}:")
    for project in projects:
        number = f" ({project.project_number})" if project.project_number else ""
        print(f"- {project.id}: {project.name or 'Unnamed project'}{number}")


if __name__ == "__main__":
    main()
