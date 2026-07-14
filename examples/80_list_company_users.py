"""List company directory users.

Set PROCORE_COMPANY_ID in your environment or .env file before running this
example. The script calls Procore only when you run it directly.
"""

from __future__ import annotations

import os

from pyprocore.core.exceptions import ProcoreError
from pyprocore.services import list_company_users


def main() -> None:
    """Run the example."""
    company_id = os.getenv("PROCORE_COMPANY_ID")
    if not company_id:
        print("Set PROCORE_COMPANY_ID before listing company users.")
        return

    try:
        users = list_company_users(int(company_id))
    except ProcoreError as exc:
        print(f"Could not list company users: {exc}")
        return

    print(f"Found {len(users)} company users.")
    for user in users[:10]:
        email = user.email or user.email_address or "no email"
        print(f"- {user.id}: {user.name or email}")


if __name__ == "__main__":
    main()
