"""Export Procore change events to a local CSV file."""

from __future__ import annotations

import os
from pathlib import Path

from pyprocore.core.exceptions import ProcoreAPIError
from pyprocore.workflows import export_change_events_to_csv


def main() -> None:
    """Run the example."""
    company_id = int(os.environ["PROCORE_COMPANY_ID"])
    project_id = int(os.environ["PROCORE_PROJECT_ID"])
    output_path = Path(os.environ.get("PYPROCORE_OUTPUT", "exports/change_events.csv"))
    try:
        saved_path = export_change_events_to_csv(company_id, project_id, output_path)
    except ProcoreAPIError as error:
        print(f"Could not export change events: {error}")
        return
    print(f"Saved change events to {saved_path}")


if __name__ == "__main__":
    main()
