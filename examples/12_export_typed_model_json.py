"""Export one typed RFI model to JSON.

Set PROCORE_PROJECT_ID and PROCORE_RFI_ID before running. This example fetches
an RFI and writes its typed model data to JSON text on screen.
"""

from __future__ import annotations

import os

from pyprocore.core.exceptions import ProcoreError
from pyprocore.services import get_rfi


def main() -> None:
    """Run the typed-model JSON export example."""
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

    print("RFI as JSON:")
    print(rfi.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
