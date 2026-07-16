"""Build a scheduled export plan in Python without calling Procore.

This example creates a local ``ScheduledExportPlan`` object with placeholder
IDs. It is safe to run without credentials because it does not fetch data.
"""

from __future__ import annotations

from pathlib import Path

from pyprocore import ScheduledExportPlan


def main() -> None:
    """Create and print a safe scheduled export plan."""
    plan = ScheduledExportPlan(
        plan_name="example-enterprise-nightly-export",
        auth_mode="client_credentials",
        company_id=12345,
        project_ids=[67890],
        resources=["rfis", "submittals", "documents"],
        output_dir=Path("./exports/scheduled/example"),
        output_format="csv",
        dry_run=True,
        redaction_enabled=True,
        max_projects=5,
        notes="Replace placeholder IDs only after reviewing permissions.",
    )
    print("Created a local scheduled export plan.")
    print(plan.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
