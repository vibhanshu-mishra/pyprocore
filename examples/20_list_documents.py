"""List Procore documents for a project.

Set PROCORE_PROJECT_ID in your environment or .env file before running this
example. Optionally set PROCORE_DOCUMENT_FOLDER_ID to list one folder.
"""

from __future__ import annotations

import os

from pyprocore.core.exceptions import ProcoreError
from pyprocore.services import list_documents


def main() -> None:
    """Run the document listing example."""
    project_id = os.getenv("PROCORE_PROJECT_ID")
    folder_id = os.getenv("PROCORE_DOCUMENT_FOLDER_ID")
    if not project_id:
        print("Set PROCORE_PROJECT_ID before running this example.")
        return

    try:
        documents = list_documents(
            int(project_id),
            folder_id=int(folder_id) if folder_id else None,
        )
    except ProcoreError as exc:
        print(f"Could not list documents: {exc}")
        return

    print(f"Found {len(documents)} document(s).")
    for document in documents:
        label = document.filename or document.file_name or document.name or "Untitled document"
        print(f"- {document.id}: {label}")


if __name__ == "__main__":
    main()
