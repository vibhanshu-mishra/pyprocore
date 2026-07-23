"""Local webhook fixture helpers for integration blueprints."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from pathlib import Path
from typing import Any

from pyprocore.integrations.models import IntegrationWebhookEvent
from pyprocore.integrations.sync_runs import redact_sensitive_data


def canonical_webhook_body(body: dict[str, Any] | str | bytes) -> bytes:
    """Return deterministic bytes for local webhook fixture signing."""
    if isinstance(body, bytes):
        return body
    if isinstance(body, str):
        return body.encode("utf-8")
    return json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")


def compute_webhook_signature(
    body: dict[str, Any] | str | bytes,
    secret: str,
) -> str:
    """Compute an HMAC SHA-256 signature for local webhook test fixtures.

    Args:
        body: Local fixture payload.
        secret: Local test secret. The value is never printed.

    Returns:
        Hex-encoded HMAC SHA-256 signature.
    """
    return hmac.new(
        secret.encode("utf-8"),
        canonical_webhook_body(body),
        hashlib.sha256,
    ).hexdigest()


def verify_webhook_signature(
    body: dict[str, Any] | str | bytes,
    signature: str,
    secret: str,
) -> bool:
    """Verify a local webhook fixture HMAC SHA-256 signature."""
    expected = compute_webhook_signature(body, secret)
    return hmac.compare_digest(expected, signature)


def normalize_webhook_event(
    headers: dict[str, str],
    body: dict[str, Any] | str | bytes,
    *,
    signature_header: str | None = None,
    secret: str | None = None,
    event_id: str | None = None,
) -> IntegrationWebhookEvent:
    """Build a sanitized local webhook event record.

    Args:
        headers: Request headers from a local fixture or user-owned receiver.
        body: Request body from a local fixture or user-owned receiver.
        signature_header: Header key that carries the signature.
        secret: Optional local secret used to verify the fixture signature.
        event_id: Optional caller-provided event identifier.

    Returns:
        Sanitized local webhook event record.
    """
    body_bytes = canonical_webhook_body(body)
    parsed_body = _parse_body(body)
    sanitized_headers = {
        key: str(redact_sensitive_data(value)) for key, value in sorted(headers.items())
    }
    signature = headers.get(signature_header or "") if signature_header else None
    signature_valid = (
        verify_webhook_signature(body_bytes, signature, secret)
        if signature and secret is not None
        else None
    )
    return IntegrationWebhookEvent(
        event_id=event_id or f"evt_{secrets.token_hex(8)}",
        headers=sanitized_headers,
        body=redact_sensitive_data(parsed_body),
        body_sha256=hashlib.sha256(body_bytes).hexdigest(),
        signature_header=signature_header,
        signature_valid=signature_valid,
    )


def write_webhook_event(
    event: IntegrationWebhookEvent,
    path: Path | str,
    *,
    append_jsonl: bool | None = None,
) -> Path:
    """Write a sanitized local webhook event to JSON or JSONL."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    use_jsonl = append_jsonl if append_jsonl is not None else output_path.suffix == ".jsonl"
    payload = json.dumps(event.model_dump(mode="json"), sort_keys=True)
    if use_jsonl:
        with output_path.open("a", encoding="utf-8") as handle:
            handle.write(payload + "\n")
    else:
        output_path.write_text(payload + "\n", encoding="utf-8")
    return output_path


def build_sample_webhook_event(output_path: Path | str | None = None) -> IntegrationWebhookEvent:
    """Build a local fake webhook fixture event without network calls."""
    secret = "local-test-secret"
    body = {
        "event_type": "project.updated",
        "resource": "project",
        "resource_id": 123,
        "company_id": 456,
    }
    signature = compute_webhook_signature(body, secret)
    event = normalize_webhook_event(
        {"X-PyProcore-Signature": signature},
        body,
        signature_header="X-PyProcore-Signature",
        secret=secret,
        event_id="evt_local_fixture",
    )
    if output_path is not None:
        write_webhook_event(event, output_path)
    return event


def _parse_body(body: dict[str, Any] | str | bytes) -> dict[str, Any]:
    if isinstance(body, dict):
        return body
    raw = body.decode("utf-8") if isinstance(body, bytes) else body
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {"raw_body": raw}
    if isinstance(parsed, dict):
        return parsed
    return {"body": parsed}
