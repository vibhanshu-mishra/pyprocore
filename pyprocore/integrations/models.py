"""Typed models for local integration blueprint metadata."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import Field

from pyprocore.models.base import ProcoreModel

INTEGRATION_SCHEMA_VERSION = "1"
INTEGRATION_MODE = "local_integration_blueprint_metadata_only"


class IntegrationFindingSeverity(str, Enum):
    """Severity for local integration readiness findings."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class IntegrationSyncRunStatus(str, Enum):
    """Lifecycle status for a local sync run record."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class IntegrationEndpoint(ProcoreModel):
    """Local metadata for an integration-facing endpoint template.

    Attributes:
        name: Stable endpoint name.
        description: Human-readable endpoint purpose.
        method: HTTP method a user might expose in their own service template.
        path: Example local service path.
        read_only: Whether the endpoint template is read-only.
        pseudocode: Non-executable guidance for implementing the endpoint.
    """

    name: str
    description: str
    method: str = "GET"
    path: str
    read_only: bool = True
    pseudocode: list[str] = Field(default_factory=list)


class IntegrationCredentialRequirement(ProcoreModel):
    """Credential or environment variable required by an integration blueprint."""

    name: str
    description: str
    required: bool = True
    secret: bool = False
    source: str = "environment"


class IntegrationSyncPlan(ProcoreModel):
    """Local sync plan metadata for a blueprint.

    Attributes:
        name: Stable plan name.
        description: What the plan exports or prepares.
        resources: Read-only Procore resources that the plan may use.
        output_files: Local file outputs the plan suggests.
        dry_run_supported: Whether users should dry-run this plan first.
        read_only: Whether the plan is read-only.
    """

    name: str
    description: str
    resources: list[str] = Field(default_factory=list)
    output_files: list[str] = Field(default_factory=list)
    dry_run_supported: bool = True
    read_only: bool = True


class IntegrationBlueprint(ProcoreModel):
    """Local template metadata for building a PyProcore integration.

    Blueprints are guidance only. They do not host infrastructure, schedule jobs,
    store secrets in a database, call Procore, or enable write actions.
    """

    schema_version: str = INTEGRATION_SCHEMA_VERSION
    name: str
    title: str
    description: str
    intended_use: str
    required_environment_variables: list[IntegrationCredentialRequirement] = Field(
        default_factory=list
    )
    required_pyprocore_capabilities: list[str] = Field(default_factory=list)
    endpoints: list[IntegrationEndpoint] = Field(default_factory=list)
    sync_plan: IntegrationSyncPlan | None = None
    local_output_files: list[str] = Field(default_factory=list)
    safety_boundaries: list[str] = Field(default_factory=list)
    suggested_deployment_notes: list[str] = Field(default_factory=list)
    no_secrets_guidance: list[str] = Field(default_factory=list)
    test_strategy: list[str] = Field(default_factory=list)
    example_commands: list[str] = Field(default_factory=list)
    pseudocode: list[str] = Field(default_factory=list)
    mode: str = INTEGRATION_MODE
    metadata_only: bool = True
    execution_enabled: bool = False
    procore_api_call_required: bool = False
    write_enabled: bool = False
    hosted_app_included: bool = False
    database_dependency_required: bool = False
    automatic_scheduler_enabled: bool = False
    remote_call_enabled: bool = False
    external_ai_required: bool = False
    mcp_execution_enabled: bool = False


class IntegrationSyncLogEntry(ProcoreModel):
    """One local JSONL log entry for a sync run."""

    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    level: str = "info"
    message: str
    data: dict[str, Any] = Field(default_factory=dict)


class IntegrationSyncRun(ProcoreModel):
    """Local JSON record for one integration sync run."""

    schema_version: str = INTEGRATION_SCHEMA_VERSION
    run_id: str
    blueprint_name: str
    status: IntegrationSyncRunStatus = IntegrationSyncRunStatus.RUNNING
    output_dir: str
    started_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    completed_at: str | None = None
    failed_at: str | None = None
    summary: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None
    log_path: str | None = None
    metadata_only: bool = True
    procore_api_call_required: bool = False
    write_enabled: bool = False


class IntegrationWebhookEvent(ProcoreModel):
    """Sanitized local webhook event fixture record."""

    schema_version: str = INTEGRATION_SCHEMA_VERSION
    event_id: str
    received_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    headers: dict[str, str] = Field(default_factory=dict)
    body: dict[str, Any] = Field(default_factory=dict)
    body_sha256: str
    signature_header: str | None = None
    signature_valid: bool | None = None
    mode: str = "local_webhook_fixture_only"
    hosted_receiver_included: bool = False
    procore_api_call_required: bool = False


class IntegrationAuditEvent(ProcoreModel):
    """Local audit event metadata for integration templates."""

    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    actor: str = "local"
    action: str
    target: str
    details: dict[str, Any] = Field(default_factory=dict)


class IntegrationReadinessFinding(ProcoreModel):
    """One local integration readiness finding."""

    severity: IntegrationFindingSeverity
    code: str
    message: str
    suggested_action: str | None = None


class IntegrationReadinessReport(ProcoreModel):
    """Local readiness report for one integration blueprint."""

    schema_version: str = INTEGRATION_SCHEMA_VERSION
    blueprint_name: str
    output_dir: str
    ready: bool
    finding_count: int
    findings: list[IntegrationReadinessFinding] = Field(default_factory=list)
    mode: str = INTEGRATION_MODE
    metadata_only: bool = True
    execution_enabled: bool = False
    procore_api_call_required: bool = False
    write_enabled: bool = False
    hosted_app_included: bool = False
    database_dependency_required: bool = False
    automatic_scheduler_enabled: bool = False
    remote_call_enabled: bool = False
