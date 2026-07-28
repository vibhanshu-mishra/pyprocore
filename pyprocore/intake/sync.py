"""Mocked/local RFI and Submittal intake sync runner."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal, Mapping

from pyprocore.core.exceptions import ValidationError
from pyprocore.intake.attachments import build_intake_attachment_manifest
from pyprocore.intake.models import (
    IntakeOutputManifest,
    IntakeSyncConfig,
    IntakeSyncFinding,
    IntakeSyncResourceResult,
    IntakeSyncRunResult,
    IntakeSyncState,
    IntakeSyncSummary,
)
from pyprocore.intake.normalizers import (
    normalize_rfi_record,
    normalize_submittal_record,
    record_updated_at,
)
from pyprocore.intake.planning import build_intake_sync_plan
from pyprocore.intake.state import build_initial_intake_sync_state


def run_intake_sync_with_records(
    config: IntakeSyncConfig,
    rfis_by_project: Mapping[int | str, list[dict[str, Any]]] | None = None,
    submittals_by_project: Mapping[int | str, list[dict[str, Any]]] | None = None,
    *,
    state: IntakeSyncState | None = None,
    preserve_raw: bool = True,
) -> IntakeSyncRunResult:
    """Run a complete intake workflow using only preloaded local records."""
    plan = build_intake_sync_plan(config)
    errors = [finding for finding in plan.findings if finding.level == "error"]
    if errors:
        raise ValidationError(
            "Invalid intake sync config: " + "; ".join(item.message for item in errors)
        )

    started_at = datetime.now(UTC)
    state_before = state or build_initial_intake_sync_state(config)
    resource_results: list[IntakeSyncResourceResult] = []
    attachment_inputs: list[tuple[Literal["rfi", "submittal"], int, dict[str, Any]]] = []
    all_findings: list[IntakeSyncFinding] = list(plan.findings)

    for project_id in config.project_ids:
        if config.include_rfis:
            result = _process_resource(
                "rfis",
                project_id,
                _records_for_project(rfis_by_project, project_id),
                config,
                preserve_raw,
            )
            resource_results.append(result)
            all_findings.extend(result.findings)
            attachment_inputs.extend(("rfi", project_id, record) for record in result.raw_records)
        if config.include_submittals:
            result = _process_resource(
                "submittals",
                project_id,
                _records_for_project(submittals_by_project, project_id),
                config,
                preserve_raw,
            )
            resource_results.append(result)
            all_findings.extend(result.findings)
            attachment_inputs.extend(
                ("submittal", project_id, record) for record in result.raw_records
            )

    attachment_manifest = build_intake_attachment_manifest(
        attachment_inputs if config.include_attachments else []
    )
    completed_at = datetime.now(UTC)
    rfi_count = sum(item.included_count for item in resource_results if item.resource == "rfis")
    submittal_count = sum(
        item.included_count for item in resource_results if item.resource == "submittals"
    )
    status: Literal["completed", "completed_with_findings"] = (
        "completed_with_findings" if all_findings else "completed"
    )
    summary = IntakeSyncSummary(
        status=status,
        project_count=len(config.project_ids),
        rfi_count=rfi_count,
        submittal_count=submittal_count,
        attachment_count=len(attachment_manifest.items),
        finding_count=len(all_findings),
        started_at=started_at,
        completed_at=completed_at,
    )
    state_after = _updated_state(
        state_before,
        config,
        completed_at,
        status,
        rfi_count,
        submittal_count,
        all_findings,
    )
    return IntakeSyncRunResult(
        config=config,
        plan=plan,
        resource_results=resource_results,
        attachment_manifest=attachment_manifest,
        summary=summary,
        findings=all_findings,
        state_before=state_before,
        state_after=state_after,
        output_manifest=IntakeOutputManifest(
            output_dir=config.output_dir,
            dry_run=True,
            planned_files=plan.output_files,
        ),
    )


def _process_resource(
    resource: str,
    project_id: int,
    records: list[dict[str, Any]],
    config: IntakeSyncConfig,
    preserve_raw: bool,
) -> IntakeSyncResourceResult:
    included = [
        record
        for record in records
        if config.updated_since is None
        or _is_at_or_after(record_updated_at(record), config.updated_since)
    ]
    if config.max_items_per_project is not None:
        included = included[: config.max_items_per_project]
    normalizer = normalize_rfi_record if resource == "rfis" else normalize_submittal_record
    rows = [normalizer(record, project_id, preserve_raw=preserve_raw) for record in included]
    findings = [finding for row in rows for finding in row.findings]
    if not records:
        findings.append(
            IntakeSyncFinding(
                level="info",
                code="empty_resource",
                message=(
                    f"No {resource} were supplied for project {project_id}. "
                    "In live use, review records and DMSA permissions."
                ),
                project_id=project_id,
                resource=resource,
            )
        )
    return IntakeSyncResourceResult(
        project_id=project_id,
        resource=resource,  # type: ignore[arg-type]
        received_count=len(records),
        included_count=len(included),
        filtered_count=len(records) - len(included),
        rows=rows,
        raw_records=[dict(record) for record in included] if preserve_raw else [],
        findings=findings,
    )


def _records_for_project(
    values: Mapping[int | str, list[dict[str, Any]]] | None,
    project_id: int,
) -> list[dict[str, Any]]:
    if not values:
        return []
    records = values.get(project_id, values.get(str(project_id), []))
    return [dict(item) for item in records if isinstance(item, dict)]


def _is_at_or_after(value: datetime | None, threshold: datetime) -> bool:
    if value is None:
        return False
    if value.tzinfo is None and threshold.tzinfo is not None:
        value = value.replace(tzinfo=UTC)
    if value.tzinfo is not None and threshold.tzinfo is None:
        threshold = threshold.replace(tzinfo=UTC)
    return value >= threshold


def _updated_state(
    state: IntakeSyncState,
    config: IntakeSyncConfig,
    completed_at: datetime,
    status: str,
    rfi_count: int,
    submittal_count: int,
    findings: list[IntakeSyncFinding],
) -> IntakeSyncState:
    rfi_times = dict(state.per_project_rfi_sync_at)
    submittal_times = dict(state.per_project_submittal_sync_at)
    for project_id in config.project_ids:
        if config.include_rfis:
            rfi_times[str(project_id)] = completed_at
        if config.include_submittals:
            submittal_times[str(project_id)] = completed_at
    return state.model_copy(
        update={
            "profile_name": state.profile_name or config.profile_name,
            "company_id": state.company_id or config.company_id,
            "project_ids": config.project_ids,
            "last_attempted_sync_at": completed_at,
            "last_successful_sync_at": completed_at,
            "last_run_status": status,
            "per_project_rfi_sync_at": rfi_times,
            "per_project_submittal_sync_at": submittal_times,
            "record_counts": {"rfis": rfi_count, "submittals": submittal_count},
            "warnings": [item.message for item in findings if item.level != "info"],
        }
    )
