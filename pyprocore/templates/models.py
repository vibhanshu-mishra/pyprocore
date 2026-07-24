"""Models for safe local PyProcore starter templates."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field

from pyprocore.models.base import ProcoreModel


class StarterTemplateFile(ProcoreModel):
    """One static file included in a local starter template."""

    path: str
    description: str
    content: str


class StarterTemplateMetadata(ProcoreModel):
    """Metadata describing a safe optional starter template."""

    name: str
    title: str
    summary: str
    category: str
    files: list[StarterTemplateFile] = Field(default_factory=list)
    safety_boundaries: list[str] = Field(default_factory=list)
    optional_dependencies: list[str] = Field(default_factory=list)
    read_only_routes: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    procore_api_call_required: bool = False
    external_ai_call_required: bool = False
    mcp_execution_enabled: bool = False
    procore_write_actions_enabled: bool = False


class TemplateCopyFinding(ProcoreModel):
    """One validation or copy finding for a starter template operation."""

    severity: str
    message: str
    path: str | None = None


class TemplateCopyFileResult(ProcoreModel):
    """One planned or copied template file."""

    source_template: str
    path: str
    exists: bool = False
    status: str = "planned"


class TemplateCopyResult(ProcoreModel):
    """Result for a starter template dry-run or copy operation."""

    template_name: str
    output_dir: Path
    dry_run: bool
    overwrite: bool
    files: list[TemplateCopyFileResult] = Field(default_factory=list)
    findings: list[TemplateCopyFinding] = Field(default_factory=list)
    planned_count: int = 0
    written_count: int = 0
    skipped_count: int = 0
    mode: str = "static_template_copy_only"
    procore_api_call_required: bool = False
    external_ai_call_required: bool = False
    mcp_execution_enabled: bool = False
    procore_write_actions_enabled: bool = False
