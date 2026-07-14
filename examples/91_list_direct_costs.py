"""List Procore direct costs for a project."""

from __future__ import annotations

import os

from pyprocore.core.exceptions import ProcoreAPIError
from pyprocore.services.financials import list_direct_costs


def main() -> None:
    """Run the example."""
    company_id = int(os.environ["PROCORE_COMPANY_ID"])
    project_id = int(os.environ["PROCORE_PROJECT_ID"])
    try:
        costs = list_direct_costs(company_id, project_id)
    except ProcoreAPIError as error:
        print(f"Could not list direct costs: {error}")
        return
    print(f"Found {len(costs)} direct costs.")
    for cost in costs[:10]:
        print(f"- {cost.number or cost.id}: {cost.title or cost.name}")


if __name__ == "__main__":
    main()
