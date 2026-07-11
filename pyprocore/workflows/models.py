"""Typed models for higher-level workflow automation results."""

from __future__ import annotations

from pathlib import Path

from pydantic import ConfigDict, Field

from pyprocore.models.base import ProcoreModel


class SyncedItem(ProcoreModel):
    """One Procore item written to a local workflow sync folder.

    Attributes:
        id: Procore item ID.
        number: RFI or submittal number when available.
        title: Human-readable item title.
        folder: Local folder created for the item.
        status: Item status when available.
        summary_path: Markdown summary path when Markdown output is enabled.
        item_json_path: JSON metadata path.
        attachment_count: Number of attachments reported by the item payload.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True, arbitrary_types_allowed=True)

    id: int
    number: str | None = None
    title: str | None = None
    folder: Path
    status: str | None = None
    summary_path: Path | None = None
    item_json_path: Path | None = None
    attachment_count: int = 0


class SyncResult(ProcoreModel):
    """Result returned after syncing Procore items to a local folder.

    Attributes:
        output_dir: Root folder used for the sync.
        item_type: Synced item type, such as ``rfi`` or ``submittal``.
        project_id: Procore project ID used for the sync.
        item_count: Number of items written locally.
        tracker_path: Optional CSV tracker path.
        manifest_path: JSON manifest path when a manifest was written.
        downloaded_files: Attachment paths returned by download helpers.
        skipped_files: Files skipped by the workflow layer.
        errors: Non-fatal workflow errors when available.
        warnings: Workflow warnings such as dry-run notes.
        dry_run: Whether the sync only planned local outputs.
        summary_path: Markdown summary report path when written.
        synced_count: Number of items written during this run.
        skipped_count: Number of unchanged items skipped by state.
        warning_count: Number of warnings.
        error_count: Number of errors.
        state_path: Incremental state file path.
        incremental: Whether incremental state mode was enabled.
        items: Item folder metadata.
        skipped_items: Unchanged items skipped by incremental mode.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True, arbitrary_types_allowed=True)

    output_dir: Path
    item_type: str
    project_id: int
    item_count: int
    tracker_path: Path | None = None
    manifest_path: Path | None = None
    downloaded_files: list[Path] = Field(default_factory=list)
    skipped_files: list[Path] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    dry_run: bool = False
    summary_path: Path | None = None
    synced_count: int | None = None
    skipped_count: int = 0
    warning_count: int = 0
    error_count: int = 0
    state_path: Path | None = None
    incremental: bool = False
    items: list[SyncedItem] = Field(default_factory=list)
    skipped_items: list[SyncedItem] = Field(default_factory=list)


class SyncStateItem(ProcoreModel):
    """One item recorded in a local incremental sync state file."""

    model_config = ConfigDict(extra="allow", populate_by_name=True, arbitrary_types_allowed=True)

    id: int
    number: str | None = None
    updated_at: str | None = None
    folder: str


class SyncState(ProcoreModel):
    """Local sync state used to skip unchanged items."""

    project_id: int
    item_type: str
    last_sync_at: str | None = None
    items: dict[str, SyncStateItem] = Field(default_factory=dict)


class ProjectSyncResult(ProcoreModel):
    """Result returned by a combined project folder sync."""

    model_config = ConfigDict(extra="allow", populate_by_name=True, arbitrary_types_allowed=True)

    output_dir: Path
    project_id: int
    item_count: int
    synced_count: int
    skipped_count: int
    warning_count: int
    error_count: int
    dry_run: bool = False
    incremental: bool = False
    rfi_result: SyncResult | None = None
    submittal_result: SyncResult | None = None
    manifest_path: Path | None = None
    summary_path: Path | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class ProjectContextOptions(ProcoreModel):
    """Options used to build an AI-ready project context package."""

    model_config = ConfigDict(extra="allow", populate_by_name=True, arbitrary_types_allowed=True)

    project_id: int
    company_id: int | None = None
    output_dir: Path
    include: list[str] | None = None
    exclude: list[str] | None = None
    start_date: str | None = None
    end_date: str | None = None
    log_date: str | None = None
    max_items: int | None = None
    download_files: bool = False
    overwrite: bool = False
    continue_on_error: bool = True


