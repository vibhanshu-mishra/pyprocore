"""Download photos from one Procore photo album.

Set PROCORE_PROJECT_ID and PROCORE_PHOTO_ALBUM_ID before running. Use
PROCORE_PHOTO_LIMIT while testing to download only a few photos.
"""

from __future__ import annotations

import os
from pathlib import Path

from pyprocore.core.exceptions import ProcoreError
from pyprocore.services import download_photo_album


def main() -> None:
    """Run the photo album download example."""
    project_id = os.getenv("PROCORE_PROJECT_ID")
    album_id = os.getenv("PROCORE_PHOTO_ALBUM_ID")
    company_id = os.getenv("PROCORE_COMPANY_ID")
    output_dir = Path(os.getenv("PROCORE_OUTPUT_DIR", "downloads/photos"))
    limit = os.getenv("PROCORE_PHOTO_LIMIT")
    if not project_id or not album_id:
        print("Set PROCORE_PROJECT_ID and PROCORE_PHOTO_ALBUM_ID before running this example.")
        return

    try:
        result = download_photo_album(
            int(project_id),
            int(album_id),
            output_dir=output_dir,
            company_id=int(company_id) if company_id else None,
            limit=int(limit) if limit else None,
        )
    except ValueError:
        print("Project, company, album, and limit values must be numbers.")
        return
    except ProcoreError as exc:
        print(f"Could not download the photo album: {exc}")
        return

    print("Photo album download summary:")
    print(f"- Requested: {result.requested}")
    print(f"- Downloaded: {len(result.downloaded_files)}")
    print(f"- Skipped: {len(result.skipped)}")
    print(f"- Errors: {len(result.errors)}")


if __name__ == "__main__":
    main()
