"""Export checklist-backed Procore inspections to a local CSV file."""

from __future__ import annotations

import os
from pathlib import Path

from pyprocore.core.exceptions import ProcoreError
from pyprocore.workflows import export_inspections_to_csv


def main() -> None:
    """Run the example."""
    company_id = os.getenv("PROCORE_COMPANY_ID")
    project_id = os.getenv("PROCORE_PROJECT_ID")
    output_path = Path(os.getenv("PROCORE_OUTPUT_PATH", "exports/inspections.csv"))
    if not company_id or not project_id:
        print("Set PROCORE_COMPANY_ID and PROCORE_PROJECT_ID before running this example.")
        return

    try:
        saved_path = export_inspections_to_csv(int(company_id), int(project_id), output_path)
    except ProcoreError as exc:
        print(f"Could not export inspections: {exc}")
        return

    print(f"Inspection export written to: {saved_path}")


if __name__ == "__main__":
    main()
