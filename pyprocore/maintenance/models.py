"""Typed models for the local API maintenance assistant."""

from __future__ import annotations

from pydantic import Field

from pyprocore.catalog import CatalogEndpoint, CatalogEndpointSafety, CatalogParameter
from pyprocore.models.base import ProcoreModel

MAINTENANCE_SCHEMA_VERSION = "1"
MAINTENANCE_MODE = "local_oas_maintenance_assistant"


class ApiMaintenanceFinding(ProcoreModel):
    """A validation, safety, or review finding from the maintenance assistant."""

    severity: str
    code: str
    message: str


class ApiEndpointChange(ProcoreModel):
    """A detected difference between two local OAS endpoint catalogs."""

    change_type: str
    path: str
    method: str | None = None
    previous_method: str | None = None
    operation_id_before: str | None = None
    operation_id_after: str | None = None
    parameters_before: list[CatalogParameter] = Field(default_factory=list)
    parameters_after: list[CatalogParameter] = Field(default_factory=list)
    safety: CatalogEndpointSafety = CatalogEndpointSafety.UNKNOWN
    risky: bool = False
    details: list[str] = Field(default_factory=list)


class ApiDriftReport(ProcoreModel):
    """Local OAS-to-OAS API drift report."""

    schema_version: str = MAINTENANCE_SCHEMA_VERSION
    old_source_path: str
    new_source_path: str
    added_endpoints: list[ApiEndpointChange] = Field(default_factory=list)
    removed_endpoints: list[ApiEndpointChange] = Field(default_factory=list)
    changed_methods: list[ApiEndpointChange] = Field(default_factory=list)
    changed_parameters: list[ApiEndpointChange] = Field(default_factory=list)
    changed_operation_ids: list[ApiEndpointChange] = Field(default_factory=list)
    risky_changes: list[ApiEndpointChange] = Field(default_factory=list)
    findings: list[ApiMaintenanceFinding] = Field(default_factory=list)
    mode: str = MAINTENANCE_MODE
    remote_fetch_enabled: bool = False
    procore_calls_enabled: bool = False
    execution_enabled: bool = False
    human_review_required: bool = True


class ApiCoverageGap(ProcoreModel):
    """One supported, unsupported, risky, or unknown endpoint coverage result."""

    resource_family: str
    endpoint: CatalogEndpoint
    supported: bool
    recommendation: str
    deferred: bool = False
    notes: list[str] = Field(default_factory=list)


class ApiCoverageGapReport(ProcoreModel):
    """Coverage-gap analysis against PyProcore's known read coverage areas."""

    schema_version: str = MAINTENANCE_SCHEMA_VERSION
    source_path: str
    supported_areas: list[str] = Field(default_factory=list)
    unsupported_read_only: list[ApiCoverageGap] = Field(default_factory=list)
    unsupported_risky_write: list[ApiCoverageGap] = Field(default_factory=list)
    unknown: list[ApiCoverageGap] = Field(default_factory=list)
    recommended_next_candidates: list[ApiCoverageGap] = Field(default_factory=list)
    deferred_candidates: list[ApiCoverageGap] = Field(default_factory=list)
    findings: list[ApiMaintenanceFinding] = Field(default_factory=list)
    mode: str = MAINTENANCE_MODE
    remote_fetch_enabled: bool = False
    procore_calls_enabled: bool = False
    execution_enabled: bool = False
    human_review_required: bool = True


class ApiMaintenanceTask(ProcoreModel):
    """A human-review task proposed from local endpoint metadata."""

    category: str
    resource_family: str
    endpoint_path: str
    method: str
    safety_classification: CatalogEndpointSafety
    suggested_service_module: str
    suggested_model_name: str
    suggested_cli_command: str
    suggested_tests: list[str] = Field(default_factory=list)
    suggested_examples: list[str] = Field(default_factory=list)
    implementation_notes: list[str] = Field(default_factory=list)
    warning: str | None = None


