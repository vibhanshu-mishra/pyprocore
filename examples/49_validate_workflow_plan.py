"""Validate a local PyProcore workflow plan without running it.

Set WORKFLOW_PLAN_PATH to a JSON plan file. Validation is local-only and does
not require Procore credentials.
"""

from __future__ import annotations

import os
from pathlib import Path

from pyprocore.core.exceptions import ProcoreError
from pyprocore.workflows import load_workflow_plan, validate_workflow_plan


def main() -> None:
    """Run the workflow plan validation example."""
    plan_path = Path(
        os.getenv(
            "WORKFLOW_PLAN_PATH",
            "examples/workflow_plans/project_context_and_ai_export.json",
        )
    )

    try:
        plan = validate_workflow_plan(load_workflow_plan(plan_path))
    except ProcoreError as exc:
        print(f"Workflow plan is not valid: {exc}")
        return

    enabled_steps = sum(1 for step in plan.steps if step.enabled)
    print("Workflow plan is valid.")
    print(f"Name: {plan.name}")
    print(f"Steps: {len(plan.steps)}")
    print(f"Enabled steps: {enabled_steps}")


if __name__ == "__main__":
    main()
