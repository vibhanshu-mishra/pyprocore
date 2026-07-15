"""List read-only contract payments for a Procore project."""

from __future__ import annotations

import os

from pyprocore import list_contract_payments
from pyprocore.core.exceptions import ProcoreAPIError


def main() -> None:
    """Run the contract payments example."""
    project_id = int(os.environ["PROCORE_PROJECT_ID"])
    company_id = int(os.environ["PROCORE_COMPANY_ID"]) if os.getenv("PROCORE_COMPANY_ID") else None
    try:
        payments = list_contract_payments(company_id, project_id)
    except ProcoreAPIError as exc:
        print(f"Could not list contract payments: {exc}")
        return
    print(f"Found {len(payments)} contract payment(s).")


if __name__ == "__main__":
    main()
