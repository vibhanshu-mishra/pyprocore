"""Use the object-oriented Procore client interface.

This example shows the `from pyprocore import Procore` style. It lists
projects for PROCORE_COMPANY_ID when that value is set, otherwise it lists
companies available to the authenticated user.

This script makes a live Procore API call when you run it.
"""

from __future__ import annotations

import os

from pyprocore import Procore
from pyprocore.core.exceptions import ProcoreError


def main() -> None:
    """Run the object-oriented client example."""
    client = Procore()
    company_id_text = os.getenv("PROCORE_COMPANY_ID")

    if company_id_text:
        try:
            company_id = int(company_id_text)
            projects = client.projects.list(company_id=company_id)
        except ValueError:
            print("PROCORE_COMPANY_ID must be a number.")
            return
        except ProcoreError as error:
            print(f"Could not list projects: {error}")
            print("Check your company ID, OAuth token, and Procore permissions.")
            return

        print(f"Projects for company {company_id}:")
        for project in projects:
            print(f"- {project.id}: {project.name or 'Unnamed project'}")
        return

    try:
        companies = client.companies.list()
    except ProcoreError as error:
        print(f"Could not list companies: {error}")
        print("Check your OAuth token and Procore permissions.")
        return

    print("Companies available to your Procore user:")
    for company in companies:
        print(f"- {company.id}: {company.name or 'Unnamed company'}")


if __name__ == "__main__":
    main()
