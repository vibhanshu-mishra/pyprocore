"""Download one Procore document.

Set PROCORE_PROJECT_ID and PROCORE_DOCUMENT_ID in your environment or .env file
before running this example.
"""

from __future__ import annotations

import os
from pathlib import Path

from pyprocore.core.exceptions import ProcoreError
from pyprocore.services import download_document


def main() -> None:
    """Run the document download example."""
    project_id = os.getenv("PROCORE_PROJECT_ID")
    document_id = os.getenv("PROCORE_DOCUMENT_ID")
    output_dir = Path(os.getenv("PROCORE_OUTPUT_DIR", "downloads/documents"))
    if not project_id or not document_id:
        print("Set PROCORE_PROJECT_ID and PROCORE_DOCUMENT_ID before running this example.")
        return

    try:
        saved_path = download_document(
            int(project_id),
            int(document_id),
            output_dir=output_dir,
        )
    except ProcoreError as exc:
        print(f"Could not download the document: {exc}")
        return

    print(f"Document saved to: {saved_path}")


if __name__ == "__main__":
    main()
