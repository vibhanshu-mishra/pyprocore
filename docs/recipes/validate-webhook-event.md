# Validate a Webhook Event

## What this does

Validates a local webhook JSON payload and prints a normalized summary.

## When to use it

Use this when you receive a sample Procore webhook payload and want to inspect
it before building a real webhook receiver.

## Before you start

No Procore credentials are required for local validation. You only need a JSON
payload file, such as `examples/webhooks/rfi_created_event.json`.

## Code

```python
from pathlib import Path

from pyprocore.webhooks import load_webhook_event

event = load_webhook_event(Path("examples/webhooks/rfi_created_event.json"))

print(event.event_id)
print(event.event_type)
print(event.resource_type)
print(event.project_id)
```

CLI:

```bash
procore-sdk webhook validate examples/webhooks/rfi_created_event.json
```

## Expected output

You should see the event ID, event type, action, resource, company, and project
when those fields are present.

## Common issues

If the payload is not valid JSON, PyProcore prints a friendly validation error.

If fields are missing, PyProcore shows warnings instead of crashing because
webhook payload shapes can vary.
