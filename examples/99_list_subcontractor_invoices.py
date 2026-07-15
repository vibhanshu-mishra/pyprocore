"""List read-only subcontractor invoices/requisitions for a project."""

from __future__ import annotations

import os

from pyprocore import list_subcontractor_invoices
from pyprocore.core.exceptions import ProcoreAPIError


def main() -> None:
    """Run the subcontractor invoices example."""
    project_id = int(os.environ["PROCORE_PROJECT_ID"])
    company_id = int(os.environ["PROCORE_COMPANY_ID"]) if os.getenv("PROCORE_COMPANY_ID") else None
    try:
        invoices = list_subcontractor_invoices(company_id, project_id)
    except ProcoreAPIError as exc:
        print(f"Could not list subcontractor invoices: {exc}")
        return
    print(f"Found {len(invoices)} subcontractor invoice(s).")


if __name__ == "__main__":
    main()
