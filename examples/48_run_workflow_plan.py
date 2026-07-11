"""Run or dry-run a local PyProcore workflow plan.

Set WORKFLOW_PLAN_PATH to a JSON plan file. This example defaults to dry-run so
beginners can inspect what would happen before any workflow calls Procore.
"""

from __future__ import annotations

import os
from pathlib import Path

from pyprocore.core.exceptions import ProcoreError
from pyprocore.workflows import run_workflow_plan


def main() -> None:
    """Run the workflow plan example."""
    plan_path = os.getenv(
        "WORKFLOW_PLAN_PATH",
        "examples/workflow_plans/project_context_and_ai_export.json",
    )
    output_dir = os.getenv("WORKFLOW_RUN_OUTPUT_DIR")
    dry_run = os.getenv("WORKFLOW_DRY_RUN", "1") != "0"

    try:
        result = run_workflow_plan(
            Path(plan_path),
            output_dir=Path(output_dir) if output_dir else None,
            dry_run=dry_run,
        )
    except ProcoreError as exc:
        print(f"Could not run the workflow plan: {exc}")
        return

    print(f"Workflow plan: {result.plan.name}")
    print(f"Status: {result.status}")
    print(f"Dry run: {result.dry_run}")
    print(f"Run folder: {result.output_dir}")
    print(f"Summary: {result.summary_path}")


if __name__ == "__main__":
    main()
