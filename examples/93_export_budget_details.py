"""Export budget detail rows for one Procore budget view."""

from __future__ import annotations

import os
from pathlib import Path

from pyprocore.core.exceptions import ProcoreAPIError
from pyprocore.workflows import export_budget_details_to_csv


def main() -> None:
    """Run the example."""
    company_id = int(os.environ["PROCORE_COMPANY_ID"])
    project_id = int(os.environ["PROCORE_PROJECT_ID"])
    budget_view_id = int(os.environ["PROCORE_BUDGET_VIEW_ID"])
    output_path = Path(os.environ.get("PYPROCORE_OUTPUT", "exports/budget_details.csv"))
    try:
        saved_path = export_budget_details_to_csv(
            company_id,
            project_id,
            budget_view_id,
            output_path,
        )
    except ProcoreAPIError as error:
        print(f"Could not export budget details: {error}")
        return
    print(f"Saved budget details to {saved_path}")


if __name__ == "__main__":
    main()
