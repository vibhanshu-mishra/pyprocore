"""List Procore company cost codes."""

from __future__ import annotations

import os

from pyprocore.core.exceptions import ProcoreAPIError
from pyprocore.services.financials import list_cost_codes


def main() -> None:
    """Run the example."""
    company_id = int(os.environ["PROCORE_COMPANY_ID"])
    try:
        codes = list_cost_codes(company_id)
    except ProcoreAPIError as error:
        print(f"Could not list cost codes: {error}")
        return
    print(f"Found {len(codes)} cost codes.")
    for code in codes[:10]:
        print(f"- {code.code or code.id}: {code.name}")


if __name__ == "__main__":
    main()
