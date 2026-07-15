"""List read-only owner invoices/payment applications for a prime contract."""

from __future__ import annotations

import os

from pyprocore import list_owner_invoices
from pyprocore.core.exceptions import ProcoreAPIError


def main() -> None:
    """Run the owner invoices example."""
    project_id = int(os.environ["PROCORE_PROJECT_ID"])
    prime_contract_id = int(os.environ["PROCORE_PRIME_CONTRACT_ID"])
    company_id = int(os.environ["PROCORE_COMPANY_ID"]) if os.getenv("PROCORE_COMPANY_ID") else None
    try:
        invoices = list_owner_invoices(company_id, project_id, prime_contract_id)
    except ProcoreAPIError as exc:
        print(f"Could not list owner invoices: {exc}")
        return
    print(f"Found {len(invoices)} owner invoice(s).")


if __name__ == "__main__":
    main()
