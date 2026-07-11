"""List Procore photo albums for a project.

Procore calls photo albums "image categories" in the REST API. Set
PROCORE_PROJECT_ID and PROCORE_COMPANY_ID before running this example.
"""

from __future__ import annotations

import os

from pyprocore.core.exceptions import ProcoreError
from pyprocore.services import list_photo_albums


def main() -> None:
    """Run the photo album listing example."""
    project_id = os.getenv("PROCORE_PROJECT_ID")
    company_id = os.getenv("PROCORE_COMPANY_ID")
    if not project_id:
        print("Set PROCORE_PROJECT_ID before running this example.")
        return

    try:
        albums = list_photo_albums(
            int(project_id),
            company_id=int(company_id) if company_id else None,
        )
    except ValueError:
        print("PROCORE_PROJECT_ID and PROCORE_COMPANY_ID must be numbers.")
        return
    except ProcoreError as exc:
        print(f"Could not list photo albums: {exc}")
        return

    print(f"Found {len(albums)} photo album(s).")
    for album in albums:
        print(f"- {album.id}: {album.name or 'Unnamed album'}")


if __name__ == "__main__":
    main()
