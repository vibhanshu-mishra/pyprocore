"""List read-only project forms.

Set PROCORE_PROJECT_ID and optionally PROCORE_COMPANY_ID before running.
This example makes a live Procore call only when executed directly.
"""

from __future__ import annotations

import os

from pyprocore import list_forms
from pyprocore.core.exceptions import ProcoreAPIError


def main() -> None:
    """Run the forms example."""
    project_id = int(os.environ["PROCORE_PROJECT_ID"])
    company_id = int(os.environ["PROCORE_COMPANY_ID"]) if os.getenv("PROCORE_COMPANY_ID") else None
    try:
        forms = list_forms(company_id, project_id)
    except ProcoreAPIError as exc:
        print(f"Could not list forms: {exc}")
        return
    print(f"Found {len(forms)} form(s).")
    for form in forms[:10]:
        print(f"- {form.id}: {form.name or form.title}")


if __name__ == "__main__":
    main()
