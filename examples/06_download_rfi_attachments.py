"""Download attachments from one RFI.

Set PROCORE_PROJECT_ID and PROCORE_RFI_ID before running. Optionally set
PROCORE_OUTPUT_DIR. This script makes live Procore API and download requests.
"""

from __future__ import annotations

import os
from pathlib import Path

from pyprocore.core.exceptions import ProcoreError
from pyprocore.services import download_rfi_attachments


def main() -> None:
    """Run the RFI attachment download example."""
    project_id_text = os.getenv("PROCORE_PROJECT_ID")
    rfi_id_text = os.getenv("PROCORE_RFI_ID")
    output_dir = os.getenv("PROCORE_OUTPUT_DIR")
    if not project_id_text or not rfi_id_text:
        print("Set PROCORE_PROJECT_ID and PROCORE_RFI_ID before running.")
        return

    try:
        project_id = int(project_id_text)
        rfi_id = int(rfi_id_text)
        paths = download_rfi_attachments(
            project_id,
            rfi_id,
            Path(output_dir) if output_dir else None,
        )
    except ValueError:
        print("PROCORE_PROJECT_ID and PROCORE_RFI_ID must be numbers.")
        return
    except ProcoreError as error:
        print(f"Could not download RFI attachments: {error}")
        return

    if not paths:
        print("No RFI attachments were downloaded.")
        return

    print("Downloaded RFI attachments:")
    for path in paths:
        print(f"- {path}")


if __name__ == "__main__":
    main()
