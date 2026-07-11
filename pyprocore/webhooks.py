"""Local helpers for validating and storing Procore webhook payloads.

This module intentionally does not run a web server or register Procore
webhooks. It works with local JSON payloads so developers can safely inspect,
archive, and dry-run workflow dispatch behavior.
"""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import ConfigDict, Field

from pyprocore.core.exceptions import ValidationError
from pyprocore.models.base import ProcoreModel
from pyprocore.workflows import WorkflowRunResult, load_workflow_plan, run_workflow_plan
from pyprocore.workflows.models import WorkflowPlan

DEFAULT_EVENT_DIR = Path("webhook-events")
SENSITIVE_KEYS = {
    "authorization",
    "token",
    "access_token",
    "refresh_token",
    "client_secret",
    "secret",
    "password",
    "api_key",
    "signature",
    "webhook_secret",
}


class WebhookEvent(ProcoreModel):
    """Normalized local representation of a Procore webhook event.

    Attributes:
        event_id: Procore event ID when supplied, otherwise a local generated ID.
        event_type: Event type such as ``rfi.created`` when supplied.
        action: Event action such as ``created`` or ``updated`` when supplied.
        resource_type: Resource type such as ``rfi`` or ``submittal``.
        resource_id: Procore resource ID when supplied.
        company_id: Procore company ID when supplied.
        project_id: Procore project ID when supplied.
        user_id: User ID associated with the event when supplied.
        created_at: Event creation timestamp when supplied.
        raw_payload: Redacted original payload.
        warnings: Non-fatal normalization warnings.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True, arbitrary_types_allowed=True)

    event_id: str
    event_type: str | None = None
    action: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    company_id: str | None = None
    project_id: str | None = None
    user_id: str | None = None
    created_at: str | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)

    @property
    def id(self) -> str:
        """Return the event ID using the shorter placeholder-friendly name."""
        return self.event_id

    @property
    def type(self) -> str | None:
        """Return the event type using the shorter placeholder-friendly name."""
        return self.event_type


class WebhookEventStoreResult(ProcoreModel):
    """Result returned after saving a local webhook event.

    Attributes:
        event: Normalized webhook event that was saved.
        original_path: Path to the redacted original payload JSON file.
        normalized_path: Path to the normalized event JSON file.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True, arbitrary_types_allowed=True)

    event: WebhookEvent
    original_path: Path
    normalized_path: Path


