"""Dry-run a workflow plan from a local webhook event.

This example does not call Procore because dispatch defaults to dry-run. It
shows how a webhook event can provide placeholders such as {event.project_id}
to an existing local workflow plan.
"""

from __future__ import annotations

from pathlib import Path

from pyprocore.core.exceptions import ProcoreError
from pyprocore.webhooks import dispatch_webhook_event, load_webhook_event


def main() -> None:
    """Run the local webhook dispatch example."""
    examples_dir = Path(__file__).parent
    event_path = examples_dir / "webhooks" / "rfi_created_event.json"
    plan_path = examples_dir / "workflow_plans" / "lightweight_sync.json"
    output_dir = Path("exports/webhook-dispatch-dry-run")

    try:
        event = load_webhook_event(event_path)
        result = dispatch_webhook_event(
            event,
            workflow_plan=plan_path,
            output_dir=output_dir,
            dry_run=True,
        )
    except ProcoreError as error:
        print(f"Could not dispatch the webhook event: {error}")
        return

    print("Webhook dispatch finished.")
    print(f"Event ID: {result.event.event_id}")
    print(f"Dry run: {result.dry_run}")
    print(f"Dispatched: {result.dispatched}")
    if result.workflow_result is not None:
        print(f"Workflow status: {result.workflow_result.status}")
        print(f"Workflow output: {result.workflow_result.output_dir}")


if __name__ == "__main__":
    main()
