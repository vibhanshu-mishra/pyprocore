"""Export read-only project tasks to CSV.

Set PROCORE_PROJECT_ID and optionally PROCORE_COMPANY_ID/PROCORE_OUTPUT_DIR
before running. This example makes a live Procore call only when executed
directly.
"""

from __future__ import annotations

import os
from pathlib import Path

from pyprocore import export_tasks_to_csv
from pyprocore.core.exceptions import ProcoreAPIError


def main() -> None:
    """Run the task export example."""
    project_id = int(os.environ["PROCORE_PROJECT_ID"])
    company_id = int(os.environ["PROCORE_COMPANY_ID"]) if os.getenv("PROCORE_COMPANY_ID") else None
    output_dir = Path(os.getenv("PROCORE_OUTPUT_DIR", "example-output"))
    output_path = output_dir / "tasks.csv"
    try:
        saved_path = export_tasks_to_csv(company_id, project_id, output_path)
    except ProcoreAPIError as exc:
        print(f"Could not export tasks: {exc}")
        return
    print(f"Tasks exported to {saved_path}")


if __name__ == "__main__":
    main()