class WebhookDispatchResult(ProcoreModel):
    """Result returned after optionally dispatching a webhook event.

    Attributes:
        event: Normalized event considered for dispatch.
        dispatched: Whether a workflow plan was dispatched.
        dry_run: Whether workflow dispatch used dry-run mode.
        workflow_plan: Workflow plan path when supplied.
        output_dir: Optional workflow output directory.
        workflow_result: Result returned by the workflow runner when dispatched.
        message: Human-readable dispatch summary.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True, arbitrary_types_allowed=True)

    event: WebhookEvent
    dispatched: bool
    dry_run: bool
    workflow_plan: Path | None = None
    output_dir: Path | None = None
    workflow_result: WorkflowRunResult | None = None
    message: str


def parse_webhook_event(payload: Mapping[str, Any] | str | bytes) -> WebhookEvent:
    """Parse and normalize a webhook event payload.

    Args:
        payload: Webhook payload mapping or JSON string/bytes.

    Returns:
        A normalized webhook event.

    Raises:
        ValidationError: If the payload is not valid JSON or a JSON object.
    """
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")
    if isinstance(payload, str):
        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"Webhook payload JSON is invalid: {exc.msg}") from exc
        if not isinstance(parsed, Mapping):
            raise ValidationError("Webhook payload must be a JSON object.")
        return normalize_webhook_event(parsed)
    return normalize_webhook_event(payload)


def load_webhook_event(path_or_stdin: Path | str) -> WebhookEvent:
    """Load a webhook event from a JSON file or stdin.

    Args:
        path_or_stdin: JSON file path, or ``-`` to read JSON from stdin.

    Returns:
        A normalized webhook event.

    Raises:
        ValidationError: If the file cannot be read or parsed.
    """
    if str(path_or_stdin) == "-":
        return parse_webhook_event(sys.stdin.read())

    path = Path(path_or_stdin)
    try:
        return parse_webhook_event(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"Webhook event file not found: {path}") from exc
    except OSError as exc:
        raise ValidationError(f"Could not read webhook event file {path}: {exc}") from exc


def normalize_webhook_event(payload: Mapping[str, Any]) -> WebhookEvent:
    """Normalize a flexible Procore webhook payload into a typed event.

    Args:
        payload: Webhook payload mapping.

    Returns:
        A normalized webhook event with warnings for missing important fields.

    Raises:
        ValidationError: If the payload is not a mapping.
    """
    if not isinstance(payload, Mapping):
        raise ValidationError("Webhook payload must be a JSON object.")

    data = _mapping_value(payload, "data")
    resource = _mapping_value(payload, "resource") or _mapping_value(data, "resource")
    metadata = _mapping_value(payload, "metadata") or _mapping_value(data, "metadata")
    redacted_payload = redact_webhook_payload(payload)

    event_id = (
        _first_text(
            payload,
            data,
            metadata,
            keys=("event_id", "eventId", "id", "uuid"),
        )
        or f"local-{uuid4().hex}"
    )
    event_type = _first_text(
        payload,
        data,
        metadata,
        keys=("event_type", "eventType", "type", "topic"),
    )
    action = _first_text(payload, data, metadata, keys=("action", "operation"))
    resource_type = _first_text(
        resource,
        keys=("resource_type", "resourceType", "entity_type", "entityType", "type"),
    ) or _first_text(
        payload,
        data,
        metadata,
        keys=("resource_type", "resourceType", "entity_type", "entityType"),
    )
    resource_id = _first_text(
        resource,
        keys=("resource_id", "resourceId", "entity_id", "entityId", "id"),
    ) or _first_text(
        payload,
        data,
        metadata,
        keys=("resource_id", "resourceId", "entity_id", "entityId"),
    )
    company_id = _first_text(
        payload,
        data,
        resource,
        metadata,
        keys=("company_id", "companyId", "company"),
    )
    project_id = _first_text(
        payload,
        data,
        resource,
        metadata,
        keys=("project_id", "projectId", "project"),
    )
    user_id = _first_text(
        payload,
        data,
        metadata,
        keys=("user_id", "userId", "actor_id", "actorId"),
    )
    created_at = _first_text(
        payload,
        data,
        metadata,
        keys=("created_at", "createdAt", "timestamp", "occurred_at", "occurredAt"),
    )

    warnings = _normalization_warnings(
        event_type=event_type,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        company_id=company_id,
        project_id=project_id,
    )

    return WebhookEvent(
        event_id=event_id,
        event_type=event_type,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        company_id=company_id,
        project_id=project_id,
        user_id=user_id,
        created_at=created_at,
        raw_payload=dict(redacted_payload),
        warnings=warnings,
    )


def redact_webhook_payload(payload: Any) -> Any:
    """Return a copy of a webhook payload with sensitive values redacted.

    Args:
        payload: Arbitrary JSON-compatible payload value.

    Returns:
        A redacted copy of the input value.
    """
    if isinstance(payload, Mapping):
        redacted: dict[str, Any] = {}
        for key, value in payload.items():
            key_text = str(key)
            if _is_sensitive_key(key_text):
                redacted[key_text] = "[REDACTED]"
            else:
                redacted[key_text] = redact_webhook_payload(value)
        return redacted
    if isinstance(payload, list):
        return [redact_webhook_payload(item) for item in payload]
    return payload


def save_webhook_event(
    event: WebhookEvent | Mapping[str, Any],
    event_dir: Path | str | None = None,
) -> WebhookEventStoreResult:
    """Save a webhook event to the local file-based event store.

    Args:
        event: Normalized event or raw payload mapping.
        event_dir: Optional root event store directory. Defaults to
            ``webhook-events`` in the current directory.

    Returns:
        Paths to the redacted original and normalized event files.
    """
    normalized = event if isinstance(event, WebhookEvent) else normalize_webhook_event(event)
    timestamp = _safe_timestamp()
    day = datetime.now(UTC).date().isoformat()
    root = Path(event_dir) if event_dir is not None else DEFAULT_EVENT_DIR
    target_dir = root / day
    target_dir.mkdir(parents=True, exist_ok=True)

    safe_event_id = _safe_slug(normalized.event_id)
    base_name = f"event-{timestamp}-{safe_event_id}"
    original_path = target_dir / f"{base_name}.json"
    normalized_path = target_dir / f"{base_name}.normalized.json"
    _write_json(original_path, normalized.raw_payload)
    _write_json(normalized_path, normalized.model_dump(mode="json"))
    return WebhookEventStoreResult(
        event=normalized,
        original_path=original_path,
        normalized_path=normalized_path,
    )


def list_webhook_events(
    event_dir: Path | str | None = None,
    filters: Mapping[str, str | int | None] | None = None,
) -> list[WebhookEvent]:
    """List normalized webhook events from the local file-based event store.

    Args:
        event_dir: Optional root event store directory. Defaults to
            ``webhook-events`` in the current directory.
        filters: Optional filters for company, project, resource, event type,
            action, and date.

    Returns:
        Saved normalized events matching the supplied filters.
    """
    root = Path(event_dir) if event_dir is not None else DEFAULT_EVENT_DIR
    if not root.exists():
        return []

    normalized_paths = sorted(root.glob("**/*.normalized.json"))
    active_filters = {key: str(value) for key, value in (filters or {}).items() if value}
    events: list[WebhookEvent] = []
    for path in normalized_paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, Mapping):
            continue
        event = WebhookEvent.model_validate(payload)
        if _matches_filters(event, path, active_filters):
            events.append(event)
    return events


def dispatch_webhook_event(
    event: WebhookEvent | Mapping[str, Any],
    workflow_plan: Path | str | WorkflowPlan | Mapping[str, Any] | None = None,
    output_dir: Path | str | None = None,
    dry_run: bool = True,
) -> WebhookDispatchResult:
    """Optionally dispatch a webhook event to a local workflow plan.

    Args:
        event: Normalized event or raw payload mapping.
        workflow_plan: Optional workflow plan path or in-memory plan.
        output_dir: Optional workflow output directory.
        dry_run: Whether to dry-run workflow execution. Defaults to ``True``.

    Returns:
        A dispatch result. If no workflow plan is supplied, no workflow runs.
    """
    normalized = event if isinstance(event, WebhookEvent) else normalize_webhook_event(event)
    resolved_output_dir = Path(output_dir) if output_dir is not None else None

    if workflow_plan is None:
        return WebhookDispatchResult(
            event=normalized,
            dispatched=False,
            dry_run=dry_run,
            output_dir=resolved_output_dir,
            message="No workflow plan supplied; no workflow was dispatched.",
        )

    plan_with_event = _plan_with_event_context(workflow_plan, normalized)
    workflow_result = run_workflow_plan(
        plan_with_event,
        output_dir=resolved_output_dir,
        dry_run=dry_run,
    )
    workflow_plan_path = workflow_plan if isinstance(workflow_plan, (str, Path)) else None
    return WebhookDispatchResult(
        event=normalized,
        dispatched=True,
        dry_run=dry_run,
        workflow_plan=Path(workflow_plan_path) if workflow_plan_path is not None else None,
        output_dir=resolved_output_dir,
        workflow_result=workflow_result,
        message="Workflow plan dispatched.",
    )


def _plan_with_event_context(
    workflow_plan: Path | str | WorkflowPlan | Mapping[str, Any],
    event: WebhookEvent,
) -> WorkflowPlan:
    """Return a workflow plan with webhook event placeholders available."""
    plan = (
        load_workflow_plan(workflow_plan)
        if isinstance(workflow_plan, (str, Path))
        else (
            WorkflowPlan.model_validate(workflow_plan)
            if isinstance(workflow_plan, Mapping)
            else workflow_plan
        )
    )
    event_context = {
        "id": event.event_id,
        "type": event.event_type,
        "action": event.action,
        "company_id": event.company_id,
        "project_id": event.project_id,
        "resource_type": event.resource_type,
        "resource_id": event.resource_id,
    }
    defaults = {**plan.defaults, "event": event_context}
    return plan.model_copy(update={"defaults": defaults}, deep=True)


def _matches_filters(
    event: WebhookEvent,
    path: Path,
    filters: Mapping[str, str],
) -> bool:
    filter_fields = {
        "company_id": event.company_id,
        "project_id": event.project_id,
        "resource_type": event.resource_type,
        "resource_id": event.resource_id,
        "event_type": event.event_type,
        "action": event.action,
    }
    for key, expected in filters.items():
        if key == "date":
            if expected not in path.parts:
                return False
            continue
        if str(filter_fields.get(key) or "") != expected:
            return False
    return True


def _normalization_warnings(
    *,
    event_type: str | None,
    action: str | None,
    resource_type: str | None,
    resource_id: str | None,
    company_id: str | None,
    project_id: str | None,
) -> list[str]:
    """Build non-fatal warnings for missing event fields."""
    checks = {
        "event_type": event_type,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "company_id": company_id,
        "project_id": project_id,
    }
    return [f"Missing {name}." for name, value in checks.items() if value is None]


def _first_text(*mappings: Mapping[str, Any] | None, keys: tuple[str, ...]) -> str | None:
    """Return the first non-empty scalar value found for any key."""
    for mapping in mappings:
        if not isinstance(mapping, Mapping):
            continue
        for key in keys:
            value = mapping.get(key)
            if value is None or isinstance(value, (Mapping, list)):
                continue
            text = str(value).strip()
            if text:
                return text
    return None


def _mapping_value(mapping: Mapping[str, Any] | None, key: str) -> Mapping[str, Any] | None:
    """Return a nested mapping value when present."""
    if not isinstance(mapping, Mapping):
        return None
    value = mapping.get(key)
    return value if isinstance(value, Mapping) else None


def _is_sensitive_key(key: str) -> bool:
    """Return whether a JSON key should be redacted."""
    normalized = key.casefold()
    return normalized in SENSITIVE_KEYS or any(part in normalized for part in SENSITIVE_KEYS)


def _safe_slug(value: str) -> str:
    """Return a filesystem-safe slug for an event ID."""
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip(".-")
    return slug or f"local-{uuid4().hex}"


def _safe_timestamp() -> str:
    """Return a compact UTC timestamp suitable for filenames."""
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _write_json(path: Path, payload: Any) -> None:
    """Write a JSON file with stable formatting."""
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", "utf-8")
