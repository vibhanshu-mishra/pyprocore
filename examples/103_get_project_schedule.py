"""Get read-only project schedule metadata.

Set PROCORE_PROJECT_ID and optionally PROCORE_COMPANY_ID before running.
This example makes a live Procore call only when executed directly.
"""

from __future__ import annotations

import os

from pyprocore import get_project_schedule
from pyprocore.core.exceptions import ProcoreAPIError


def main() -> None:
    """Run the project schedule example."""
    project_id = int(os.environ["PROCORE_PROJECT_ID"])
    company_id = int(os.environ["PROCORE_COMPANY_ID"]) if os.getenv("PROCORE_COMPANY_ID") else None
    try:
        schedule = get_project_schedule(company_id, project_id)
    except ProcoreAPIError as exc:
        print(f"Could not get project schedule: {exc}")
        return
    print("Project schedule loaded.")
    print(f"- id: {schedule.id}")
    print(f"- name: {schedule.name or schedule.title}")


if __name__ == "__main__":
    main()
