"""List submittals for a Procore project.

Set PROCORE_PROJECT_ID before running. Optionally set PROCORE_SUBMITTAL_STATUS
to filter by status. This script makes a live Procore API call.
"""

from __future__ import annotations

import os

from pyprocore.core.exceptions import ProcoreError
from pyprocore.services import list_submittals


def main() -> None:
    """Run the submittal listing example."""
    project_id_text = os.getenv("PROCORE_PROJECT_ID")
    if not project_id_text:
        print("Set PROCORE_PROJECT_ID before running this example.")
        return

    try:
        project_id = int(project_id_text)
        status = os.getenv("PROCORE_SUBMITTAL_STATUS")
        submittals = list_submittals(project_id, status=status)
    except ValueError:
        print("PROCORE_PROJECT_ID must be a number.")
        return
    except ProcoreError as error:
        print(f"Could not list submittals: {error}")
        print("Check the project ID and your Procore permissions.")
        return

    if not submittals:
        print(f"No submittals were returned for project {project_id}.")
        return

    filter_text = f" with status {status!r}" if status else ""
    print(f"Submittals for project {project_id}{filter_text}:")
    for submittal in submittals:
        print(
            f"- {submittal.id}: "
            f"#{submittal.number or 'No number'} - {submittal.title or 'No title'}"
        )


if __name__ == "__main__":
    main()
