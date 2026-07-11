"""Save a local webhook event to the file-based event store.

This example does not call Procore. It saves a redacted original payload and a
normalized event JSON file under ./webhook-events-example.
"""

from __future__ import annotations

from pathlib import Path

from pyprocore.core.exceptions import ProcoreError
from pyprocore.webhooks import load_webhook_event, save_webhook_event


def main() -> None:
    """Run the local webhook save example."""
    event_path = Path(__file__).parent / "webhooks" / "submittal_updated_event.json"
    event_dir = Path("webhook-events-example")
    try:
        result = save_webhook_event(load_webhook_event(event_path), event_dir=event_dir)
    except ProcoreError as error:
        print(f"Could not save the webhook event: {error}")
        return

    print("Webhook event saved.")
    print(f"Original payload: {result.original_path}")
    print(f"Normalized event: {result.normalized_path}")


if __name__ == "__main__":
    main()
