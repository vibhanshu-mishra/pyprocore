"""Typed models for local DMSA connection profile planning."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from pyprocore.models.base import ProcoreModel

FindingLevel = Literal["error", "warning", "info"]


class DmsaConnectionProfileInput(ProcoreModel):
    """User-provided metadata used to build a DMSA connection profile."""

    profile_name: str = "procore-dmsa"
    company_id: int | None = None
    allowed_project_ids: list[int] = Field(default_factory=list)
    api_base_url: str = "https://api.procore.com"
    login_url: str = "https://login.procore.com"
    client_id_env_var: str | None = "PROCORE_CLIENT_ID"
    client_secret_env_var: str | None = "PROCORE_CLIENT_SECRET"
    token_store_backend: Literal["file", "memory"] = "file"
    token_store_path: str | None = None
    notes: list[str] = Field(default_factory=list)
    created_for: str | None = None
    app_version_key_reference: str | None = None


class DmsaConnectionProfile(DmsaConnectionProfileInput):
    """Safe local DMSA metadata that references credentials by env-var name."""


class DmsaConnectionProfileValidationFinding(ProcoreModel):
    """One structural profile validation result."""

    level: FindingLevel
    code: str
    message: str
    recommended_review: str


class DmsaConnectionProfileValidationReport(ProcoreModel):
    """Structural validation results for one DMSA profile."""

    profile_name: str
    valid: bool
    findings: list[DmsaConnectionProfileValidationFinding] = Field(default_factory=list)


class DmsaPermissionChecklistItem(ProcoreModel):
    """One GC/Owner installation or permission checklist item."""

    item_id: str
    title: str
    description: str
    required: bool = True
    completed: bool = False


class DmsaPermissionChecklist(ProcoreModel):
    """GC/Owner-facing DMSA installation and access checklist."""

    title: str
    summary: str
    items: list[DmsaPermissionChecklistItem]


class DmsaInstallationPacket(ProcoreModel):
    """Plain-English DMSA installation packet for a GC/Owner."""

    title: str
    what_it_does: list[str]
    requested_access: list[str]
    what_it_does_not_do: list[str]
    installation_summary: list[str]
    permitted_projects: list[str]
    attachment_access: list[str]
    webhook_and_polling: list[str]
    security_statement: list[str]
    troubleshooting: dict[str, str]
    support_contact: str
    permission_checklist: DmsaPermissionChecklist


class DmsaSmokeCheckItem(ProcoreModel):
    """One intended read-only DMSA smoke check."""

    item_id: str
    title: str
    purpose: str
    expected_result: str
    requires_live_access: bool = True
    read_only: bool = True


class DmsaSmokeCheckPlan(ProcoreModel):
    """Plan describing explicit, user-run read-only DMSA checks."""

    profile_name: str
    selected_project_ids: list[int]
    live_execution_enabled: bool = False
    items: list[DmsaSmokeCheckItem]


class DmsaSmokeCheckResult(ProcoreModel):
    """Locally recorded result for one planned smoke check."""

    item_id: str
    outcome: Literal["not_run", "passed", "failed", "warning"] = "not_run"
    message: str
    status_code: int | None = None


class DmsaPermissionDiagnosticFinding(ProcoreModel):
    """One likely cause and recommended permission review."""

    code: str
    likely_cause: str
    recommended_review: str
    confidence: Literal["low", "medium"] = "medium"


class DmsaPermissionDiagnosticReport(ProcoreModel):
    """Local interpretation of a supplied status or response summary."""

    context: str
    status_code: int | None = None
    findings: list[DmsaPermissionDiagnosticFinding] = Field(default_factory=list)
    disclaimer: str = (
        "These are likely causes based on local metadata, not a live permission check."
    )


class DmsaConnectionSummary(ProcoreModel):
    """Redacted summary of a DMSA connection profile."""

    profile_name: str
    company_id: int | None
    allowed_project_ids: list[int]
    api_base_url: str
    login_url: str
    credential_references: dict[str, str | None]
    token_store_backend: str
    token_store_path: str | None
    created_for: str | None
    notes: list[str]
    safety_boundaries: list[str]
