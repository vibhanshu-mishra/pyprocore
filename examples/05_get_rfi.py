"""Fetch one RFI by project ID and RFI ID.

Set PROCORE_PROJECT_ID and PROCORE_RFI_ID before running. This script makes a
live Procore API call.
"""

from __future__ import annotations

import os

from pyprocore.core.exceptions import ProcoreError
from pyprocore.services import get_rfi


def main() -> None:
    """Run the get-RFI example."""
    project_id_text = os.getenv("PROCORE_PROJECT_ID")
    rfi_id_text = os.getenv("PROCORE_RFI_ID")
    if not project_id_text or not rfi_id_text:
        print("Set PROCORE_PROJECT_ID and PROCORE_RFI_ID before running.")
        return

    try:
        project_id = int(project_id_text)
        rfi_id = int(rfi_id_text)
        rfi = get_rfi(project_id, rfi_id)
    except ValueError:
        print("PROCORE_PROJECT_ID and PROCORE_RFI_ID must be numbers.")
        return
    except ProcoreError as error:
        print(f"Could not fetch the RFI: {error}")
        return

    print("RFI details:")
    print(f"- ID: {rfi.id}")
    print(f"- Number: {rfi.number or 'No number'}")
    print(f"- Subject: {rfi.subject or 'No subject'}")
    print(f"- Questions: {len(rfi.questions)}")


if __name__ == "__main__":
    main()
