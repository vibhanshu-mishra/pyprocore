"""Local scheduled export planning helpers.

This module validates enterprise scheduled export plan files and produces
dry-run manifests. It intentionally does not call Procore, read tokens, or run
export workflows.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import ConfigDict, Field

from pyprocore.core.exceptions import ValidationError
from pyprocore.models.base import ProcoreModel

ScheduledExportAuthMode = Literal["authorization_code", "client_credentials"]
ScheduledExportOutputFormat = Literal["csv", "jsonl"]
ValidationSeverity = Literal["error", "warning", "info"]

SUPPORTED_AUTH_MODES: tuple[str, ...] = ("authorization_code", "client_credentials")
SUPPORTED_OUTPUT_FORMATS: tuple[str, ...] = ("csv", "jsonl")

COMPANY_SCOPED_RESOURCES: tuple[str, ...] = (
    "companies",
    "projects",
    "company_users",
    "company_inactive_users",
    "vendors",
    "departments",
    "cost_codes",
    "cost_types",
    "tax_codes",
)

PROJECT_SCOPED_RESOURCES: tuple[str, ...] = (
    "rfis",
    "submittals",
    "documents",
    "drawings",
    "specifications",
    "photos",
    "daily_logs",
    "observations",
    "punch_items",
    "correspondences",
    "generic_tools",
    "meetings",
    "inspections",
    "incidents",
    "project_users",
    "project_vendors",
    "locations",
    "distribution_groups",
    "change_events",
    "prime_change_orders",
    "direct_costs",
    "budget_views",
    "budget_details",
    "commitments",
    "prime_contracts",
    "owner_invoices",
    "subcontractor_invoices",
    "schedule_resource_assignments",
    "tasks",
    "calendar_items",
    "coordination_issues",
    "forms",
    "form_templates",
    "action_plans",
)

SUPPORTED_RESOURCES: tuple[str, ...] = tuple(
    sorted({*COMPANY_SCOPED_RESOURCES, *PROJECT_SCOPED_RESOURCES})
)

SECRET_FIELD_PATTERN = re.compile(
    r"(access[_-]?token|refresh[_-]?token|client[_-]?secret|authorization|password|api[_-]?key)",
    flags=re.IGNORECASE,
)


class ScheduledExportPlan(ProcoreModel):
    """Local configuration for an enterprise scheduled export plan.

    Attributes:
        plan_name: Human-readable plan name.
        auth_mode: Authentication mode expected by the deployment.
        company_id: Procore company ID used for the export scope.
        project_ids: Project IDs to include for project-scoped resources.
        resources: Resource names to export.
        output_dir: Local output directory pattern.
        output_format: File format used by real export jobs.
        include_timestamp: Whether output paths should include a timestamp.
        dry_run: Whether the plan is intended to run in dry-run mode first.
        redaction_enabled: Whether downstream exports should redact sensitive text.
        max_projects: Optional safety limit for project-scoped export runs.
        notes: Optional operator notes.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, arbitrary_types_allowed=True)

    plan_name: str
    auth_mode: str = "client_credentials"
    company_id: int | None = None
    project_ids: list[int] = Field(default_factory=list)
    resources: list[str] = Field(default_factory=list)
    output_dir: Path = Path("./exports/scheduled")
    output_format: str = "csv"
    include_timestamp: bool = True
    dry_run: bool = True
    redaction_enabled: bool = True
    max_projects: int | None = None
    notes: str | None = None


class ScheduledExportFinding(ProcoreModel):
    """One validation or dry-run finding for a scheduled export plan."""

    severity: ValidationSeverity
    code: str
    message: str


class ScheduledExportValidationReport(ProcoreModel):
    """Validation result for a scheduled export plan."""

    plan_name: str
    is_valid: bool
    findings: list[ScheduledExportFinding] = Field(default_factory=list)

    @property
    def errors(self) -> list[ScheduledExportFinding]:
        """Return error findings."""
        return [finding for finding in self.findings if finding.severity == "error"]

    @property
    def warnings(self) -> list[ScheduledExportFinding]:
        """Return warning findings."""
        return [finding for finding in self.findings if finding.severity == "warning"]


