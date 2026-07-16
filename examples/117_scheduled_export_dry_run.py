"""Preview scheduled export output without calling Procore."""

from __future__ import annotations

import os
from pathlib import Path

from pyprocore import explain_scheduled_export_plan
from pyprocore.core.exceptions import ProcoreError


def main() -> None:
    """Print a local dry-run explanation for a scheduled export plan."""
    plan_path = Path(
        os.getenv(
            "SCHEDULED_EXPORT_PLAN",
            "examples/configs/scheduled_export_client_credentials.json",
        )
    )
    try:
        print(explain_scheduled_export_plan(plan_path))
    except ProcoreError as exc:
        print(f"Could not dry-run the plan: {exc}")


if __name__ == "__main__":
    main()