class ApiMaintenancePlan(ProcoreModel):
    """A metadata-only implementation plan requiring maintainer review."""

    schema_version: str = MAINTENANCE_SCHEMA_VERSION
    source_path: str
    safe_read_only_candidates: list[ApiMaintenanceTask] = Field(default_factory=list)
    needs_endpoint_shape_review: list[ApiMaintenanceTask] = Field(default_factory=list)
    risky_write_deferred: list[ApiMaintenanceTask] = Field(default_factory=list)
    docs_only_updates: list[ApiMaintenanceTask] = Field(default_factory=list)
    tests_examples_needed: list[ApiMaintenanceTask] = Field(default_factory=list)
    findings: list[ApiMaintenanceFinding] = Field(default_factory=list)
    mode: str = MAINTENANCE_MODE
    remote_fetch_enabled: bool = False
    procore_calls_enabled: bool = False
    execution_enabled: bool = False
    human_review_required: bool = True


class ApiScaffoldFile(ProcoreModel):
    """One proposed draft file in a read-only endpoint scaffold."""

    relative_path: str
    purpose: str
    content: str
    draft: bool = True


class ApiScaffoldPlan(ProcoreModel):
    """A metadata-only plan for draft read-only endpoint files."""

    schema_version: str = MAINTENANCE_SCHEMA_VERSION
    source_path: str
    endpoint_path: str
    method: str
    safety_classification: CatalogEndpointSafety
    allowed: bool
    files: list[ApiScaffoldFile] = Field(default_factory=list)
    findings: list[ApiMaintenanceFinding] = Field(default_factory=list)
    mode: str = MAINTENANCE_MODE
    remote_fetch_enabled: bool = False
    procore_calls_enabled: bool = False
    execution_enabled: bool = False
    generated_tools: bool = False
    human_review_required: bool = True


class ApiScaffoldCopyResult(ProcoreModel):
    """Result of a local draft scaffold dry-run or copy operation."""

    plan: ApiScaffoldPlan
    output_dir: str
    dry_run: bool
    written_files: list[str] = Field(default_factory=list)
    skipped_files: list[str] = Field(default_factory=list)
    findings: list[ApiMaintenanceFinding] = Field(default_factory=list)


class CodebaseScanOptions(ProcoreModel):
    """Options controlling a bounded local customer-codebase scan."""

    extensions: list[str] = Field(
        default_factory=lambda: [
            ".py",
            ".md",
            ".rst",
            ".txt",
            ".sh",
            ".bash",
            ".zsh",
            ".yml",
            ".yaml",
            ".toml",
            ".json",
            ".cfg",
            ".conf",
            ".ini",
        ]
    )
    ignored_directories: list[str] = Field(
        default_factory=lambda: [
            ".git",
            ".venv",
            "venv",
            "env",
            "__pycache__",
            "node_modules",
            "dist",
            "build",
            "site",
            ".mypy_cache",
            ".pytest_cache",
            ".ruff_cache",
            "exports",
            "downloads",
            "secrets",
            ".secrets",
            "token_store",
            "token_stores",
        ]
    )
    ignored_filenames: list[str] = Field(
        default_factory=lambda: [
            ".env",
            "token.json",
            "tokens.json",
            "credentials.json",
        ]
    )
    max_file_size_bytes: int = 1_048_576
    include_hidden_files: bool = False


class CodebaseFileFinding(ProcoreModel):
    """A scanned or skipped local file finding."""

    path: str
    status: str
    reason: str | None = None
    size_bytes: int | None = None


class PyprocoreUsage(ProcoreModel):
    """Normalized PyProcore usage found in a local text or Python file."""

    usage_type: str
    file_path: str
    line_number: int | None = None
    symbol: str
    capability_family: str
    snippet: str | None = None
    confidence: str = "high"
    dynamic: bool = False


class PyprocoreCliUsage(PyprocoreUsage):
    """A detected ``procore-sdk`` command usage."""

    command: str


class PyprocoreImportUsage(PyprocoreUsage):
    """A detected Python import from the PyProcore package."""

    module: str
    imported_name: str | None = None


class PyprocoreCallUsage(PyprocoreUsage):
    """A detected object-client or helper call."""

    call_chain: str


