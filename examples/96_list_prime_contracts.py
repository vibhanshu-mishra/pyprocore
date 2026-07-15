"""List read-only prime contracts for a Procore project.

Set PROCORE_PROJECT_ID and optionally PROCORE_COMPANY_ID before running.
This example makes a live Procore call only when executed directly.
"""

from __future__ import annotations

import os

from pyprocore import list_prime_contracts
from pyprocore.core.exceptions import ProcoreAPIError


def main() -> None:
    """Run the prime contracts example."""
    project_id = int(os.environ["PROCORE_PROJECT_ID"])
    company_id = int(os.environ["PROCORE_COMPANY_ID"]) if os.getenv("PROCORE_COMPANY_ID") else None
    try:
        contracts = list_prime_contracts(company_id, project_id)
    except ProcoreAPIError as exc:
        print(f"Could not list prime contracts: {exc}")
        return
    print(f"Found {len(contracts)} prime contract(s).")
    for contract in contracts:
        print(f"- {contract.id}: {contract.number or contract.name or contract.title}")


if __name__ == "__main__":
    main()
