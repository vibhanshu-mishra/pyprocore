"""Fetch one submittal by project ID and submittal ID.

Set PROCORE_PROJECT_ID and PROCORE_SUBMITTAL_ID before running. This script
makes a live Procore API call.
"""

from __future__ import annotations

import os

from pyprocore.core.exceptions import ProcoreError
from pyprocore.services import get_submittal


def main() -> None:
    """Run the get-submittal example."""
    project_id_text = os.getenv("PROCORE_PROJECT_ID")
    submittal_id_text = os.getenv("PROCORE_SUBMITTAL_ID")
    if not project_id_text or not submittal_id_text:
        print("Set PROCORE_PROJECT_ID and PROCORE_SUBMITTAL_ID before running.")
        return

    try:
        project_id = int(project_id_text)
        submittal_id = int(submittal_id_text)
        submittal = get_submittal(project_id, submittal_id)
    except ValueError:
        print("PROCORE_PROJECT_ID and PROCORE_SUBMITTAL_ID must be numbers.")
        return
    except ProcoreError as error:
        print(f"Could not fetch the submittal: {error}")
        return

    print("Submittal details:")
    print(f"- ID: {submittal.id}")
    print(f"- Number: {submittal.number or 'No number'}")
    print(f"- Title: {submittal.title or 'No title'}")
    print(f"- Attachments: {len(submittal.attachments)}")


if __name__ == "__main__":
    main()
