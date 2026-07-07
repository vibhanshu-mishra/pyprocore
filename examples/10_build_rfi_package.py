"""Build an automation package for one RFI.

Set PROCORE_PROJECT_ID or PROCORE_PROJECT_NAME, and set PROCORE_RFI_ID or
PROCORE_RFI_NUMBER. This script makes live Procore API calls and may download
attachments unless PROCORE_NO_DOWNLOADS is set to "1".
"""

from __future__ import annotations

import os
from pathlib import Path

from pyprocore.automation import AutomationInput, build_workflow_package
from pyprocore.core.exceptions import ProcoreError


def main() -> None:
    """Run the RFI workflow package example."""
    project_id_text = os.getenv("PROCORE_PROJECT_ID")
    rfi_id_text = os.getenv("PROCORE_RFI_ID")
    output_dir = os.getenv("PROCORE_OUTPUT_DIR")

    try:
        package = build_workflow_package(
            AutomationInput(
                company_id=_optional_int("PROCORE_COMPANY_ID"),
                project_id=int(project_id_text) if project_id_text else None,
                project_name=os.getenv("PROCORE_PROJECT_NAME"),
                project_number=os.getenv("PROCORE_PROJECT_NUMBER"),
                item_type="rfi",
                item_id=int(rfi_id_text) if rfi_id_text else None,
                item_number=os.getenv("PROCORE_RFI_NUMBER"),
                download_attachments=os.getenv("PROCORE_NO_DOWNLOADS") != "1",
                output_dir=Path(output_dir) if output_dir else None,
            )
        )
    except ValueError:
        print("Numeric environment variables must contain numbers.")
        return
    except ProcoreError as error:
        print(f"Could not build the RFI package: {error}")
        return

    print("Built RFI workflow package:")
    print(f"- Project ID: {package.project_id}")
    print(f"- RFI ID: {package.item_id}")
    print(f"- Title: {package.title or 'No title'}")
    print(f"- Downloaded files: {len(package.attachments)}")


def _optional_int(name: str) -> int | None:
    """Return an optional integer from an environment variable."""
    value = os.getenv(name)
    return int(value) if value else None


if __name__ == "__main__":
    main()
