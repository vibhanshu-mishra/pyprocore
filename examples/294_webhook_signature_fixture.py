"""Build and verify a local webhook signature fixture.

This example uses a fake payload and local test secret. It does not start a
webhook server, call Procore, or claim provider-specific signature behavior.
"""

from pyprocore.integrations import (
    compute_webhook_signature,
    normalize_webhook_event,
    verify_webhook_signature,
)


def main() -> None:
    """Create and verify a local webhook fixture."""
    secret = "local-test-secret"
    payload = {"event_type": "project.updated", "project_id": 123}
    signature = compute_webhook_signature(payload, secret)
    event = normalize_webhook_event(
        {"X-Test-Signature": signature},
        payload,
        signature_header="X-Test-Signature",
        secret=secret,
        event_id="evt_example",
    )

    print(f"Fixture event ID: {event.event_id}")
    print(f"Signature valid: {verify_webhook_signature(payload, signature, secret)}")
    print("Use your provider's actual signature format in production.")


if __name__ == "__main__":
    main()
