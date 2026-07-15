"""List read-only billing periods for a Procore project."""

from __future__ import annotations

import os

from pyprocore import list_billing_periods
from pyprocore.core.exceptions import ProcoreAPIError


def main() -> None:
    """Run the billing periods example."""
    project_id = int(os.environ["PROCORE_PROJECT_ID"])
    company_id = int(os.environ["PROCORE_COMPANY_ID"]) if os.getenv("PROCORE_COMPANY_ID") else None
    try:
        periods = list_billing_periods(company_id, project_id)
    except ProcoreAPIError as exc:
        print(f"Could not list billing periods: {exc}")
        return
    print(f"Found {len(periods)} billing period(s).")


if __name__ == "__main__":
    main()
