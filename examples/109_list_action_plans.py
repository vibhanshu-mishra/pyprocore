"""List read-only project action plans.

Set PROCORE_PROJECT_ID and optionally PROCORE_COMPANY_ID before running.
This example makes a live Procore call only when executed directly.
"""

from __future__ import annotations

import os

from pyprocore import list_action_plans
from pyprocore.core.exceptions import ProcoreAPIError


def main() -> None:
    """Run the action plans example."""
    project_id = int(os.environ["PROCORE_PROJECT_ID"])
    company_id = int(os.environ["PROCORE_COMPANY_ID"]) if os.getenv("PROCORE_COMPANY_ID") else None
    try:
        plans = list_action_plans(company_id, project_id)
    except ProcoreAPIError as exc:
        print(f"Could not list action plans: {exc}")
        return
    print(f"Found {len(plans)} action plan(s).")
    for plan in plans[:10]:
        print(f"- {plan.id}: {plan.number or plan.name or plan.title}")


if __name__ == "__main__":
    main()
