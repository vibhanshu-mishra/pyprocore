"""List read-only project tasks.

Set PROCORE_PROJECT_ID and optionally PROCORE_COMPANY_ID before running.
This example makes a live Procore call only when executed directly.
"""

from __future__ import annotations

import os

from pyprocore import list_tasks
from pyprocore.core.exceptions import ProcoreAPIError


def main() -> None:
    """Run the tasks list example."""
    project_id = int(os.environ["PROCORE_PROJECT_ID"])
    company_id = int(os.environ["PROCORE_COMPANY_ID"]) if os.getenv("PROCORE_COMPANY_ID") else None
    try:
        tasks = list_tasks(company_id, project_id)
    except ProcoreAPIError as exc:
        print(f"Could not list tasks: {exc}")
        return
    print(f"Found {len(tasks)} task(s).")
    for task in tasks[:10]:
        print(f"- {task.id}: {task.number or task.name or task.title}")


if __name__ == "__main__":
    main()
