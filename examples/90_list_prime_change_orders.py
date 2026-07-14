"""List Procore prime change orders for a project."""

from __future__ import annotations

import os

from pyprocore.core.exceptions import ProcoreAPIError
from pyprocore.services.financials import list_prime_change_orders


def main() -> None:
    """Run the example."""
    company_id = int(os.environ["PROCORE_COMPANY_ID"])
    project_id = int(os.environ["PROCORE_PROJECT_ID"])
    try:
        orders = list_prime_change_orders(company_id, project_id)
    except ProcoreAPIError as error:
        print(f"Could not list prime change orders: {error}")
        return
    print(f"Found {len(orders)} prime change orders.")
    for order in orders[:10]:
        print(f"- {order.number or order.id}: {order.title or order.name}")


if __name__ == "__main__":
    main()
