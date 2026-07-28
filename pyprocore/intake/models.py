"""Typed models for read-only RFI and Submittal intake sync."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import Field

from pyprocore.models.base import ProcoreModel

FindingLevel = Literal["error", "warning", "info"]
RunStatus = Literal["planned", "completed", "completed_with_findings", "failed"]


class IntakeSyncConfig(ProcoreModel):
    """Configuration for a local read-only intake sync."""

    profile_path: str | None = None
    profile_name: str | None = None
    company_id: int | None = None
    project_ids: list[int] = Field(default_factory=list)
    include_rfis: bool = True
    include_submittals: bool = True
    include_attachments: bool = True
    updated_since: datetime | None = None
    output_dir: str = "./exports/intake"
    state_path: str | None = None
    max_items_per_project: int | None = None
    dry_run: bool = True
    overwrite: bool = False
    notes: list[str] = Field(default_factory=list)


class IntakeSyncFinding(ProcoreModel):
    """One validation, normalization, or sync finding."""

    level: FindingLevel
    code: str
    message: str
    project_id: int | None = None
    resource: str | None = None
    record_id: str | None = None


class IntakePermissionFinding(IntakeSyncFinding):
    """A finding related to DMSA or attachment visibility."""

    recommended_review: str


class IntakeSyncPlan(ProcoreModel):
    """A non-executing description of a planned intake sync."""

    profile_reference: str | None
    company_id: int | None
    project_ids: list[int]
    resources: list[str]
    output_dir: str
    state_path: str
    output_files: list[str]
    updated_since: datetime | None = None
    max_items_per_project: int | None = None
    include_attachments: bool = True
    dry_run: bool = True
    findings: list[IntakeSyncFinding] = Field(default_factory=list)
    safety_boundaries: list[str] = Field(default_factory=list)


class IntakeSyncState(ProcoreModel):
    """Local polling state for repeated intake sync runs."""

    schema_version: str = "1"
    profile_name: str | None = None
    company_id: int | None = None
    project_ids: list[int] = Field(default_factory=list)
    last_successful_sync_at: datetime | None = None
    last_attempted_sync_at: datetime | None = None
    per_project_rfi_sync_at: dict[str, datetime] = Field(default_factory=dict)
    per_project_submittal_sync_at: dict[str, datetime] = Field(default_factory=dict)
    last_run_status: RunStatus | None = None
    record_counts: dict[str, int] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class IntakeSyncStateUpdate(ProcoreModel):
    """State changes produced by one mocked intake run."""

    attempted_at: datetime
    successful_at: datetime | None = None
    status: RunStatus
    per_project_rfi_sync_at: dict[str, datetime] = Field(default_factory=dict)
    per_project_submittal_sync_at: dict[str, datetime] = Field(default_factory=dict)
    record_counts: dict[str, int] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class IntakeAttachmentRecord(ProcoreModel):
    """Normalized local attachment metadata."""

    source_resource: Literal["rfi", "submittal"]
    project_id: int
    parent_id: str | None = None
    parent_number: str | None = None
    id: str | None = None
    name: str
    url: str | None = None
    content_type: str | None = None
    size: int | None = None


class IntakeRfiRecord(ProcoreModel):
    """Normalized read-only RFI record."""

    source: Literal["rfi"] = "rfi"
    project_id: int
    id: str | None = None
    number: str | None = None
    title: str | None = None
    status: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    due_date: datetime | None = None
    ball_in_court: str | None = None
    responsible_contractor: str | None = None
    assignees: list[str] = Field(default_factory=list)
    cost_impact: str | None = None
    schedule_impact: str | None = None
    attachment_count: int = 0
    source_url: str | None = None


class IntakeSubmittalRecord(ProcoreModel):
    """Normalized read-only Submittal record."""

    source: Literal["submittal"] = "submittal"
    project_id: int
    id: str | None = None
    number: str | None = None
    title: str | None = None
    status: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    due_date: datetime | None = None
    ball_in_court: str | None = None
    responsible_contractor: str | None = None
    submitter: str | None = None
    approvers: list[str] = Field(default_factory=list)
    revision: str | None = None
    package: str | None = None
    attachment_count: int = 0
    source_url: str | None = None


class IntakeNormalizedRow(ProcoreModel):
    """A normalized row plus local findings and optional raw data."""

    resource: Literal["rfi", "submittal"]
    project_id: int
    record: IntakeRfiRecord | IntakeSubmittalRecord
    findings: list[IntakeSyncFinding] = Field(default_factory=list)
    raw_record: dict[str, Any] | None = None


class IntakeAttachmentManifestItem(ProcoreModel):
    """One attachment candidate in a local download manifest."""

    attachment: IntakeAttachmentRecord
    download_available: bool
    note: str


class IntakeAttachmentManifest(ProcoreModel):
    """Local attachment metadata manifest; it never downloads files."""

    generated_at: datetime
    items: list[IntakeAttachmentManifestItem] = Field(default_factory=list)
    note: str = (
        "Download availability depends on DMSA permissions and attachment URLs "
        "included in Procore payloads. This manifest does not download files."
    )


class IntakeSyncResourceResult(ProcoreModel):
    """Normalized results for one resource type and project."""

    project_id: int
    resource: Literal["rfis", "submittals"]
    received_count: int
    included_count: int
    filtered_count: int
    rows: list[IntakeNormalizedRow] = Field(default_factory=list)
    raw_records: list[dict[str, Any]] = Field(default_factory=list)
    findings: list[IntakeSyncFinding] = Field(default_factory=list)


class IntakeSyncSummary(ProcoreModel):
    """Summary counts and safety metadata for one intake run."""

    status: RunStatus
    project_count: int
    rfi_count: int
    submittal_count: int
    attachment_count: int
    finding_count: int
    started_at: datetime
    completed_at: datetime
    read_only: bool = True
    procore_calls_made: bool = False
    remote_downloads_made: bool = False
    write_actions_enabled: bool = False


class IntakeOutputManifest(ProcoreModel):
    """Manifest of local files planned or written by the output writer."""

    output_dir: str
    dry_run: bool
    planned_files: list[str] = Field(default_factory=list)
    written_files: list[str] = Field(default_factory=list)


class IntakeSyncRunResult(ProcoreModel):
    """Complete result of a local mocked intake run."""

    config: IntakeSyncConfig
    plan: IntakeSyncPlan
    resource_results: list[IntakeSyncResourceResult] = Field(default_factory=list)
    attachment_manifest: IntakeAttachmentManifest
    summary: IntakeSyncSummary
    findings: list[IntakeSyncFinding] = Field(default_factory=list)
    state_before: IntakeSyncState
    state_after: IntakeSyncState
    output_manifest: IntakeOutputManifest | None = None
