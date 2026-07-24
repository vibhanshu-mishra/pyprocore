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
