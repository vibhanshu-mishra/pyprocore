# Save a Webhook Event

## What this does

Saves a local webhook payload to a file-based event store.

## When to use it

Use this when you want to archive sample webhook events for testing, debugging,
or future automation work.

## Before you start

No live Procore access is required. Use a local webhook JSON file. Do not save
real webhook secrets in committed files.

## Code

```python
from pathlib import Path

from pyprocore.webhooks import load_webhook_event, save_webhook_event

event = load_webhook_event(Path("examples/webhooks/submittal_updated_event.json"))
result = save_webhook_event(event, event_dir=Path("webhook-events-dev"))

print(result.original_path)
print(result.normalized_path)
```

CLI:

```bash
procore-sdk webhook save examples/webhooks/submittal_updated_event.json \
  --event-dir webhook-events-dev
```

## Expected output

PyProcore prints the paths for the redacted original payload and normalized
event JSON file.

## Common issues

If the event store looks empty later, confirm you are listing the same
`--event-dir`.

If a saved payload contains `[REDACTED]`, that is expected. PyProcore redacts
sensitive fields before writing local files.
