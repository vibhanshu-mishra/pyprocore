"""Build only the most useful RFI context files for AI-assisted review.

Set PROCORE_PROJECT_ID and either PROCORE_RFI_ID or PROCORE_RFI_NUMBER before
running. This example limits related context to drawings, specifications, and
submittals so the generated AI folder stays focused.
"""

from __future__ import annotations

import os
from pathlib import Path

from pyprocore.core.exceptions import ProcoreError
from pyprocore.workflows import build_enhanced_rfi_package


def main() -> None:
    """Run the focused RFI AI review-context example."""
    project_id = os.getenv("PROCORE_PROJECT_ID")
    company_id = os.getenv("PROCORE_COMPANY_ID")
    rfi_id = os.getenv("PROCORE_RFI_ID")
    rfi_number = os.getenv("PROCORE_RFI_NUMBER")
    search_term = os.getenv("PROCORE_SEARCH_TERM")
    output_dir = Path(os.getenv("PROCORE_OUTPUT_DIR", "rfi-ai-review"))

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
            related_sections=["drawings", "specifications", "submittals"],
            search_terms=[search_term] if search_term else None,
            max_related_items=10,
            download_files=False,
        )
    except ValueError:
        print("Project, company, and RFI IDs must be numbers.")
        return
    except ProcoreError as exc:
        print(f"Could not build the RFI AI review context: {exc}")
        return

    print(f"AI review files created in: {result.output_dir / 'ai'}")
    print(f"Start with: {result.review_context_path}")
    print("Use the generated files for review assistance, not final judgment.")


if __name__ == "__main__":
    main()
