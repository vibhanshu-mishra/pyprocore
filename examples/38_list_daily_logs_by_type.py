"""List Procore Daily Logs by type.

Set PROCORE_PROJECT_ID before running. Set PROCORE_DAILY_LOG_TYPE to one of the
supported types, such as manpower, notes, delay, delivery, or plan_revision.
"""

from __future__ import annotations

import os

from pyprocore.core.exceptions import ProcoreError
from pyprocore.services import DAILY_LOG_TYPES, list_daily_logs


def main() -> None:
    """Run the Daily Logs by type example."""
    project_id = os.getenv("PROCORE_PROJECT_ID")
    company_id = os.getenv("PROCORE_COMPANY_ID")
    log_date = os.getenv("PROCORE_LOG_DATE")
    log_type = os.getenv("PROCORE_DAILY_LOG_TYPE", "manpower")
    if not project_id:
        print("Set PROCORE_PROJECT_ID before running this example.")
        return

    try:
        logs = list_daily_logs(
            int(project_id),
            log_type,
            company_id=int(company_id) if company_id else None,
            log_date=log_date,
        )
    except ValueError:
        print("Project and company IDs must be numbers.")
        return
    except ProcoreError as exc:
        print(f"Could not list {log_type} logs: {exc}")
        print(f"Supported log types: {', '.join(DAILY_LOG_TYPES)}")
        return

    print(f"Found {len(logs)} {log_type} log(s).")
    for log in logs:
        print(f"- {log.id}: {log.log_date or log.date or 'No date'}")


if __name__ == "__main__":
    main()
