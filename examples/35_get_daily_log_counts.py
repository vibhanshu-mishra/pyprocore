"""Get Procore Daily Log counts for a project.

Set PROCORE_PROJECT_ID before running. Optionally set PROCORE_COMPANY_ID and
PROCORE_LOG_DATE to scope the request.
"""

from __future__ import annotations

import os

from pyprocore.core.exceptions import ProcoreError
from pyprocore.services import get_daily_log_counts


def main() -> None:
    """Run the Daily Log counts example."""
    project_id = os.getenv("PROCORE_PROJECT_ID")
    company_id = os.getenv("PROCORE_COMPANY_ID")
    log_date = os.getenv("PROCORE_LOG_DATE")
    if not project_id:
        print("Set PROCORE_PROJECT_ID before running this example.")
        return

    try:
        counts = get_daily_log_counts(
            int(project_id),
            company_id=int(company_id) if company_id else None,
            log_date=log_date,
        )
    except ValueError:
        print("Project and company IDs must be numbers.")
        return
    except ProcoreError as exc:
        print(f"Could not get Daily Log counts: {exc}")
        return

    print(f"Found {len(counts)} Daily Log count item(s).")
    for count in counts:
        print(f"- {count.log_type or 'unknown'}: {count.count}")


if __name__ == "__main__":
    main()
