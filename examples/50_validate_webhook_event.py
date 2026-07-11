"""Validate a local webhook event JSON file.

This example does not call Procore. It loads a sample webhook payload from
examples/webhooks, normalizes the flexible payload shape, and prints a short
summary that is safe for beginners to inspect.
"""

from __future__ import annotations

from pathlib import Path

from pyprocore.core.exceptions import ProcoreError
from pyprocore.webhooks import load_webhook_event


def main() -> None:
    """Run the local webhook validation example."""
    event_path = Path(__file__).parent / "webhooks" / "rfi_created_event.json"
    try:
        event = load_webhook_event(event_path)
    except ProcoreError as error:
        print(f"Could not validate the webhook event: {error}")
        return

    print("Webhook event is valid.")
    print(f"Event ID: {event.event_id}")
    print(f"Event type: {event.event_type or 'unknown'}")
    print(f"Resource: {event.resource_type or 'unknown'} {event.resource_id or ''}".rstrip())
    if event.warnings:
        print("Warnings:")
        for warning in event.warnings:
            print(f"- {warning}")


if __name__ == "__main__":
    main()
