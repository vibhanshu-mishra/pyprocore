"""Export project RFIs to a CSV file.

Set PROCORE_PROJECT_ID before running this example. You can optionally set
PROCORE_RFI_STATUS and PROCORE_OUTPUT_DIR. This script makes a live Procore API
call when you run it.
"""

from __future__ import annotations

import os
from pathlib import Path

from pyprocore.core.exceptions import ProcoreError
from pyprocore.workflows import export_rfis_to_csv


def main() -> None:
    """Run the RFI CSV export example."""
    project_id_text = os.getenv("PROCORE_PROJECT_ID")
    if not project_id_text:
        print("Set PROCORE_PROJECT_ID before running this example.")
        return

    output_dir = Path(os.getenv("PROCORE_OUTPUT_DIR", "exports"))
    output_path = output_dir / "rfis.csv"

    try:
        saved_path = export_rfis_to_csv(
            int(project_id_text),
            output_path,
            status=os.getenv("PROCORE_RFI_STATUS"),
        )
    except ValueError:
        print("PROCORE_PROJECT_ID must be a number.")
        return
    except ProcoreError as error:
        print(f"Could not export RFIs: {error}")
        print("Check your OAuth token, project ID, and Procore permissions.")
        return

    print(f"RFI CSV export saved to: {saved_path}")


if __name__ == "__main__":
    main()
