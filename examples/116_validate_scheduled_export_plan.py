"""Validate a scheduled export plan JSON file without Procore access."""

from __future__ import annotations

import os
from pathlib import Path

from pyprocore import load_scheduled_export_plan, validate_scheduled_export_plan
from pyprocore.core.exceptions import ProcoreError


def main() -> None:
    """Validate a local scheduled export plan and print beginner-friendly results."""
    plan_path = Path(
        os.getenv(
            "SCHEDULED_EXPORT_PLAN",
            "examples/configs/scheduled_export_client_credentials.json",
        )
    )
    try:
        report = validate_scheduled_export_plan(load_scheduled_export_plan(plan_path))
    except ProcoreError as exc:
        print(f"Could not validate the plan: {exc}")
        return

    print(f"Plan: {report.plan_name}")
    print(f"Valid: {report.is_valid}")
    for finding in report.findings:
        print(f"- {finding.severity.upper()}: {finding.message}")


if __name__ == "__main__":
    main()