class ScheduledExportFilePlan(ProcoreModel):
    """One local file that a real scheduled export run would write."""

    resource: str
    project_id: int | None = None
    output_path: Path
    output_format: str


class ScheduledExportManifest(ProcoreModel):
    """Dry-run manifest for a scheduled export plan."""

    plan_name: str
    generated_at: str
    dry_run: bool
    auth_mode: str
    company_id: int | None
    project_ids: list[int] = Field(default_factory=list)
    resources: list[str] = Field(default_factory=list)
    output_dir: Path
    output_format: str
    include_timestamp: bool
    redaction_enabled: bool
    max_projects: int | None = None
    files: list[ScheduledExportFilePlan] = Field(default_factory=list)
    findings: list[ScheduledExportFinding] = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)


def load_scheduled_export_plan(path: Path | str) -> ScheduledExportPlan:
    """Load a scheduled export plan from JSON.

    Args:
        path: Path to a JSON scheduled export plan.

    Returns:
        Parsed scheduled export plan.

    Raises:
        ValidationError: If the file is missing, invalid, or not a JSON object.
    """
    plan_path = Path(path)
    if plan_path.suffix.casefold() != ".json":
        raise ValidationError("Scheduled export plan files must use .json.")
    try:
        payload = json.loads(plan_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"Scheduled export plan file not found: {plan_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Scheduled export plan JSON is invalid: {exc.msg}") from exc
    except OSError as exc:
        raise ValidationError(f"Could not read scheduled export plan {plan_path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValidationError("Scheduled export plan must be a JSON object.")
    try:
        return ScheduledExportPlan.model_validate(payload)
    except ValueError as exc:
        raise ValidationError(f"Scheduled export plan is invalid: {exc}") from exc


def validate_scheduled_export_plan(
    plan: ScheduledExportPlan | Path | str,
) -> ScheduledExportValidationReport:
    """Validate a scheduled export plan without calling Procore.

    Args:
        plan: Plan object or path to a JSON plan file.

    Returns:
        Validation report with errors, warnings, and informational findings.
    """
    scheduled_plan = _coerce_plan(plan)
    findings: list[ScheduledExportFinding] = []

    _validate_no_secret_like_fields(scheduled_plan, findings)
    _validate_auth_mode(scheduled_plan, findings)
    _validate_output_format(scheduled_plan, findings)
    _validate_company_scope(scheduled_plan, findings)
    _validate_resource_scope(scheduled_plan, findings)
    _validate_output_dir(scheduled_plan, findings)
    _validate_project_limits(scheduled_plan, findings)
    _add_operational_guidance(scheduled_plan, findings)

    return ScheduledExportValidationReport(
        plan_name=scheduled_plan.plan_name,
        is_valid=not any(finding.severity == "error" for finding in findings),
        findings=findings,
    )


def export_plan_to_manifest(plan: ScheduledExportPlan | Path | str) -> ScheduledExportManifest:
    """Build a dry-run manifest for a scheduled export plan.

    Args:
        plan: Plan object or path to a JSON plan file.

    Returns:
        Dry-run manifest describing the local export plan.
    """
    scheduled_plan = _coerce_plan(plan)
    validation = validate_scheduled_export_plan(scheduled_plan)
    return ScheduledExportManifest(
        plan_name=scheduled_plan.plan_name,
        generated_at=datetime.now(tz=UTC).isoformat(),
        dry_run=True,
        auth_mode=scheduled_plan.auth_mode,
        company_id=scheduled_plan.company_id,
        project_ids=scheduled_plan.project_ids,
        resources=scheduled_plan.resources,
        output_dir=scheduled_plan.output_dir,
        output_format=scheduled_plan.output_format,
        include_timestamp=scheduled_plan.include_timestamp,
        redaction_enabled=scheduled_plan.redaction_enabled,
        max_projects=scheduled_plan.max_projects,
        files=_planned_files(scheduled_plan),
        findings=validation.findings,
        safety_notes=_safety_notes(scheduled_plan),
    )


def explain_scheduled_export_plan(plan: ScheduledExportPlan | Path | str) -> str:
    """Return a beginner-friendly dry-run explanation for a plan.

    Args:
        plan: Plan object or path to a JSON plan file.

    Returns:
        Human-readable plan explanation.
    """
    manifest = export_plan_to_manifest(plan)
    validation = ScheduledExportValidationReport(
        plan_name=manifest.plan_name,
        is_valid=not any(finding.severity == "error" for finding in manifest.findings),
        findings=manifest.findings,
    )
    lines = [
        "Scheduled export dry run.",
        f"Plan: {manifest.plan_name}",
        f"Valid: {validation.is_valid}",
        f"Auth mode: {manifest.auth_mode}",
        f"Company: {manifest.company_id or 'missing'}",
        f"Projects: {', '.join(str(project_id) for project_id in manifest.project_ids) or 'none'}",
        f"Resources: {', '.join(manifest.resources) or 'none'}",
        f"Output format: {manifest.output_format}",
        f"Output folder: {manifest.output_dir}",
        f"Planned files: {len(manifest.files)}",
        "",
        "Safety notes:",
    ]
    lines.extend(f"- {note}" for note in manifest.safety_notes)
    if manifest.findings:
        lines.append("")
        lines.append("Findings:")
        lines.extend(
            f"- {finding.severity.upper()}: {finding.message}" for finding in manifest.findings
        )
    return "\n".join(lines)


def write_scheduled_export_manifest(
    plan: ScheduledExportPlan | Path | str,
    output_path: Path | str,
) -> Path:
    """Write a dry-run manifest to disk.

    Args:
        plan: Plan object or path to a JSON plan file.
        output_path: Local JSON manifest path.

    Returns:
        Path written.
    """
    manifest = export_plan_to_manifest(plan)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(manifest.model_dump(mode="json"), indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    return destination


def sample_scheduled_export_plan(auth_mode: str = "client_credentials") -> ScheduledExportPlan:
    """Return a safe placeholder scheduled export plan.

    Args:
        auth_mode: Authentication mode for the sample.

    Returns:
        Sample plan containing placeholder IDs only.
    """
    return ScheduledExportPlan(
        plan_name=f"sample-{auth_mode}-scheduled-export",
        auth_mode=auth_mode,
        company_id=12345,
        project_ids=[67890],
        resources=["rfis", "submittals", "documents", "tasks"],
        output_dir=Path("./exports/scheduled/sample"),
        output_format="csv",
        include_timestamp=True,
        dry_run=True,
        redaction_enabled=True,
        max_projects=5,
        notes=(
            "Placeholder-only sample. Replace IDs after reviewing Procore app, "
            "company, project, and tool permissions."
        ),
    )


def sample_scheduled_export_plan_json(auth_mode: str = "client_credentials") -> str:
    """Return a safe placeholder scheduled export plan as pretty JSON."""
    sample = sample_scheduled_export_plan(auth_mode=auth_mode)
    return json.dumps(sample.model_dump(mode="json"), indent=2, default=str) + "\n"


def _coerce_plan(plan: ScheduledExportPlan | Path | str) -> ScheduledExportPlan:
    """Coerce a scheduled export plan input to a plan model."""
    if isinstance(plan, ScheduledExportPlan):
        return plan
    return load_scheduled_export_plan(plan)


def _validate_no_secret_like_fields(
    plan: ScheduledExportPlan,
    findings: list[ScheduledExportFinding],
) -> None:
    """Validate the plan does not carry secret-like extra fields."""
    dumped = plan.model_dump(mode="json")
    for key in dumped:
        if SECRET_FIELD_PATTERN.search(key):
            findings.append(
                ScheduledExportFinding(
                    severity="error",
                    code="secret_field",
                    message=(
                        f"Plan field '{key}' looks secret-like. Keep tokens and client "
                        "secrets in .env or a private token store, never in export plans."
                    ),
                )
            )


def _validate_auth_mode(
    plan: ScheduledExportPlan,
    findings: list[ScheduledExportFinding],
) -> None:
    """Validate auth mode."""
    if plan.auth_mode not in SUPPORTED_AUTH_MODES:
        findings.append(
            ScheduledExportFinding(
                severity="error",
                code="unknown_auth_mode",
                message=(
                    f"Unsupported auth_mode '{plan.auth_mode}'. Use authorization_code "
                    "or client_credentials."
                ),
            )
        )
        return
    if plan.auth_mode == "authorization_code":
        findings.append(
            ScheduledExportFinding(
                severity="warning",
                code="authorization_code_scheduled_export",
                message=(
                    "Authorization Code can work for user-owned local workflows, but "
                    "client_credentials is recommended for server-to-server scheduled exports."
                ),
            )
        )
    else:
        findings.append(
            ScheduledExportFinding(
                severity="info",
                code="client_credentials_recommended",
                message=(
                    "client_credentials is the recommended auth mode for enterprise "
                    "server-to-server scheduled exports."
                ),
            )
        )


def _validate_output_format(
    plan: ScheduledExportPlan,
    findings: list[ScheduledExportFinding],
) -> None:
    """Validate output format."""
    if plan.output_format not in SUPPORTED_OUTPUT_FORMATS:
        findings.append(
            ScheduledExportFinding(
                severity="error",
                code="unknown_output_format",
                message=f"Unsupported output_format '{plan.output_format}'. Use csv or jsonl.",
            )
        )


def _validate_company_scope(
    plan: ScheduledExportPlan,
    findings: list[ScheduledExportFinding],
) -> None:
    """Validate company scope."""
    if plan.company_id is None:
        findings.append(
            ScheduledExportFinding(
                severity="error",
                code="missing_company_id",
                message="company_id is required for scheduled export planning.",
            )
        )


def _validate_resource_scope(
    plan: ScheduledExportPlan,
    findings: list[ScheduledExportFinding],
) -> None:
    """Validate resources and project IDs."""
    if not plan.resources:
        findings.append(
            ScheduledExportFinding(
                severity="error",
                code="missing_resources",
                message="At least one supported resource is required.",
            )
        )
        return

    unknown = [resource for resource in plan.resources if resource not in SUPPORTED_RESOURCES]
    for resource in unknown:
        findings.append(
            ScheduledExportFinding(
                severity="error",
                code="unknown_resource",
                message=(
                    f"Unsupported resource '{resource}'. Supported resources include: "
                    f"{', '.join(SUPPORTED_RESOURCES)}."
                ),
            )
        )

    project_resources = [
        resource for resource in plan.resources if resource in PROJECT_SCOPED_RESOURCES
    ]
    if project_resources and not plan.project_ids:
        findings.append(
            ScheduledExportFinding(
                severity="error",
                code="missing_project_ids",
                message=(
                    "project_ids are required when exporting project-scoped resources: "
                    f"{', '.join(project_resources)}."
                ),
            )
        )


def _validate_output_dir(
    plan: ScheduledExportPlan,
    findings: list[ScheduledExportFinding],
) -> None:
    """Validate output directory looks local and safe."""
    output_text = str(plan.output_dir)
    if not output_text.strip():
        findings.append(
            ScheduledExportFinding(
                severity="error",
                code="missing_output_dir",
                message="output_dir is required.",
            )
        )
        return
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", output_text):
        findings.append(
            ScheduledExportFinding(
                severity="error",
                code="remote_output_dir",
                message="output_dir must be a local filesystem path, not a URL.",
            )
        )
    if ".." in plan.output_dir.parts:
        findings.append(
            ScheduledExportFinding(
                severity="warning",
                code="parent_directory_output",
                message=(
                    "output_dir contains '..'. Prefer an explicit private export folder "
                    "outside the repository."
                ),
            )
        )


def _validate_project_limits(
    plan: ScheduledExportPlan,
    findings: list[ScheduledExportFinding],
) -> None:
    """Validate project scope limits."""
    if plan.max_projects is not None and plan.max_projects <= 0:
        findings.append(
            ScheduledExportFinding(
                severity="error",
                code="invalid_max_projects",
                message="max_projects must be greater than zero when provided.",
            )
        )
    if plan.max_projects is not None and len(plan.project_ids) > plan.max_projects:
        findings.append(
            ScheduledExportFinding(
                severity="error",
                code="project_limit_exceeded",
                message=(
                    f"Plan includes {len(plan.project_ids)} projects, which exceeds "
                    f"max_projects={plan.max_projects}."
                ),
            )
        )
    if len(plan.project_ids) > 10 and plan.max_projects is None:
        findings.append(
            ScheduledExportFinding(
                severity="warning",
                code="broad_project_export",
                message=(
                    "This plan targets more than 10 projects without max_projects. "
                    "Review permissions, storage, and runtime before scheduling."
                ),
            )
        )


def _add_operational_guidance(
    plan: ScheduledExportPlan,
    findings: list[ScheduledExportFinding],
) -> None:
    """Add non-blocking operational guidance."""
    if not plan.dry_run:
        findings.append(
            ScheduledExportFinding(
                severity="warning",
                code="dry_run_disabled",
                message="Run and review a dry-run plan before scheduling real exports.",
            )
        )
    if not plan.redaction_enabled:
        findings.append(
            ScheduledExportFinding(
                severity="warning",
                code="redaction_disabled",
                message=(
                    "redaction_enabled is false. Review whether exported records may "
                    "contain private project data."
                ),
            )
        )


def _planned_files(plan: ScheduledExportPlan) -> list[ScheduledExportFilePlan]:
    """Return deterministic file plans for a dry-run manifest."""
    file_plans: list[ScheduledExportFilePlan] = []
    suffix = f".{plan.output_format}"
    timestamp = "{timestamp}" if plan.include_timestamp else None
    for resource in plan.resources:
        if resource in PROJECT_SCOPED_RESOURCES:
            for project_id in plan.project_ids:
                parts = [str(plan.output_dir), f"project-{project_id}", resource]
                if timestamp:
                    parts.append(timestamp)
                file_plans.append(
                    ScheduledExportFilePlan(
                        resource=resource,
                        project_id=project_id,
                        output_path=Path(*parts).with_suffix(suffix),
                        output_format=plan.output_format,
                    )
                )
        else:
            parts = [str(plan.output_dir), "company", resource]
            if timestamp:
                parts.append(timestamp)
            file_plans.append(
                ScheduledExportFilePlan(
                    resource=resource,
                    project_id=None,
                    output_path=Path(*parts).with_suffix(suffix),
                    output_format=plan.output_format,
                )
            )
    return file_plans


def _safety_notes(plan: ScheduledExportPlan) -> list[str]:
    """Return safety notes for operators reviewing a plan."""
    notes = [
        "Validation and dry-run planning are local-only and do not call Procore.",
        "Keep .env files, token stores, logs, downloads, and export output private.",
        "Review Data Connection App company, project, and tool permissions before scheduling.",
        "Run real exports only after reviewing this dry-run manifest.",
        "Tool execution remains disabled and MCP metadata remains discovery-only.",
    ]
    if plan.auth_mode == "client_credentials":
        notes.append(
            "Use a private service account or Data Connection App credential "
            "process for scheduled jobs."
        )
    else:
        notes.append(
            "Authorization Code workflows depend on a user-owned token store "
            "and may need refresh handling."
        )
    return notes


__all__ = [
    "COMPANY_SCOPED_RESOURCES",
    "PROJECT_SCOPED_RESOURCES",
    "SUPPORTED_AUTH_MODES",
    "SUPPORTED_OUTPUT_FORMATS",
    "SUPPORTED_RESOURCES",
    "ScheduledExportFilePlan",
    "ScheduledExportFinding",
    "ScheduledExportManifest",
    "ScheduledExportPlan",
    "ScheduledExportValidationReport",
    "explain_scheduled_export_plan",
    "export_plan_to_manifest",
    "load_scheduled_export_plan",
    "sample_scheduled_export_plan",
    "sample_scheduled_export_plan_json",
    "validate_scheduled_export_plan",
    "write_scheduled_export_manifest",
]
