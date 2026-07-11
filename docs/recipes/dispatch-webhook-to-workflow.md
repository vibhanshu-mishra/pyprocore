# Dispatch a Webhook Event to a Workflow Plan

## What this does

Uses a local webhook event to dry-run an existing PyProcore workflow plan.

## When to use it

Use this when you want to test how future webhook-triggered automation might
work without running a hosted webhook server.

## Before you start

You need a local webhook JSON file and a JSON workflow plan. Dispatch defaults
to dry-run. Live workflow execution still requires a configured `.env`, OAuth
token store, and valid Procore access.

## Code

```python
from pathlib import Path

from pyprocore.webhooks import dispatch_webhook_event, load_webhook_event

event = load_webhook_event(Path("examples/webhooks/rfi_created_event.json"))
result = dispatch_webhook_event(
    event,
    workflow_plan=Path("examples/workflow_plans/lightweight_sync.json"),
    output_dir=Path("exports/webhook-dispatch-dry-run"),
    dry_run=True,
)

print(result.dispatched)
print(result.workflow_result.status if result.workflow_result else "no workflow")
```

CLI:

```bash
procore-sdk webhook dispatch examples/webhooks/rfi_created_event.json \
  --workflow-plan examples/workflow_plans/lightweight_sync.json \
  --dry-run
```

## Expected output

PyProcore prints a dispatch summary and writes local dry-run workflow manifest
files.

## Common issues

If you omit `--workflow-plan`, no workflow is dispatched.

If you use `--no-dry-run`, the workflow can make live Procore read calls. Only
use that after validating credentials, project IDs, and workflow options.

This is not a hosted webhook receiver. Use a real web framework or hosting
service for production webhook receiving.
