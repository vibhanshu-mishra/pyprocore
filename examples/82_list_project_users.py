"""List project directory users.

Set PROCORE_COMPANY_ID and PROCORE_PROJECT_ID in your environment or .env file.
"""

from __future__ import annotations

import os

from pyprocore.core.exceptions import ProcoreError
from pyprocore.services import list_project_users


def main() -> None:
    """Run the example."""
    company_id = os.getenv("PROCORE_COMPANY_ID")
    project_id = os.getenv("PROCORE_PROJECT_ID")
    if not company_id or not project_id:
        print("Set PROCORE_COMPANY_ID and PROCORE_PROJECT_ID before listing project users.")
        return

    try:
        users = list_project_users(int(company_id), int(project_id))
    except ProcoreError as exc:
        print(f"Could not list project users: {exc}")
        return

    print(f"Found {len(users)} project users.")
    for user in users[:10]:
        email = user.email or user.email_address or "no email"
        print(f"- {user.id}: {user.name or email}")


if __name__ == "__main__":
    main()
