"""Download one Procore photo when the payload includes a full-size URL.

Set PROCORE_PROJECT_ID and PROCORE_PHOTO_ID before running. The file is saved to
PROCORE_OUTPUT_DIR or downloads/photos by default.
"""

from __future__ import annotations

import os
from pathlib import Path

from pyprocore.core.exceptions import ProcoreError
from pyprocore.services import download_photo


def main() -> None:
    """Run the photo download example."""
    project_id = os.getenv("PROCORE_PROJECT_ID")
    photo_id = os.getenv("PROCORE_PHOTO_ID")
    company_id = os.getenv("PROCORE_COMPANY_ID")
    output_dir = Path(os.getenv("PROCORE_OUTPUT_DIR", "downloads/photos"))
    if not project_id or not photo_id:
        print("Set PROCORE_PROJECT_ID and PROCORE_PHOTO_ID before running this example.")
        return

    try:
        saved_path = download_photo(
            int(project_id),
            int(photo_id),
            output_dir=output_dir,
            company_id=int(company_id) if company_id else None,
        )
    except ValueError:
        print("PROCORE_PROJECT_ID, PROCORE_COMPANY_ID, and PROCORE_PHOTO_ID must be numbers.")
        return
    except ProcoreError as exc:
        print(f"Could not download the photo: {exc}")
        return

    print(f"Photo saved to: {saved_path}")


if __name__ == "__main__":
    main()
