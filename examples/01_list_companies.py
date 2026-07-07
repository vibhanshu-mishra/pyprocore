"""List Procore companies available to the authenticated user.

Before running this example, configure your `.env` file and complete OAuth once.
This script makes a live Procore API call when you run it.
"""

from __future__ import annotations

from pyprocore.core.exceptions import ProcoreError
from pyprocore.services import list_companies


def main() -> None:
    """Run the company listing example."""
    print("Listing companies your Procore account can access...")

    try:
        companies = list_companies()
    except ProcoreError as error:
        print(f"Could not list companies: {error}")
        print("Check your .env file, OAuth token, and Procore permissions.")
        return

    if not companies:
        print("No companies were returned for this account.")
        return

    for company in companies:
        print(f"- {company.id}: {company.name or 'Unnamed company'}")


if __name__ == "__main__":
    main()
