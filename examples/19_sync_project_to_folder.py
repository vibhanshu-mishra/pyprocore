"""Sync RFIs and submittals for one project into a local folder.

Set PROCORE_PROJECT_ID before running this example. You can optionally set
PROCORE_RFI_STATUS or PROCORE_SUBMITTAL_STATUS through PROCORE_STATUS,
PROCORE_OUTPUT_DIR, PROCORE_NO_DOWNLOADS=1, and PROCORE_DRY_RUN=1. This script
makes live Procore API calls when you run it.
"""

from __future__ import annotations

import os
from pathlib import Path

from pyprocore.core.exceptions import ProcoreError
from pyprocore.workflows import sync_project_to_folder


def main() -> None:
    """Run the combined project sync example."""
    project_id_text = os.getenv("PROCORE_PROJECT_ID")
    if not project_id_text:
        print("Set PROCORE_PROJECT_ID before running this example.")
        return

    output_dir = Path(os.getenv("PROCORE_OUTPUT_DIR", "exports")) / "project-sync"

    try:
        result = sync_project_to_folder(
            int(project_id_text),
            output_dir,
            status=os.getenv("PROCORE_STATUS"),
            download_attachments=os.getenv("PROCORE_NO_DOWNLOADS") != "1",
            dry_run=os.getenv("PROCORE_DRY_RUN") == "1",
            incremental=True,
        )
    except ValueError:
        print("PROCORE_PROJECT_ID must be a number.")
        return
    except ProcoreError as error:
        print(f"Could not sync the project: {error}")
        return

    print(f"Project sync output: {result.output_dir}")
    print(f"Items found: {result.item_count}")
    print(f"Items synced: {result.synced_count}")
    print(f"Items skipped: {result.skipped_count}")
    print(f"Summary: {result.summary_path or 'not written during dry run'}")


if __name__ == "__main__":
    main()