class ProjectContextSectionResult(ProcoreModel):
    """Result for one attempted project context package section."""

    model_config = ConfigDict(extra="allow", populate_by_name=True, arbitrary_types_allowed=True)

    name: str
    status: str
    item_count: int = 0
    files_written: list[Path] = Field(default_factory=list)
    downloaded_files: list[Path] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class ProjectContextManifest(ProcoreModel):
    """Manifest metadata for an AI-ready project context package."""

    model_config = ConfigDict(extra="allow", populate_by_name=True, arbitrary_types_allowed=True)

    created_at: str
    package_version: str
    project_id: int
    company_id: int | None = None
    output_dir: Path
    options: ProjectContextOptions
    sections_attempted: list[str] = Field(default_factory=list)
    sections_completed: list[str] = Field(default_factory=list)
    sections_failed: list[str] = Field(default_factory=list)
    sections_skipped: list[str] = Field(default_factory=list)
    file_paths_written: list[Path] = Field(default_factory=list)
    item_counts: dict[str, int] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    live_downloads_enabled: bool = False
    duration_seconds: float | None = None
    sections: list[ProjectContextSectionResult] = Field(default_factory=list)


class ProjectContextResult(ProcoreModel):
    """Result returned after building a project context package."""

    model_config = ConfigDict(extra="allow", populate_by_name=True, arbitrary_types_allowed=True)

    output_dir: Path
    project_id: int
    company_id: int | None = None
    manifest_path: Path
    summary_path: Path
    errors_path: Path | None = None
    warnings_path: Path | None = None
    manifest: ProjectContextManifest


class EnhancedRFIPackageOptions(ProcoreModel):
    """Options used to build an enhanced AI-ready RFI package."""

    model_config = ConfigDict(extra="allow", populate_by_name=True, arbitrary_types_allowed=True)

    project_id: int
    rfi_id: int | None = None
    rfi_number: str | None = None
    company_id: int | None = None
    output_dir: Path
    include_related: bool = True
    related_sections: list[str] | None = None
    exclude_related: list[str] | None = None
    search_terms: list[str] = Field(default_factory=list)
    start_date: str | None = None
    end_date: str | None = None
    log_date: str | None = None
    max_related_items: int = 25
    download_files: bool = False
    overwrite: bool = False
    continue_on_error: bool = True


class EnhancedRFIRelatedSectionResult(ProcoreModel):
    """Result for one related-context section in an enhanced RFI package."""

    model_config = ConfigDict(extra="allow", populate_by_name=True, arbitrary_types_allowed=True)

    name: str
    status: str
    item_count: int = 0
    files_written: list[Path] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class EnhancedRFIPackageManifest(ProcoreModel):
    """Manifest metadata for an enhanced RFI package."""

    model_config = ConfigDict(extra="allow", populate_by_name=True, arbitrary_types_allowed=True)

    created_at: str
    project_id: int
    company_id: int | None = None
    rfi_id: int
    rfi_number: str | None = None
    output_dir: Path
    options: EnhancedRFIPackageOptions
    sections_attempted: list[str] = Field(default_factory=list)
    sections_completed: list[str] = Field(default_factory=list)
    sections_failed: list[str] = Field(default_factory=list)
    files_written: list[Path] = Field(default_factory=list)
    related_item_counts: dict[str, int] = Field(default_factory=dict)
    downloads_enabled: bool = False
    downloaded_files: list[Path] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    related_sections: list[EnhancedRFIRelatedSectionResult] = Field(default_factory=list)


