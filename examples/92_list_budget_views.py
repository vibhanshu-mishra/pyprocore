"""List Procore budget views for a project."""

from __future__ import annotations

import os

from pyprocore.core.exceptions import ProcoreAPIError
from pyprocore.services.financials import list_budget_views


def main() -> None:
    """Run the example."""
    company_id = int(os.environ["PROCORE_COMPANY_ID"])
    project_id = int(os.environ["PROCORE_PROJECT_ID"])
    try:
        views = list_budget_views(company_id, project_id)
    except ProcoreAPIError as error:
        print(f"Could not list budget views: {error}")
        return
    print(f"Found {len(views)} budget views.")
    for view in views:
        print(f"- {view.id}: {view.name}")


if __name__ == "__main__":
    main()
