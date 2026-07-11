"""Build an enhanced AI-ready submittal review package.

Set PROCORE_PROJECT_ID and either PROCORE_SUBMITTAL_ID or
PROCORE_SUBMITTAL_NUMBER before running. Optional related project context is
gathered with keyword matching. Downloads are disabled by default.
"""

from __future__ import annotations

import os
from pathlib import Path

from pyprocore.core.exceptions import ProcoreError
from pyprocore.workflows import build_enhanced_submittal_package


def main() -> None:
    """Run the enhanced submittal package example."""
    project_id = os.getenv("PROCORE_PROJECT_ID")
    company_id = os.getenv("PROCORE_COMPANY_ID")
    submittal_id = os.getenv("PROCORE_SUBMITTAL_ID")
    submittal_number = os.getenv("PROCORE_SUBMITTAL_NUMBER")
    output_dir = Path(os.getenv("PROCORE_OUTPUT_DIR", "enhanced-submittal-package"))

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
            include_related=True,
            max_related_items=25,
            download_files=False,
        )
    except ValueError:
        print("Project, company, and submittal IDs must be numbers.")
        return
    except ProcoreError as exc:
        print(f"Could not build the enhanced submittal package: {exc}")
        return

    print(f"Enhanced submittal package created: {result.output_dir}")
    print(f"Manifest: {result.manifest_path}")
    print(f"AI review context: {result.review_context_path}")
    print(f"Approval review: {result.approval_review_path}")
    if result.manifest.sections_failed:
        print(f"Some related sections failed: {', '.join(result.manifest.sections_failed)}")


if __name__ == "__main__":
    main()
