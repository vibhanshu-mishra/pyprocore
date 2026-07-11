"""Build a small Procore project context package for AI review.

Set PROCORE_PROJECT_ID before running. This example includes only RFIs,
submittals, and Daily Logs so beginners can create a smaller package first.
"""

from __future__ import annotations

import os
from pathlib import Path

from pyprocore.core.exceptions import ProcoreError
from pyprocore.workflows import build_project_context_package


def main() -> None:
    """Run the lightweight project context package example."""
    project_id = os.getenv("PROCORE_PROJECT_ID")
    company_id = os.getenv("PROCORE_COMPANY_ID")
    log_date = os.getenv("PROCORE_LOG_DATE")
    output_dir = Path(os.getenv("PROCORE_OUTPUT_DIR", "project-context-light"))
    if not project_id:
        print("Set PROCORE_PROJECT_ID before running this example.")
        return

    try:
        result = build_project_context_package(
            int(project_id),
            company_id=int(company_id) if company_id else None,
            output_dir=output_dir,
            include=["rfis", "submittals", "daily_logs"],
            log_date=log_date,
            max_items=25,
        )
    except ValueError:
        print("Project and company IDs must be numbers.")
        return
    except ProcoreError as exc:
        print(f"Could not build the lightweight context package: {exc}")
        return

    print(f"Lightweight project context package created: {result.output_dir}")
    print(f"Completed sections: {', '.join(result.manifest.sections_completed)}")
    if result.manifest.sections_failed:
        print(f"Failed sections: {', '.join(result.manifest.sections_failed)}")


if __name__ == "__main__":
    main()
