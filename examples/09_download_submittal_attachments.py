"""Download attachments from one submittal.

Set PROCORE_PROJECT_ID and PROCORE_SUBMITTAL_ID before running. Optionally set
PROCORE_OUTPUT_DIR. This script makes live Procore API and download requests.
"""

from __future__ import annotations

import os
from pathlib import Path

from pyprocore.core.exceptions import ProcoreError
from pyprocore.services import download_submittal_attachments


def main() -> None:
    """Run the submittal attachment download example."""
    project_id_text = os.getenv("PROCORE_PROJECT_ID")
    submittal_id_text = os.getenv("PROCORE_SUBMITTAL_ID")
    output_dir = os.getenv("PROCORE_OUTPUT_DIR")
    if not project_id_text or not submittal_id_text:
        print("Set PROCORE_PROJECT_ID and PROCORE_SUBMITTAL_ID before running.")
        return

    try:
        project_id = int(project_id_text)
        submittal_id = int(submittal_id_text)
        paths = download_submittal_attachments(
            project_id,
            submittal_id,
            Path(output_dir) if output_dir else None,
        )
    except ValueError:
        print("PROCORE_PROJECT_ID and PROCORE_SUBMITTAL_ID must be numbers.")
        return
    except ProcoreError as error:
        print(f"Could not download submittal attachments: {error}")
        return

    if not paths:
        print("No submittal attachments were downloaded.")
        return

    print("Downloaded submittal attachments:")
    for path in paths:
        print(f"- {path}")


if __name__ == "__main__":
    main()