class CodebaseScanReport(ProcoreModel):
    """Bounded local report of PyProcore usage in a customer codebase."""

    schema_version: str = MAINTENANCE_SCHEMA_VERSION
    scanned_path: str
    options: CodebaseScanOptions
    files_scanned: list[CodebaseFileFinding] = Field(default_factory=list)
    files_skipped: list[CodebaseFileFinding] = Field(default_factory=list)
    imports: list[PyprocoreImportUsage] = Field(default_factory=list)
    calls: list[PyprocoreCallUsage] = Field(default_factory=list)
    cli_usages: list[PyprocoreCliUsage] = Field(default_factory=list)
    usages: list[PyprocoreUsage] = Field(default_factory=list)
    capability_counts: dict[str, int] = Field(default_factory=dict)
    findings: list[ApiMaintenanceFinding] = Field(default_factory=list)
    mode: str = "local_customer_codebase_scan"
    files_modified: bool = False
    remote_repo_access_enabled: bool = False
    procore_calls_enabled: bool = False
    external_ai_calls_enabled: bool = False
    execution_enabled: bool = False
    human_review_required: bool = True


class ImpactedUsage(ProcoreModel):
    """One normalized usage annotated with a possible API impact."""

    usage: PyprocoreUsage
    severity: str
    reasons: list[str] = Field(default_factory=list)


class MigrationSuggestion(ProcoreModel):
    """A human-review action suggested by the impact scanner."""

    capability_family: str
    priority: str
    action: str


class ApiImpactFinding(ProcoreModel):
    """Possible impact of local OAS drift on one capability family."""

    classification: str
    capability_family: str
    message: str
    changed_endpoint_paths: list[str] = Field(default_factory=list)
    impacted_usages: list[ImpactedUsage] = Field(default_factory=list)
    suggested_actions: list[str] = Field(default_factory=list)


class ApiImpactReport(ProcoreModel):
    """Local human-review report relating code usage to optional OAS drift."""

    schema_version: str = MAINTENANCE_SCHEMA_VERSION
    scanned_path: str
    scan_report: CodebaseScanReport
    drift_report: ApiDriftReport | None = None
    oas_comparison_provided: bool = False
    findings: list[ApiImpactFinding] = Field(default_factory=list)
    impacted_usages: list[ImpactedUsage] = Field(default_factory=list)
    migration_suggestions: list[MigrationSuggestion] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    mode: str = "local_customer_codebase_impact_scan"
    files_modified: bool = False
    remote_repo_access_enabled: bool = False
    procore_calls_enabled: bool = False
    external_ai_calls_enabled: bool = False
    execution_enabled: bool = False
    human_review_required: bool = True


class MigrationPatchPlanOptions(ProcoreModel):
    """Options controlling conservative migration patch planning."""

    include_suggested_diffs: bool = True
    include_no_action_suggestions: bool = True


class MigrationSafetyFinding(ProcoreModel):
    """A safety boundary or manual-review finding from migration planning."""

    severity: str
    code: str
    message: str


class MigrationPatchHunk(ProcoreModel):
    """One non-applied, human-review unified diff hunk."""

    file_path: str
    line_number: int
    original_text: str
    suggested_text: str
    unified_diff: str
    applied: bool = False
    human_review_required: bool = True


class MigrationPatchSuggestion(ProcoreModel):
    """One conservative migration or review suggestion for detected usage."""

    suggestion_id: str
    category: str
    severity: str
    message: str
    file_path: str
    line_number: int | None = None
    capability_family: str
    usage_type: str
    source_snippet: str | None = None
    related_endpoint_paths: list[str] = Field(default_factory=list)
    manual_review_only: bool = True
    exact_change_safe: bool = False
    hunk: MigrationPatchHunk | None = None


class MigrationPatchFile(ProcoreModel):
    """Suggestions grouped for one scanned customer file."""

    file_path: str
    suggestions: list[MigrationPatchSuggestion] = Field(default_factory=list)
    hunks: list[MigrationPatchHunk] = Field(default_factory=list)


class MigrationPatchPlan(ProcoreModel):
    """Local migration patch plan that never modifies customer files."""

    schema_version: str = MAINTENANCE_SCHEMA_VERSION
    scanned_path: str
    options: MigrationPatchPlanOptions
    impact_report: ApiImpactReport
    impacted_files: list[str] = Field(default_factory=list)
    suggestions: list[MigrationPatchSuggestion] = Field(default_factory=list)
    files: list[MigrationPatchFile] = Field(default_factory=list)
    manual_review_checklist: list[str] = Field(default_factory=list)
    safety_findings: list[MigrationSafetyFinding] = Field(default_factory=list)
    mode: str = "local_migration_patch_plan"
    customer_files_modified: bool = False
    patches_applied: bool = False
    git_operations_enabled: bool = False
    remote_repo_access_enabled: bool = False
    procore_calls_enabled: bool = False
    external_ai_calls_enabled: bool = False
    execution_enabled: bool = False
    human_review_required: bool = True


