"""List Procore photos for a project or photo album.

Set PROCORE_PROJECT_ID before running. Optionally set PROCORE_PHOTO_ALBUM_ID to
list photos from one album. Procore calls photos "images" in the REST API.
"""

from __future__ import annotations

import os

from pyprocore.core.exceptions import ProcoreError
from pyprocore.services import list_photos


def main() -> None:
    """Run the photo listing example."""
    project_id = os.getenv("PROCORE_PROJECT_ID")
    company_id = os.getenv("PROCORE_COMPANY_ID")
    album_id = os.getenv("PROCORE_PHOTO_ALBUM_ID")
    if not project_id:
        print("Set PROCORE_PROJECT_ID before running this example.")
        return

    try:
        photos = list_photos(
            int(project_id),
            company_id=int(company_id) if company_id else None,
            album_id=int(album_id) if album_id else None,
            sort="-created_at",
        )
    except ValueError:
        print("Project, company, and album IDs must be numbers.")
        return
    except ProcoreError as exc:
        print(f"Could not list photos: {exc}")
        return

    print(f"Found {len(photos)} photo(s).")
    for photo in photos:
        label = photo.filename or photo.name or photo.image_name or "Unnamed photo"
        print(f"- {photo.id}: {label}")


if __name__ == "__main__":
    main()
