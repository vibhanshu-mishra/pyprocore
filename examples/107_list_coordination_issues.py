"""List read-only project coordination issues.

Set PROCORE_PROJECT_ID and optionally PROCORE_COMPANY_ID before running.
This example makes a live Procore call only when executed directly.
"""

from __future__ import annotations

import os

from pyprocore import list_coordination_issues
from pyprocore.core.exceptions import ProcoreAPIError


def main() -> None:
    """Run the coordination issues example."""
    project_id = int(os.environ["PROCORE_PROJECT_ID"])
    company_id = int(os.environ["PROCORE_COMPANY_ID"]) if os.getenv("PROCORE_COMPANY_ID") else None
    try:
        issues = list_coordination_issues(company_id, project_id)
    except ProcoreAPIError as exc:
        print(f"Could not list coordination issues: {exc}")
        return
    print(f"Found {len(issues)} coordination issue(s).")
    for issue in issues[:10]:
        print(f"- {issue.id}: {issue.number or issue.title or issue.name}")


if __name__ == "__main__":
    main()
