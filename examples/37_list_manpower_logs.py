"""List Procore manpower logs for a project.

Set PROCORE_PROJECT_ID before running. Optionally set PROCORE_COMPANY_ID and
PROCORE_LOG_DATE. If no date is supplied, Procore may return current or default
Daily Log data based on its API behavior.
"""

from __future__ import annotations

import os

from pyprocore.core.exceptions import ProcoreError
from pyprocore.services import list_manpower_logs


def main() -> None:
    """Run the manpower log listing example."""
    project_id = os.getenv("PROCORE_PROJECT_ID")
    company_id = os.getenv("PROCORE_COMPANY_ID")
    log_date = os.getenv("PROCORE_LOG_DATE")
    if not project_id:
        print("Set PROCORE_PROJECT_ID before running this example.")
        return

    try:
        logs = list_manpower_logs(
            int(project_id),
            company_id=int(company_id) if company_id else None,
            log_date=log_date,
        )
    except ValueError:
        print("Project and company IDs must be numbers.")
        return
    except ProcoreError as exc:
        print(f"Could not list manpower logs: {exc}")
        return

    print(f"Found {len(logs)} manpower log(s).")
    for log in logs:
        label = log.description or log.notes or log.comments or "No description"
        print(f"- {log.id}: {label}")


if __name__ == "__main__":
    main()
