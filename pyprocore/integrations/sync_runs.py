"""Local JSON/JSONL sync run helpers for integration templates."""

from __future__ import annotations

import json
import secrets
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from pyprocore.core.exceptions import ValidationError
from pyprocore.integrations.models import (
    IntegrationSyncLogEntry,
    IntegrationSyncRun,
    IntegrationSyncRunStatus,
)

SECRET_FIELD_FRAGMENTS = (
    "token",
    "secret",
    "authorization",
    "password",
    "client_secret",
    "refresh",
    "access",
)
REDACTED = "[REDACTED]"


def create_sync_run(
    blueprint_name: str,
    output_dir: Path | str,
    *,
    run_id: str | None = None,
    summary: dict[str, Any] | None = None,
) -> IntegrationSyncRun:
    """Create and write a local sync run record.

    Args:
        blueprint_name: Blueprint name associated with the run.
        output_dir: Directory where local run files should be written.
        run_id: Optional caller-provided run identifier.
        summary: Optional sanitized summary metadata.

    Returns:
        Written sync run record.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    generated_run_id = (
        run_id or f"run_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{secrets.token_hex(4)}"
    )
    run = IntegrationSyncRun(
        run_id=generated_run_id,
        blueprint_name=blueprint_name,
        output_dir=str(output_path),
        summary=redact_sensitive_data(summary or {}),
        log_path=str(_sync_log_path(output_path, generated_run_id)),
    )
    _write_sync_run(run)
    return run


def append_sync_log(
    run: IntegrationSyncRun | Path | str,
    message: str,
    *,
    level: str = "info",
    data: dict[str, Any] | None = None,
) -> IntegrationSyncLogEntry:
    """Append a redacted local JSONL log entry to a sync run.

    Args:
        run: Sync run model or path to a sync run JSON file.
        message: Log message.
        level: Log level.
        data: Optional structured data to redact and store.

    Returns:
        Written log entry.
    """
    sync_run = read_sync_run(run) if isinstance(run, (str, Path)) else run
    entry = IntegrationSyncLogEntry(
        level=level,
        message=_redact_text(message),
        data=redact_sensitive_data(data or {}),
    )
    log_path = Path(sync_run.log_path or _sync_log_path(Path(sync_run.output_dir), sync_run.run_id))
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry.model_dump(mode="json"), sort_keys=True) + "\n")
    return entry


def complete_sync_run(
    run: IntegrationSyncRun | Path | str,
    *,
    summary: dict[str, Any] | None = None,
) -> IntegrationSyncRun:
    """Mark a local sync run record completed."""
    sync_run = read_sync_run(run) if isinstance(run, (str, Path)) else run
    sync_run.status = IntegrationSyncRunStatus.COMPLETED
    sync_run.completed_at = datetime.now(UTC).isoformat()
    if summary:
        sync_run.summary.update(redact_sensitive_data(summary))
    _write_sync_run(sync_run)
    return sync_run


def fail_sync_run(
    run: IntegrationSyncRun | Path | str,
    error_message: str,
    *,
    summary: dict[str, Any] | None = None,
) -> IntegrationSyncRun:
    """Mark a local sync run record failed with a redacted message."""
    sync_run = read_sync_run(run) if isinstance(run, (str, Path)) else run
    sync_run.status = IntegrationSyncRunStatus.FAILED
    sync_run.failed_at = datetime.now(UTC).isoformat()
    sync_run.error_message = _redact_text(error_message)
    if summary:
        sync_run.summary.update(redact_sensitive_data(summary))
    _write_sync_run(sync_run)
    return sync_run


def read_sync_run(path_or_run: IntegrationSyncRun | Path | str) -> IntegrationSyncRun:
    """Read a local sync run JSON file."""
    if isinstance(path_or_run, IntegrationSyncRun):
        return path_or_run
    path = Path(path_or_run)
    try:
        return IntegrationSyncRun.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, PydanticValidationError) as exc:
        raise ValidationError(f"Could not read sync run record from {path}: {exc}") from exc


def summarize_sync_runs(path: Path | str) -> dict[str, Any]:
    """Summarize local sync run JSON files below a path."""
    root = Path(path)
    files = [root] if root.is_file() else sorted(root.glob("*.json"))
    runs = [read_sync_run(file_path) for file_path in files]
    status_counts: dict[str, int] = {}
    for run in runs:
        status_counts[run.status.value] = status_counts.get(run.status.value, 0) + 1
    return {
        "path": str(root),
        "run_count": len(runs),
        "status_counts": dict(sorted(status_counts.items())),
        "runs": [run.model_dump(mode="json") for run in runs],
        "mode": "local_sync_run_files_only",
        "procore_api_call_required": False,
        "write_enabled": False,
    }


def redact_sensitive_data(value: Any) -> Any:
    """Redact common secret-like keys from structured sync data."""
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            if _is_secret_key(str(key)):
                redacted[str(key)] = REDACTED
            else:
                redacted[str(key)] = redact_sensitive_data(item)
        return redacted
    if isinstance(value, list):
        return [redact_sensitive_data(item) for item in value]
    if isinstance(value, tuple):
        return [redact_sensitive_data(item) for item in value]
    if isinstance(value, str):
        return _redact_text(value)
    return value


def _write_sync_run(run: IntegrationSyncRun) -> Path:
    path = _sync_run_path(Path(run.output_dir), run.run_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(run.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _sync_run_path(output_dir: Path, run_id: str) -> Path:
    return output_dir / f"{run_id}.json"


def _sync_log_path(output_dir: Path, run_id: str) -> Path:
    return output_dir / f"{run_id}.jsonl"


def _is_secret_key(key: str) -> bool:
    folded = key.casefold()
    return any(fragment in folded for fragment in SECRET_FIELD_FRAGMENTS)


def _redact_text(text: str) -> str:
    redacted = text
    for marker in ("Bearer ", "Token ", "client_secret=", "refresh_token=", "access_token="):
        if marker in redacted:
            prefix, _, remainder = redacted.partition(marker)
            redacted = prefix + marker + REDACTED
            if " " in remainder:
                redacted += " " + remainder.split(" ", 1)[1]
    return redacted
