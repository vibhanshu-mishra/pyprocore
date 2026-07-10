"""Download one Procore drawing when Procore provides a direct URL.

Set PROCORE_PROJECT_ID and PROCORE_DRAWING_ID in your environment or .env file
before running this example. If you know it, set PROCORE_DRAWING_AREA_ID so the
SDK can use Procore's direct drawing-area endpoint.
"""

from __future__ import annotations

import os
from pathlib import Path

from pyprocore.core.exceptions import ProcoreError
from pyprocore.services import download_drawing


def main() -> None:
    """Run the drawing download example."""
    project_id = os.getenv("PROCORE_PROJECT_ID")
    drawing_area_id = os.getenv("PROCORE_DRAWING_AREA_ID")
    drawing_id = os.getenv("PROCORE_DRAWING_ID")
    company_id = os.getenv("PROCORE_COMPANY_ID")
    output_dir = Path(os.getenv("PROCORE_OUTPUT_DIR", "downloads/drawings"))
    if not project_id or not drawing_id:
        print("Set PROCORE_PROJECT_ID and PROCORE_DRAWING_ID before running this example.")
        return

    try:
        saved_path = download_drawing(
            int(project_id),
            int(drawing_id),
            output_dir=output_dir,
            company_id=int(company_id) if company_id else None,
            drawing_area_id=int(drawing_area_id) if drawing_area_id else None,
        )
    except ProcoreError as exc:
        print(f"Could not download the drawing: {exc}")
        return

    print(f"Drawing saved to: {saved_path}")


if __name__ == "__main__":
    main()
