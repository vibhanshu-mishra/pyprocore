"""Fetch one Procore photo by ID.

Set PROCORE_PROJECT_ID and PROCORE_PHOTO_ID before running this example. This
script prints basic metadata and does not download the photo.
"""

from __future__ import annotations

import os

from pyprocore.core.exceptions import ProcoreError
from pyprocore.services import get_photo


def main() -> None:
    """Run the get-photo example."""
    project_id = os.getenv("PROCORE_PROJECT_ID")
    photo_id = os.getenv("PROCORE_PHOTO_ID")
    company_id = os.getenv("PROCORE_COMPANY_ID")
    if not project_id or not photo_id:
        print("Set PROCORE_PROJECT_ID and PROCORE_PHOTO_ID before running this example.")
        return

    try:
        photo = get_photo(
            int(project_id),
            int(photo_id),
            company_id=int(company_id) if company_id else None,
        )
    except ValueError:
        print("PROCORE_PROJECT_ID, PROCORE_COMPANY_ID, and PROCORE_PHOTO_ID must be numbers.")
        return
    except ProcoreError as exc:
        print(f"Could not fetch the photo: {exc}")
        return

    print("Photo details:")
    print(f"- ID: {photo.id}")
    print(f"- Filename: {photo.filename or photo.name or 'Not provided'}")
    print(f"- Description: {photo.description or 'Not provided'}")
    print(f"- Album ID: {photo.image_category_id or 'Not provided'}")


if __name__ == "__main__":
    main()
