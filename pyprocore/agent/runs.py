"""Local, privacy-safe run logs and replay for the PyProcore Agent API."""

from __future__ import annotations

import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import Field

from pyprocore.agent.registry import AgentToolNotFoundError, get_agent_registry, get_agent_tool
from pyprocore.models.base import ProcoreModel

DEFAULT_AGENT_RUN_LOG_DIR = Path("agent-runs")
SENSITIVE_KEY_PATTERN = re.compile(
    r"(authorization|access[_-]?token|refresh[_-]?token|"
    r"client[_-]?secret|secret|password|api[_-]?key)",
    re.IGNORECASE,
)
SIGNED_URL_PATTERN = re.compile(
    r"([?&](?:X-Amz|Signature|Expires|token|key|signature)=)[^&\s]+", re.I
)
SAFE_RUN_ID_PATTERN = re.compile(r"[^a-zA-Z0-9_.-]+")
RECOGNIZED_ROUTES = {
    "/",
    "/health",
    "/agent/manifest",
    "/agent/tools",
    "/agent/openapi.json",
    "/agent/schemas",
}


class AgentRunEvent(ProcoreModel):
    """One sanitized local Agent API request/response event."""

    event_id: str
    run_id: str
    timestamp: datetime
    method: str
    path: str
    status_code: int
    event_type: str
    redacted: bool = True
    tool_name: str | None = None
    request_summary: dict[str, Any] = Field(default_factory=dict)
    response_summary: dict[str, Any] = Field(default_factory=dict)
    error_type: str | None = None
    duration_ms: float | None = None


class AgentRun(ProcoreModel):
    """Local Agent API run log metadata and events."""

    run_id: str
    created_at: datetime
    source: str
    pyprocore_version: str
    registry_version: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    events: list[AgentRunEvent] = Field(default_factory=list)


class AgentRunLogStore(ProcoreModel):
    """Local filesystem store for Agent API run logs."""

    root_dir: Path = DEFAULT_AGENT_RUN_LOG_DIR


class AgentReplayEventResult(ProcoreModel):
    """Replay validation result for one logged Agent API event."""

    event_id: str
    path: str
    passed: bool
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class AgentReplayResult(ProcoreModel):
    """Replay validation result for an Agent API run."""

    run_id: str
    passed: bool
    event_count: int
    checked_at: datetime
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    events: list[AgentReplayEventResult] = Field(default_factory=list)


