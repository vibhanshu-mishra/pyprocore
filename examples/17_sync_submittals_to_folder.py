"""Sync project submittals into a local folder tree.

Set PROCORE_PROJECT_ID before running this example. You can optionally set
PROCORE_SUBMITTAL_STATUS, PROCORE_OUTPUT_DIR, PROCORE_NO_DOWNLOADS=1, and
PROCORE_DRY_RUN=1. This script makes live Procore API calls when you run it.
"""

from __future__ import annotations

import os
from pathlib import Path

from pyprocore.core.exceptions import ProcoreError
from pyprocore.workflows import sync_submittals_to_folder


def main() -> None:
    """Run the submittal folder sync example."""
    project_id_text = os.getenv("PROCORE_PROJECT_ID")
    if not project_id_text:
        print("Set PROCORE_PROJECT_ID before running this example.")
        return

    output_dir = Path(os.getenv("PROCORE_OUTPUT_DIR", "exports")) / "submittal-sync"

    try:
        result = sync_submittals_to_folder(
            int(project_id_text),
            output_dir,
            status=os.getenv("PROCORE_SUBMITTAL_STATUS"),
            download_attachments=os.getenv("PROCORE_NO_DOWNLOADS") != "1",
            dry_run=os.getenv("PROCORE_DRY_RUN") == "1",
        )
    except ValueError:
        print("PROCORE_PROJECT_ID must be a number.")
        return
    except ProcoreError as error:
        print(f"Could not sync submittals: {error}")
        print("Check your OAuth token, project ID, and Procore permissions.")
        return

    action = "Planned" if result.dry_run else "Synced"
    print(f"{action} {result.item_count} submittals for: {result.output_dir}")
    print(f"Manifest: {result.manifest_path or 'not written during dry run'}")
    if result.tracker_path:
        print(f"Tracker CSV: {result.tracker_path}")


if __name__ == "__main__":
    main()
