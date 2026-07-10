"""Download one Procore specification section revision.

Set PROCORE_PROJECT_ID and PROCORE_SPECIFICATION_REVISION_ID before running.
The file is saved to PROCORE_OUTPUT_DIR or downloads/specifications by default.
"""

from __future__ import annotations

import os
from pathlib import Path

from pyprocore.core.exceptions import ProcoreError
from pyprocore.services import download_specification_section_revision


def main() -> None:
    """Run the specification revision download example."""
    project_id = os.getenv("PROCORE_PROJECT_ID")
    revision_id = os.getenv("PROCORE_SPECIFICATION_REVISION_ID")
    company_id = os.getenv("PROCORE_COMPANY_ID")
    output_dir = Path(os.getenv("PROCORE_OUTPUT_DIR", "downloads/specifications"))
    if not project_id or not revision_id:
        print(
            "Set PROCORE_PROJECT_ID and PROCORE_SPECIFICATION_REVISION_ID "
            "before running this example."
        )
        return

    try:
        saved_path = download_specification_section_revision(
            int(project_id),
            int(revision_id),
            output_dir=output_dir,
            company_id=int(company_id) if company_id else None,
        )
    except ValueError:
        print("PROCORE_PROJECT_ID, PROCORE_COMPANY_ID, and revision ID must be numbers.")
        return
    except ProcoreError as exc:
        print(f"Could not download the specification revision: {exc}")
        return

    print(f"Specification revision saved to: {saved_path}")


if __name__ == "__main__":
    main()
