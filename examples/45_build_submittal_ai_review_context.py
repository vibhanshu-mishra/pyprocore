"""Build focused submittal AI review files.

Set PROCORE_PROJECT_ID and either PROCORE_SUBMITTAL_ID or
PROCORE_SUBMITTAL_NUMBER before running. This example limits related context to
RFIs, drawings, and specifications so the generated AI folder stays focused.
"""

from __future__ import annotations

import os
from pathlib import Path

from pyprocore.core.exceptions import ProcoreError
from pyprocore.workflows import build_enhanced_submittal_package


def main() -> None:
    """Run the focused submittal AI review-context example."""
    project_id = os.getenv("PROCORE_PROJECT_ID")
    company_id = os.getenv("PROCORE_COMPANY_ID")
    submittal_id = os.getenv("PROCORE_SUBMITTAL_ID")
    submittal_number = os.getenv("PROCORE_SUBMITTAL_NUMBER")
    search_term = os.getenv("PROCORE_SEARCH_TERM")
    output_dir = Path(os.getenv("PROCORE_OUTPUT_DIR", "submittal-ai-review"))

    if not project_id:
        print("Set PROCORE_PROJECT_ID before running this example.")
        return
    if not submittal_id and not submittal_number:
        print("Set PROCORE_SUBMITTAL_ID or PROCORE_SUBMITTAL_NUMBER before running this example.")
        return

    try:
        result = build_enhanced_submittal_package(
            int(project_id),
            submittal_id=int(submittal_id) if submittal_id else None,
            submittal_number=submittal_number,
            company_id=int(company_id) if company_id else None,
            output_dir=output_dir,
            related_sections=["rfis", "drawings", "specifications"],
            search_terms=[search_term] if search_term else None,
            max_related_items=10,
            download_files=False,
        )
    except ValueError:
        print("Project, company, and submittal IDs must be numbers.")
        return
    except ProcoreError as exc:
        print(f"Could not build the submittal AI review context: {exc}")
        return

    print(f"AI review files created in: {result.output_dir / 'ai'}")
    print(f"Start with: {result.review_context_path}")
    print(f"Approval review notes: {result.approval_review_path}")
    print("Use the generated files for review assistance, not final approval decisions.")


if __name__ == "__main__":
    main()