class MigrationPatchArtifact(ProcoreModel):
    """One optional local patch-plan artifact."""

    relative_path: str
    content: str
    purpose: str


class MigrationPatchReport(ProcoreModel):
    """Result of a migration patch artifact dry-run or local write."""

    plan: MigrationPatchPlan
    output_dir: str
    dry_run: bool
    artifacts: list[MigrationPatchArtifact] = Field(default_factory=list)
    written_files: list[str] = Field(default_factory=list)
    planned_files: list[str] = Field(default_factory=list)
    safety_findings: list[MigrationSafetyFinding] = Field(default_factory=list)
    customer_files_modified: bool = False
    patches_applied: bool = False
    git_operations_enabled: bool = False
    human_review_required: bool = True


class PullRequestDraftOptions(ProcoreModel):
    """Options controlling local pull-request draft content."""

    include_suggested_changes: bool = True
    include_no_action_suggestions: bool = True


class PullRequestDraftChecklistItem(ProcoreModel):
    """One human-review checklist item in a local PR draft pack."""

    category: str
    text: str
    required: bool = True
    completed: bool = False


class PullRequestDraftRiskSummary(ProcoreModel):
    """Migration suggestions grouped by conservative review priority."""

    high: list[MigrationPatchSuggestion] = Field(default_factory=list)
    medium: list[MigrationPatchSuggestion] = Field(default_factory=list)
    low: list[MigrationPatchSuggestion] = Field(default_factory=list)
    unknown_manual_review: list[MigrationPatchSuggestion] = Field(default_factory=list)


class PullRequestDraftSection(ProcoreModel):
    """One titled Markdown section in the proposed PR body."""

    heading: str
    content: str


class PullRequestDraftArtifact(ProcoreModel):
    """One local PR-draft artifact that may be written on explicit request."""

    relative_path: str
    purpose: str
    content: str


class PullRequestDraftPack(ProcoreModel):
    """Local human-review PR draft package derived from migration metadata."""

    schema_version: str = MAINTENANCE_SCHEMA_VERSION
    scanned_path: str
    options: PullRequestDraftOptions
    migration_plan: MigrationPatchPlan
    title: str
    body: str
    sections: list[PullRequestDraftSection] = Field(default_factory=list)
    review_checklist: list[PullRequestDraftChecklistItem] = Field(default_factory=list)
    test_plan: list[str] = Field(default_factory=list)
    risk_summary: PullRequestDraftRiskSummary
    impacted_files: list[str] = Field(default_factory=list)
    artifacts: list[PullRequestDraftArtifact] = Field(default_factory=list)
    mode: str = "local_pr_draft_pack"
    customer_files_modified: bool = False
    patches_applied: bool = False
    git_operations_enabled: bool = False
    github_api_calls_enabled: bool = False
    pull_request_opened: bool = False
    remote_repo_access_enabled: bool = False
    procore_calls_enabled: bool = False
    external_ai_calls_enabled: bool = False
    execution_enabled: bool = False
    human_review_required: bool = True


class PullRequestDraftReport(ProcoreModel):
    """Result of a PR draft pack dry-run or explicit local artifact write."""

    pack: PullRequestDraftPack
    output_dir: str
    dry_run: bool
    artifacts: list[PullRequestDraftArtifact] = Field(default_factory=list)
    planned_files: list[str] = Field(default_factory=list)
    written_files: list[str] = Field(default_factory=list)
    findings: list[MigrationSafetyFinding] = Field(default_factory=list)
    customer_files_modified: bool = False
    patches_applied: bool = False
    git_operations_enabled: bool = False
    github_api_calls_enabled: bool = False
    pull_request_opened: bool = False
    human_review_required: bool = True


class ApiCompatibilityContractOptions(ProcoreModel):
    """Options controlling deterministic compatibility contract metadata."""

    generated_at: str | None = None


class ApiCompatibilityOperation(ProcoreModel):
    """One supported SDK operation described by compatibility metadata."""

    name: str
    read_only: bool = True
    local_only: bool = False


