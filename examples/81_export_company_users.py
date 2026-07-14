"""Export company directory users to CSV.

Set PROCORE_COMPANY_ID and optionally PROCORE_OUTPUT_PATH. The default output
path is exports/company-users.csv.
"""

from __future__ import annotations

import os
from pathlib import Path

from pyprocore.core.exceptions import ProcoreError
from pyprocore.workflows import export_company_users_to_csv


def main() -> None:
    """Run the example."""
    company_id = os.getenv("PROCORE_COMPANY_ID")
    output_path = Path(os.getenv("PROCORE_OUTPUT_PATH", "exports/company-users.csv"))
    if not company_id:
        print("Set PROCORE_COMPANY_ID before exporting company users.")
        return

    try:
        saved_path = export_company_users_to_csv(int(company_id), output_path)
    except ProcoreError as exc:
        print(f"Could not export company users: {exc}")
        return

    print(f"Company users exported to {saved_path}")


if __name__ == "__main__":
    main()
