"""Tolerant local normalizers for RFI and Submittal payloads."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pyprocore.intake.models import (
    IntakeNormalizedRow,
    IntakeRfiRecord,
    IntakeSubmittalRecord,
    IntakeSyncFinding,
)


def normalize_rfi_record(
    record: dict[str, Any],
    project_id: int,
    *,
    preserve_raw: bool = True,
) -> IntakeNormalizedRow:
    """Normalize a flexible local RFI dictionary."""
    findings = _required_findings(record, project_id, "rfi")
    normalized = IntakeRfiRecord(
        project_id=project_id,
        id=_text(record.get("id")),
        number=_text(_first(record, "number", "rfi_number")),
        title=_text(_first(record, "title", "subject")),
        status=_named(_first(record, "status", "state")),
        created_at=_datetime(_first(record, "created_at", "created_date")),
        updated_at=_datetime(_first(record, "updated_at", "updated_date", "last_modified_at")),
        due_date=_datetime(_first(record, "due_date", "due_at")),
        ball_in_court=_named(_first(record, "ball_in_court", "ball_in_court_person")),
        responsible_contractor=_named(
            _first(record, "responsible_contractor", "responsible_company")
        ),
        assignees=_names(_first(record, "assignees", "assigned_to")),
        cost_impact=_named(record.get("cost_impact")),
        schedule_impact=_named(record.get("schedule_impact")),
        attachment_count=len(_attachment_values(record)),
        source_url=_text(_first(record, "source_url", "html_url", "web_url")),
    )
    return IntakeNormalizedRow(
        resource="rfi",
        project_id=project_id,
        record=normalized,
        findings=findings,
        raw_record=dict(record) if preserve_raw else None,
    )


def normalize_submittal_record(
    record: dict[str, Any],
    project_id: int,
    *,
    preserve_raw: bool = True,
) -> IntakeNormalizedRow:
    """Normalize a flexible local Submittal dictionary."""
    findings = _required_findings(record, project_id, "submittal")
    normalized = IntakeSubmittalRecord(
        project_id=project_id,
        id=_text(record.get("id")),
        number=_text(_first(record, "number", "submittal_number")),
        title=_text(_first(record, "title", "name")),
        status=_named(_first(record, "status", "state")),
        created_at=_datetime(_first(record, "created_at", "created_date")),
        updated_at=_datetime(_first(record, "updated_at", "updated_date", "last_modified_at")),
        due_date=_datetime(_first(record, "due_date", "due_at")),
        ball_in_court=_named(_first(record, "ball_in_court", "ball_in_court_person")),
        responsible_contractor=_named(
            _first(record, "responsible_contractor", "responsible_company")
        ),
        submitter=_named(_first(record, "submitter", "submitted_by")),
        approvers=_names(_first(record, "approvers", "approver")),
        revision=_text(_first(record, "revision", "revision_number")),
        package=_named(_first(record, "package", "submittal_package")),
        attachment_count=len(_attachment_values(record)),
        source_url=_text(_first(record, "source_url", "html_url", "web_url")),
    )
    return IntakeNormalizedRow(
        resource="submittal",
        project_id=project_id,
        record=normalized,
        findings=findings,
        raw_record=dict(record) if preserve_raw else None,
    )


def record_updated_at(record: dict[str, Any]) -> datetime | None:
    """Return a record's best available update timestamp."""
    return _datetime(_first(record, "updated_at", "updated_date", "last_modified_at"))


def attachment_values(record: dict[str, Any]) -> list[dict[str, Any]]:
    """Return attachment-like local dictionaries from common payload shapes."""
    return _attachment_values(record)


def _required_findings(
    record: dict[str, Any],
    project_id: int,
    resource: Literal["rfi", "submittal"],
) -> list[IntakeSyncFinding]:
    findings = []
    record_id = _text(record.get("id"))
    for key, aliases in (
        ("id", ("id",)),
        ("number", ("number", f"{resource}_number")),
        ("title", ("title", "subject", "name")),
    ):
        if not any(record.get(alias) not in (None, "") for alias in aliases):
            findings.append(
                IntakeSyncFinding(
                    level="warning",
                    code=f"missing_{key}",
                    message=f"{resource.title()} record is missing {key}.",
                    project_id=project_id,
                    resource=resource,
                    record_id=record_id,
                )
            )
    return findings


def _first(record: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = record.get(key)
        if value not in (None, ""):
            return value
    return None


def _text(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def _named(value: Any) -> str | None:
    if isinstance(value, dict):
        return _text(_first(value, "name", "label", "title", "email", "id"))
    return _text(value)


def _names(value: Any) -> list[str]:
    values = value if isinstance(value, list) else ([] if value in (None, "") else [value])
    return [name for item in values if (name := _named(item)) is not None]


def _datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None


def _attachment_values(record: dict[str, Any]) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    for key in ("attachments", "files", "documents"):
        candidate = record.get(key)
        if isinstance(candidate, list):
            values.extend(item for item in candidate if isinstance(item, dict))
        elif isinstance(candidate, dict):
            values.append(candidate)
    single = record.get("attachment")
    if isinstance(single, dict):
        values.append(single)
    return values