class EnhancedRFIPackageResult(ProcoreModel):
    """Result returned after building an enhanced RFI package."""

    model_config = ConfigDict(extra="allow", populate_by_name=True, arbitrary_types_allowed=True)

    output_dir: Path
    project_id: int
    company_id: int | None = None
    rfi_id: int
    rfi_number: str | None = None
    manifest_path: Path
    summary_path: Path
    rfi_json_path: Path
    review_context_path: Path
    errors_path: Path | None = None
    warnings_path: Path | None = None
    manifest: EnhancedRFIPackageManifest


class EnhancedSubmittalPackageOptions(ProcoreModel):
    """Options used to build an enhanced AI-ready submittal package."""

    model_config = ConfigDict(extra="allow", populate_by_name=True, arbitrary_types_allowed=True)

    project_id: int
    submittal_id: int | None = None
    submittal_number: str | None = None
    company_id: int | None = None
    output_dir: Path
    include_related: bool = True
    related_sections: list[str] | None = None
    exclude_related: list[str] | None = None
    search_terms: list[str] = Field(default_factory=list)
    start_date: str | None = None
    end_date: str | None = None
    log_date: str | None = None
    max_related_items: int = 25
    download_files: bool = False
    overwrite: bool = False
    continue_on_error: bool = True


class EnhancedSubmittalRelatedSectionResult(ProcoreModel):
    """Result for one related-context section in an enhanced submittal package."""

    model_config = ConfigDict(extra="allow", populate_by_name=True, arbitrary_types_allowed=True)

    name: str
    status: str
    item_count: int = 0
    files_written: list[Path] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class EnhancedSubmittalPackageManifest(ProcoreModel):
    """Manifest metadata for an enhanced submittal package."""

    model_config = ConfigDict(extra="allow", populate_by_name=True, arbitrary_types_allowed=True)

    created_at: str
    project_id: int
    company_id: int | None = None
    submittal_id: int
    submittal_number: str | None = None
    output_dir: Path
    options: EnhancedSubmittalPackageOptions
    sections_attempted: list[str] = Field(default_factory=list)
    sections_completed: list[str] = Field(default_factory=list)
    sections_failed: list[str] = Field(default_factory=list)
    files_written: list[Path] = Field(default_factory=list)
    related_item_counts: dict[str, int] = Field(default_factory=dict)
    downloads_enabled: bool = False
    downloaded_files: list[Path] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    related_sections: list[EnhancedSubmittalRelatedSectionResult] = Field(default_factory=list)


class EnhancedSubmittalPackageResult(ProcoreModel):
    """Result returned after building an enhanced submittal package."""

    model_config = ConfigDict(extra="allow", populate_by_name=True, arbitrary_types_allowed=True)

    output_dir: Path
    project_id: int
    company_id: int | None = None
    submittal_id: int
    submittal_number: str | None = None
    manifest_path: Path
    summary_path: Path
    submittal_json_path: Path
    review_context_path: Path
    approval_review_path: Path
    errors_path: Path | None = None
    warnings_path: Path | None = None
    manifest: EnhancedSubmittalPackageManifest


class AIExportOptions(ProcoreModel):
    """Options used to build a local AI review export."""

    model_config = ConfigDict(extra="allow", populate_by_name=True, arbitrary_types_allowed=True)

    package_dir: Path
    output_dir: Path
    export_name: str | None = None
    format: str = "markdown"
    include_json: bool = True
    include_prompt: bool = True
    include_checklists: bool = True
    max_chunk_chars: int = 12000
    source_extensions: list[str] | None = None
    exclude_patterns: list[str] | None = None
    overwrite: bool = False


class AIExportChunk(ProcoreModel):
    """One chunk file generated for an AI review export."""

    model_config = ConfigDict(extra="allow", populate_by_name=True, arbitrary_types_allowed=True)

    path: Path
    source_paths: list[Path] = Field(default_factory=list)
    char_count: int = 0


