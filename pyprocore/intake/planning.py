"""Configuration and planning helpers for local intake sync."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from pyprocore.core.exceptions import ValidationError
from pyprocore.intake.models import IntakeSyncConfig, IntakeSyncFinding, IntakeSyncPlan

EXPECTED_OUTPUT_FILES = [
    "intake_summary.json",
    "intake_summary.md",
    "rfis.jsonl",
    "rfis.csv",
    "submittals.jsonl",
    "submittals.csv",
    "attachments_manifest.json",
    "attachments_manifest.md",
    "state/intake_state.json",
    "output_manifest.json",
]


def build_intake_sync_config(**values: Any) -> IntakeSyncConfig:
    """Build typed intake configuration from local values."""
    return IntakeSyncConfig.model_validate(values)


def load_intake_sync_config(path: str | Path) -> IntakeSyncConfig:
    """Load intake configuration from a local JSON object."""
    source = _local_json_path(path)
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValidationError(f"Could not read intake config {source}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Intake config {source} is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValidationError("An intake config JSON document must contain an object.")
    try:
        return IntakeSyncConfig.model_validate(payload)
    except PydanticValidationError as exc:
        raise ValidationError(f"Invalid intake config {source}: {exc}") from exc


def validate_intake_sync_config(config: IntakeSyncConfig) -> list[IntakeSyncFinding]:
    """Validate local intake metadata without resolving credentials or calling Procore."""
    findings: list[IntakeSyncFinding] = []
    if not config.project_ids:
        findings.append(
            IntakeSyncFinding(
                level="error",
                code="missing_project_ids",
                message="At least one permitted project ID is required.",
            )
        )
    if any(project_id <= 0 for project_id in config.project_ids):
        findings.append(
            IntakeSyncFinding(
                level="error",
                code="invalid_project_id",
                message="Project IDs must be positive integers.",
            )
        )
    if not config.include_rfis and not config.include_submittals:
        findings.append(
            IntakeSyncFinding(
                level="error",
                code="no_resources_selected",
                message="Select RFIs, Submittals, or both.",
            )
        )
    if config.max_items_per_project is not None and config.max_items_per_project <= 0:
        findings.append(
            IntakeSyncFinding(
                level="error",
                code="invalid_max_items",
                message="max_items_per_project must be a positive integer.",
            )
        )
    if not config.profile_path and not config.profile_name:
        findings.append(
            IntakeSyncFinding(
                level="warning",
                code="profile_not_documented",
                message="No DMSA profile reference is documented in this config.",
            )
        )
    return findings


def build_intake_sync_plan(config: IntakeSyncConfig) -> IntakeSyncPlan:
    """Build a non-executing intake plan without credentials or file writes."""
    resources = []
    if config.include_rfis:
        resources.append("rfis")
    if config.include_submittals:
        resources.append("submittals")
    state_path = config.state_path or str(Path(config.output_dir) / "state/intake_state.json")
    return IntakeSyncPlan(
        profile_reference=config.profile_path or config.profile_name,
        company_id=config.company_id,
        project_ids=config.project_ids,
        resources=resources,
        output_dir=config.output_dir,
        state_path=state_path,
        output_files=_plan_output_files(config),
        updated_since=config.updated_since,
        max_items_per_project=config.max_items_per_project,
        include_attachments=config.include_attachments,
        dry_run=config.dry_run,
        findings=validate_intake_sync_config(config),
        safety_boundaries=[
            "GC/Owner controls DMSA installation, permitted projects, and permissions.",
            "Plan generation does not call Procore or require credentials.",
            "All writes are local output files; no Procore write actions are enabled.",
            "Attachment manifests do not download remote files.",
        ],
    )


def summarize_intake_sync_plan(plan: IntakeSyncPlan) -> str:
    """Render a concise Markdown plan summary."""
    lines = [
        "# RFI/Submittal Intake Sync Plan",
        "",
        f"- Projects: {', '.join(str(value) for value in plan.project_ids) or 'None'}",
        f"- Resources: {', '.join(plan.resources) or 'None'}",
        f"- Output directory: `{plan.output_dir}`",
        f"- State path: `{plan.state_path}`",
        f"- Dry-run: {str(plan.dry_run).lower()}",
        f"- Attachment manifest: {str(plan.include_attachments).lower()}",
        "",
        "## Planned Local Files",
        *[f"- `{path}`" for path in plan.output_files],
        "",
        "## Safety Boundaries",
        *[f"- {value}" for value in plan.safety_boundaries],
    ]
    if plan.findings:
        lines.extend(["", "## Findings"])
        lines.extend(
            f"- **{finding.level}: {finding.code}** - {finding.message}"
            for finding in plan.findings
        )
    return "\n".join(lines) + "\n"


def write_intake_sync_config_template(
    path: str | Path,
    *,
    overwrite: bool = False,
) -> Path:
    """Write a secret-free local intake configuration template."""
    destination = _safe_json_destination(path)
    if destination.exists() and not overwrite:
        raise ValidationError(
            f"Refusing to overwrite existing intake config: {destination}. "
            "Pass overwrite=True explicitly."
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    config = IntakeSyncConfig(
        profile_path="./examples/dmsa/dmsa_connection_profile.json",
        profile_name="gc-owner-read-only",
        company_id=None,
        project_ids=[],
        output_dir="./exports/intake",
        state_path="./exports/intake/state/intake_state.json",
        dry_run=True,
        notes=["Replace metadata placeholders with GC/Owner-approved project IDs."],
    )
    destination.write_text(
        json.dumps(config.model_dump(mode="json"), indent=2) + "\n",
        encoding="utf-8",
    )
    return destination


def _plan_output_files(config: IntakeSyncConfig) -> list[str]:
    files = list(EXPECTED_OUTPUT_FILES)
    for project_id in config.project_ids:
        if config.include_rfis:
            files.append(f"raw/rfis_{project_id}.json")
        if config.include_submittals:
            files.append(f"raw/submittals_{project_id}.json")
    if not config.include_attachments:
        files = [path for path in files if not path.startswith("attachments_manifest")]
    if not config.include_rfis:
        files = [path for path in files if not path.startswith("rfis.")]
    if not config.include_submittals:
        files = [path for path in files if not path.startswith("submittals.")]
    return files


def _local_json_path(path: str | Path) -> Path:
    source = Path(path).expanduser()
    if source.suffix.casefold() != ".json":
        raise ValidationError("Intake configuration and state files must be JSON.")
    return source


def _safe_json_destination(path: str | Path) -> Path:
    candidate = Path(path).expanduser()
    if ".." in candidate.parts:
        raise ValidationError("Path traversal is not allowed for intake files.")
    if candidate.suffix.casefold() != ".json":
        raise ValidationError("Intake configuration and state files must be JSON.")
    return candidate.resolve()
