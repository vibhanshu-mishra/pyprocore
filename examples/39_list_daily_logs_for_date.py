"""List several Procore Daily Log types for one date.

Set PROCORE_PROJECT_ID before running. Optionally set PROCORE_LOG_DATE and
PROCORE_DAILY_LOG_TYPES as a comma-separated list, such as manpower,notes,delay.
"""

from __future__ import annotations

import os

from pyprocore.core.exceptions import ProcoreError
from pyprocore.services import list_daily_logs_for_date


def main() -> None:
    """Run the Daily Logs for date example."""
    project_id = os.getenv("PROCORE_PROJECT_ID")
    company_id = os.getenv("PROCORE_COMPANY_ID")
    log_date = os.getenv("PROCORE_LOG_DATE")
    raw_types = os.getenv("PROCORE_DAILY_LOG_TYPES")
    log_types = (
        [item.strip() for item in raw_types.split(",") if item.strip()] if raw_types else None
    )
    if not project_id:
        print("Set PROCORE_PROJECT_ID before running this example.")
        return

    try:
        summary = list_daily_logs_for_date(
            int(project_id),
            company_id=int(company_id) if company_id else None,
            log_date=log_date,
            log_types=log_types,
        )
    except ValueError:
        print("Project and company IDs must be numbers.")
        return
    except ProcoreError as exc:
        print(f"Could not list Daily Logs for the date: {exc}")
        return

    print(f"Daily Logs for project {summary.project_id} on {summary.log_date or 'default date'}:")
    for log_type, logs in summary.logs.items():
        print(f"- {log_type}: {len(logs)} item(s)")
    if summary.errors:
        print("Some log types could not be read:")
        for log_type, message in summary.errors.items():
            print(f"- {log_type}: {message}")


if __name__ == "__main__":
    main()