class ApiCompatibilityResource(ProcoreModel):
    """One supported capability or resource family."""

    name: str
    category: str
    operations: list[ApiCompatibilityOperation] = Field(default_factory=list)
    read_only: bool = True
    local_only: bool = False


class ApiCompatibilitySafetyBoundary(ProcoreModel):
    """One explicit compatibility contract safety boundary."""

    name: str
    status: str
    description: str


class ApiCompatibilityDeprecation(ProcoreModel):
    """Deprecated or removed helper metadata with required migration guidance."""

    helper: str
    status: str = "deprecated"
    migration_note: str


class ApiCompatibilityKnownGap(ProcoreModel):
    """One known deferred, risky, or unsupported resource family."""

    family: str
    status: str
    reason: str


class ApiCompatibilityValidationFinding(ProcoreModel):
    """One contract validation or codebase compatibility finding."""

    severity: str
    code: str
    message: str
    file_path: str | None = None
    symbol: str | None = None
    family: str | None = None
    migration_note: str | None = None


class ApiCompatibilityContract(ProcoreModel):
    """Machine-readable local compatibility metadata for one SDK version."""

    contract_schema_version: str
    pyprocore_version: str
    generated_at: str | None = None
    resources: list[ApiCompatibilityResource] = Field(default_factory=list)
    supported_read_only_service_areas: list[str] = Field(default_factory=list)
    supported_cli_groups: list[str] = Field(default_factory=list)
    local_only_features: list[str] = Field(default_factory=list)
    safety_boundaries: list[ApiCompatibilitySafetyBoundary] = Field(default_factory=list)
    deprecations: list[ApiCompatibilityDeprecation] = Field(default_factory=list)
    removed_helpers: list[ApiCompatibilityDeprecation] = Field(default_factory=list)
    known_gaps: list[ApiCompatibilityKnownGap] = Field(default_factory=list)
    mode: str = "local_api_compatibility_contract"
    certification: bool = False
    human_review_required: bool = True


class ApiCompatibilityChange(ProcoreModel):
    """One detected difference between two local compatibility contracts."""

    change_type: str
    subject: str
    before: str | None = None
    after: str | None = None
    risk_level: str
    migration_note: str


class ApiCompatibilityDiffReport(ProcoreModel):
    """Differences between two local JSON compatibility contracts."""

    old_contract_path: str
    new_contract_path: str
    added_resource_families: list[str] = Field(default_factory=list)
    removed_resource_families: list[str] = Field(default_factory=list)
    changed_safety_boundaries: list[ApiCompatibilityChange] = Field(default_factory=list)
    added_cli_groups: list[str] = Field(default_factory=list)
    removed_cli_groups: list[str] = Field(default_factory=list)
    added_deprecations: list[ApiCompatibilityDeprecation] = Field(default_factory=list)
    removed_deprecations: list[ApiCompatibilityDeprecation] = Field(default_factory=list)
    changed_known_gaps: list[ApiCompatibilityChange] = Field(default_factory=list)
    changes: list[ApiCompatibilityChange] = Field(default_factory=list)
    risk_level: str = "low"
    human_review_required: bool = True


class ApiCompatibilityValidationReport(ProcoreModel):
    """Validation result for local compatibility metadata."""

    valid: bool
    findings: list[ApiCompatibilityValidationFinding] = Field(default_factory=list)
    contract: ApiCompatibilityContract | None = None
    human_review_required: bool = True


class CodebaseCompatibilityReport(ProcoreModel):
    """Local codebase usage compared with one compatibility contract."""

    scanned_path: str
    contract_path: str
    contract_version: str
    scan_report: CodebaseScanReport
    compatible: list[ApiCompatibilityValidationFinding] = Field(default_factory=list)
    deprecated: list[ApiCompatibilityValidationFinding] = Field(default_factory=list)
    removed: list[ApiCompatibilityValidationFinding] = Field(default_factory=list)
    unknown_manual_review: list[ApiCompatibilityValidationFinding] = Field(default_factory=list)
    local_only: list[ApiCompatibilityValidationFinding] = Field(default_factory=list)
    customer_files_modified: bool = False
    patches_applied: bool = False
    remote_fetch_enabled: bool = False
    procore_calls_enabled: bool = False
    git_operations_enabled: bool = False
    github_api_calls_enabled: bool = False
    external_ai_calls_enabled: bool = False
    execution_enabled: bool = False
    human_review_required: bool = True
