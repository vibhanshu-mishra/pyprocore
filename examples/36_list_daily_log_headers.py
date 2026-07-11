"""List Procore Daily Log headers for a project.

Set PROCORE_PROJECT_ID before running. Optionally set PROCORE_COMPANY_ID and
PROCORE_LOG_DATE to view headers for a single day.
"""

from __future__ import annotations

import os

from pyprocore.core.exceptions import ProcoreError
from pyprocore.services import list_daily_log_headers


def main() -> None:
    """Run the Daily Log header listing example."""
    project_id = os.getenv("PROCORE_PROJECT_ID")
    company_id = os.getenv("PROCORE_COMPANY_ID")
    log_date = os.getenv("PROCORE_LOG_DATE")
    if not project_id:
        print("Set PROCORE_PROJECT_ID before running this example.")
        return

    try:
        headers = list_daily_log_headers(
            int(project_id),
            company_id=int(company_id) if company_id else None,
            log_date=log_date,
        )
    except ValueError:
        print("Project and company IDs must be numbers.")
        return
    except ProcoreError as exc:
        print(f"Could not list Daily Log headers: {exc}")
        return

    print(f"Found {len(headers)} Daily Log header(s).")
    for header in headers:
        print(f"- {header.id}: {header.log_date or header.date or 'No date'}")


if __name__ == "__main__":
    main()
