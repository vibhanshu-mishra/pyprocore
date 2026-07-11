"""Build an enhanced AI-ready RFI review package.

Set PROCORE_PROJECT_ID and either PROCORE_RFI_ID or PROCORE_RFI_NUMBER before
running. Optional related project context is gathered with keyword matching.
Downloads are disabled by default so beginners can inspect metadata first.
"""

from __future__ import annotations

import os
from pathlib import Path

from pyprocore.core.exceptions import ProcoreError
from pyprocore.workflows import build_enhanced_rfi_package


def main() -> None:
    """Run the enhanced RFI package example."""
    project_id = os.getenv("PROCORE_PROJECT_ID")
    company_id = os.getenv("PROCORE_COMPANY_ID")
    rfi_id = os.getenv("PROCORE_RFI_ID")
    rfi_number = os.getenv("PROCORE_RFI_NUMBER")
    output_dir = Path(os.getenv("PROCORE_OUTPUT_DIR", "rfi-package"))

    if not project_id:
        print("Set PROCORE_PROJECT_ID before running this example.")
        return
    if not rfi_id and not rfi_number:
        print("Set PROCORE_RFI_ID or PROCORE_RFI_NUMBER before running this example.")
        return

    try:
        result = build_enhanced_rfi_package(
            int(project_id),
            rfi_id=int(rfi_id) if rfi_id else None,
            rfi_number=rfi_number,
            company_id=int(company_id) if company_id else None,
            output_dir=output_dir,
            include_related=True,
            max_related_items=25,
            download_files=False,
        )
    except ValueError:
        print("Project, company, and RFI IDs must be numbers.")
        return
    except ProcoreError as exc:
        print(f"Could not build the enhanced RFI package: {exc}")
        return

    print(f"Enhanced RFI package created: {result.output_dir}")
    print(f"Manifest: {result.manifest_path}")
    print(f"AI review context: {result.review_context_path}")
    if result.manifest.sections_failed:
        print(f"Some related sections failed: {', '.join(result.manifest.sections_failed)}")


if __name__ == "__main__":
    main()