def create_agent_run(
    run_log_dir: Path | str,
    *,
    run_id: str | None = None,
    source: str = "agent-api",
    metadata: dict[str, Any] | None = None,
) -> AgentRun:
    """Create a local Agent API run log directory.

    Args:
        run_log_dir: Directory where run logs are stored.
        run_id: Optional caller-provided run identifier.
        source: Human-readable source of the run.
        metadata: Optional non-secret metadata to store with the run.

    Returns:
        Created run metadata.
    """
    from pyprocore import __version__

    registry = get_agent_registry()
    safe_run_id = sanitize_run_id(
        run_id or f"run-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{uuid4().hex[:8]}"
    )
    run = AgentRun(
        run_id=safe_run_id,
        created_at=datetime.now(timezone.utc),
        source=source,
        pyprocore_version=__version__,
        registry_version=registry.registry_version,
        metadata=redact_agent_event_payload(metadata or {}),
        events=[],
    )
    run_dir = _run_dir(run_log_dir, safe_run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    _run_json_path(run_log_dir, safe_run_id).write_text(
        run.model_dump_json(indent=2),
        encoding="utf-8",
    )
    _events_jsonl_path(run_log_dir, safe_run_id).touch(exist_ok=True)
    return run


def append_agent_run_event(
    run_log_dir: Path | str,
    run_id: str,
    *,
    method: str,
    path: str,
    status_code: int,
    event_type: str,
    tool_name: str | None = None,
    request_summary: dict[str, Any] | None = None,
    response_summary: dict[str, Any] | None = None,
    error_type: str | None = None,
    duration_ms: float | None = None,
) -> AgentRunEvent:
    """Append one sanitized event to a local Agent API run log.

    Args:
        run_log_dir: Directory containing run logs.
        run_id: Existing run identifier.
        method: HTTP method.
        path: Request path without query parameters.
        status_code: Response status code.
        event_type: Short event type label.
        tool_name: Optional registered tool name.
        request_summary: Sanitized request summary.
        response_summary: Sanitized response summary.
        error_type: Optional response error type.
        duration_ms: Optional request duration in milliseconds.

    Returns:
        Appended event.
    """
    safe_run_id = sanitize_run_id(run_id)
    if not _run_json_path(run_log_dir, safe_run_id).exists():
        raise FileNotFoundError(f"Agent run not found: {safe_run_id}")

    event = AgentRunEvent(
        event_id=f"evt-{uuid4().hex}",
        run_id=safe_run_id,
        timestamp=datetime.now(timezone.utc),
        method=method.upper(),
        path=redact_path(path),
        tool_name=tool_name,
        status_code=status_code,
        event_type=event_type,
        request_summary=redact_agent_event_payload(request_summary or {}),
        response_summary=redact_agent_event_payload(response_summary or {}),
        error_type=error_type,
        duration_ms=duration_ms,
        redacted=True,
    )
    with _events_jsonl_path(run_log_dir, safe_run_id).open("a", encoding="utf-8") as events_file:
        events_file.write(event.model_dump_json() + "\n")
    return event


def load_agent_run(run_log_dir: Path | str, run_id: str) -> AgentRun:
    """Load a local Agent API run with events.

    Args:
        run_log_dir: Directory containing run logs.
        run_id: Run identifier.

    Returns:
        Loaded run.
    """
    safe_run_id = sanitize_run_id(run_id)
    run_path = _run_json_path(run_log_dir, safe_run_id)
    if not run_path.exists():
        raise FileNotFoundError(f"Agent run not found: {safe_run_id}")
    run = AgentRun.model_validate_json(run_path.read_text(encoding="utf-8"))
    events_path = _events_jsonl_path(run_log_dir, safe_run_id)
    events: list[AgentRunEvent] = []
    if events_path.exists():
        for line in events_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                events.append(AgentRunEvent.model_validate_json(line))
    run.events = events
    return run


def list_agent_runs(run_log_dir: Path | str = DEFAULT_AGENT_RUN_LOG_DIR) -> list[AgentRun]:
    """List local Agent API runs in deterministic order.

    Args:
        run_log_dir: Directory containing run logs.

    Returns:
        Runs sorted by creation time and run ID.
    """
    root = Path(run_log_dir)
    if not root.exists():
        return []
    runs: list[AgentRun] = []
    for run_path in sorted(root.glob("*/run.json")):
        try:
            runs.append(load_agent_run(root, run_path.parent.name))
        except (OSError, ValueError):
            continue
    return sorted(runs, key=lambda run: (run.created_at, run.run_id))


def export_agent_run_bundle(
    run_log_dir: Path | str,
    run_id: str,
    output_dir: Path | str,
) -> Path:
    """Export run metadata, events, and replay result to a local bundle.

    Args:
        run_log_dir: Directory containing run logs.
        run_id: Run identifier.
        output_dir: Destination directory.

    Returns:
        Bundle directory path.
    """
    safe_run_id = sanitize_run_id(run_id)
    run = load_agent_run(run_log_dir, safe_run_id)
    replay = replay_agent_run(run_log_dir, safe_run_id)
    bundle_dir = Path(output_dir) / safe_run_id
    bundle_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(_run_json_path(run_log_dir, safe_run_id), bundle_dir / "run.json")
    shutil.copy2(_events_jsonl_path(run_log_dir, safe_run_id), bundle_dir / "events.jsonl")
    (bundle_dir / "run-with-events.json").write_text(
        run.model_dump_json(indent=2), encoding="utf-8"
    )
    (bundle_dir / "replay.json").write_text(replay.model_dump_json(indent=2), encoding="utf-8")
    return bundle_dir


def replay_agent_run(run_log_dir: Path | str, run_id: str) -> AgentReplayResult:
    """Replay a local Agent API run by validating recorded activity.

    Replay does not call Procore, does not execute tools, and does not read
    credentials. It verifies route shape, registered tool names, and that logged
    tool-call attempts remain disabled.

    Args:
        run_log_dir: Directory containing run logs.
        run_id: Run identifier.

    Returns:
        Replay validation result.
    """
    run = load_agent_run(run_log_dir, run_id)
    result = AgentReplayResult(
        run_id=run.run_id,
        passed=True,
        event_count=len(run.events),
        checked_at=datetime.now(timezone.utc),
    )
    for event in run.events:
        event_result = _replay_event(event)
        result.events.append(event_result)
        result.warnings.extend(event_result.warnings)
        result.errors.extend(event_result.errors)
        if not event_result.passed:
            result.passed = False
    if not run.events:
        result.warnings.append("Run has no events to replay.")
    return result


def redact_agent_event_payload(value: Any) -> Any:
    """Redact secret-like keys and signed URL values from local run data.

    Args:
        value: JSON-compatible value to redact.

    Returns:
        Redacted JSON-compatible value.
    """
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            if SENSITIVE_KEY_PATTERN.search(str(key)):
                redacted[str(key)] = "[REDACTED]"
            else:
                redacted[str(key)] = redact_agent_event_payload(item)
        return redacted
    if isinstance(value, list):
        return [redact_agent_event_payload(item) for item in value]
    if isinstance(value, str):
        return redact_path(value)
    return value


def redact_path(path: str) -> str:
    """Redact sensitive query values from a path or URL string."""
    return SIGNED_URL_PATTERN.sub(r"\1[REDACTED]", path)


def sanitize_run_id(run_id: str) -> str:
    """Return a filesystem-safe run identifier."""
    sanitized = SAFE_RUN_ID_PATTERN.sub("-", run_id.strip()).strip(".-")
    if not sanitized:
        raise ValueError("Run ID cannot be empty.")
    return sanitized[:120]


def _replay_event(event: AgentRunEvent) -> AgentReplayEventResult:
    """Validate one recorded event without executing it."""
    result = AgentReplayEventResult(event_id=event.event_id, path=event.path, passed=True)
    if not event.method:
        result.errors.append("Event is missing an HTTP method.")
    if not event.path:
        result.errors.append("Event is missing a request path.")
    if event.status_code <= 0:
        result.errors.append("Event has an invalid status code.")

    route_known = event.path in RECOGNIZED_ROUTES or _is_tool_route(event.path)
    if not route_known:
        result.warnings.append(f"Unknown Agent API route: {event.path}")

    if event.tool_name:
        try:
            get_agent_tool(event.tool_name)
        except AgentToolNotFoundError:
            result.warnings.append(f"Unknown registered tool: {event.tool_name}")

    if event.path.endswith("/call"):
        if event.status_code != 501 or event.error_type != "tool_execution_disabled":
            result.errors.append("Tool call event did not remain execution-disabled.")
        if event.response_summary.get("error") != "tool_execution_disabled":
            result.errors.append("Tool call response did not record tool_execution_disabled.")

    if result.errors:
        result.passed = False
    return result


def _is_tool_route(path: str) -> bool:
    """Return whether a path matches a known tool metadata route shape."""
    if not path.startswith("/agent/tools/"):
        return False
    tool_name = path.removeprefix("/agent/tools/").removesuffix("/call")
    return bool(tool_name)


def _run_dir(run_log_dir: Path | str, run_id: str) -> Path:
    """Return the run directory for a safe run ID."""
    return Path(run_log_dir) / sanitize_run_id(run_id)


def _run_json_path(run_log_dir: Path | str, run_id: str) -> Path:
    """Return the run metadata path."""
    return _run_dir(run_log_dir, run_id) / "run.json"


def _events_jsonl_path(run_log_dir: Path | str, run_id: str) -> Path:
    """Return the run events path."""
    return _run_dir(run_log_dir, run_id) / "events.jsonl"
