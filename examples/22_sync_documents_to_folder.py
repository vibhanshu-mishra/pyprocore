"""Sync Procore documents into a local folder.

Set PROCORE_PROJECT_ID in your environment or .env file before running this
example. Optionally set PROCORE_DOCUMENT_FOLDER_ID, PROCORE_OUTPUT_DIR,
PROCORE_DRY_RUN, or PROCORE_INCREMENTAL.
"""

from __future__ import annotations

import os
from pathlib import Path

from pyprocore.core.exceptions import ProcoreError
from pyprocore.workflows import sync_documents_to_folder


def _enabled(value: str | None) -> bool:
    """Return whether an environment flag is truthy."""
    return str(value or "").casefold() in {"1", "true", "yes", "on"}


def main() -> None:
    """Run the document folder sync example."""
    project_id = os.getenv("PROCORE_PROJECT_ID")
    folder_id = os.getenv("PROCORE_DOCUMENT_FOLDER_ID")
    output_dir = Path(os.getenv("PROCORE_OUTPUT_DIR", "downloads/project-documents"))
    if not project_id:
        print("Set PROCORE_PROJECT_ID before running this example.")
        return

    try:
        result = sync_documents_to_folder(
            int(project_id),
            output_dir,
            folder_id=int(folder_id) if folder_id else None,
            dry_run=_enabled(os.getenv("PROCORE_DRY_RUN")),
            incremental=_enabled(os.getenv("PROCORE_INCREMENTAL")),
        )
    except ProcoreError as exc:
        print(f"Could not sync documents: {exc}")
        return

    action = "planned" if result.dry_run else "synced"
    print(f"Documents {action}: {result.synced_count}")
    print(f"Skipped: {result.skipped_count}")
    print(f"Output folder: {result.output_dir}")


if __name__ == "__main__":
    main()
