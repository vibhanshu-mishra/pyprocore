"""Export read-only prime contracts to CSV.

Set PROCORE_PROJECT_ID and optionally PROCORE_COMPANY_ID before running.
"""

from __future__ import annotations

import os
from pathlib import Path

from pyprocore import export_prime_contracts_to_csv
from pyprocore.core.exceptions import ProcoreAPIError


def main() -> None:
    """Run the prime contracts export example."""
    project_id = int(os.environ["PROCORE_PROJECT_ID"])
    company_id = int(os.environ["PROCORE_COMPANY_ID"]) if os.getenv("PROCORE_COMPANY_ID") else None
    output_path = Path("exports/prime-contracts.csv")
    try:
        saved_path = export_prime_contracts_to_csv(company_id, project_id, output_path)
    except ProcoreAPIError as exc:
        print(f"Could not export prime contracts: {exc}")
        return
    print(f"Saved prime contracts to {saved_path}")


if __name__ == "__main__":
    main()