class AIExportSource(ProcoreModel):
    """One source file considered for an AI review export."""

    model_config = ConfigDict(extra="allow", populate_by_name=True, arbitrary_types_allowed=True)

    relative_path: str
    file_type: str
    size: int
    included: bool
    reason: str | None = None
    role: str | None = None
    chunk_files: list[Path] = Field(default_factory=list)


class AIExportManifest(ProcoreModel):
    """Manifest metadata for a local AI review export."""

    model_config = ConfigDict(extra="allow", populate_by_name=True, arbitrary_types_allowed=True)

    created_at: str
    package_dir: Path
    output_dir: Path
    package_type: str
    options: AIExportOptions
    sources: list[AIExportSource] = Field(default_factory=list)
    chunks: list[AIExportChunk] = Field(default_factory=list)
    files_written: list[Path] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class AIExportResult(ProcoreModel):
    """Result returned after building a local AI review export."""

    model_config = ConfigDict(extra="allow", populate_by_name=True, arbitrary_types_allowed=True)

    output_dir: Path
    package_dir: Path
    package_type: str
    manifest_path: Path
    ai_review_path: Path
    ai_review_json_path: Path | None = None
    prompt_path: Path | None = None
    system_context_path: Path | None = None
    source_index_json_path: Path
    source_index_md_path: Path
    chunk_paths: list[Path] = Field(default_factory=list)
    checklist_paths: list[Path] = Field(default_factory=list)
    warnings_path: Path | None = None
    errors_path: Path | None = None
    manifest: AIExportManifest


class WorkflowStep(ProcoreModel):
    """One step in a local workflow automation plan."""

    model_config = ConfigDict(extra="allow", populate_by_name=True, arbitrary_types_allowed=True)

    id: str
    workflow: str
    options: dict[str, object] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)
    continue_on_error: bool | None = None
    enabled: bool = True


class WorkflowPlan(ProcoreModel):
    """Local automation plan loaded from JSON or YAML."""

    model_config = ConfigDict(extra="allow", populate_by_name=True, arbitrary_types_allowed=True)

    name: str
    description: str | None = None
    defaults: dict[str, object] = Field(default_factory=dict)
    continue_on_error: bool = True
    steps: list[WorkflowStep] = Field(default_factory=list)


class WorkflowRunOptions(ProcoreModel):
    """Options used when running a local workflow plan."""

    model_config = ConfigDict(extra="allow", populate_by_name=True, arbitrary_types_allowed=True)

    output_dir: Path
    dry_run: bool = False
    continue_on_error: bool = True


class WorkflowStepResult(ProcoreModel):
    """Execution result for one local workflow plan step."""

    model_config = ConfigDict(extra="allow", populate_by_name=True, arbitrary_types_allowed=True)

    id: str
    workflow: str
    status: str = "pending"
    options: dict[str, object] = Field(default_factory=dict)
    started_at: str | None = None
    finished_at: str | None = None
    duration_seconds: float | None = None
    output_dir: Path | None = None
    files_written: list[Path] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    skip_reason: str | None = None


class WorkflowRunManifest(ProcoreModel):
    """Manifest metadata for a local workflow plan run."""

    model_config = ConfigDict(extra="allow", populate_by_name=True, arbitrary_types_allowed=True)

    run_id: str
    plan_name: str
    description: str | None = None
    status: str
    started_at: str
    finished_at: str | None = None
    duration_seconds: float | None = None
    dry_run: bool = False
    continue_on_error: bool = True
    output_dir: Path
    steps: list[WorkflowStepResult] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class WorkflowRunResult(ProcoreModel):
    """Result returned after validating or running a local workflow plan."""

    model_config = ConfigDict(extra="allow", populate_by_name=True, arbitrary_types_allowed=True)

    run_id: str
    plan: WorkflowPlan
    output_dir: Path
    status: str
    dry_run: bool = False
    manifest_path: Path
    summary_path: Path
    resolved_plan_path: Path
    errors_path: Path | None = None
    warnings_path: Path | None = None
    manifest: WorkflowRunManifest
