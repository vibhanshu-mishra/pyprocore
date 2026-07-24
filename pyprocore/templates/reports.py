"""Report renderers for optional starter templates."""

from __future__ import annotations

import json
from typing import Any

from pyprocore.templates.models import StarterTemplateMetadata, TemplateCopyResult


def template_metadata_to_json(template: StarterTemplateMetadata, *, pretty: bool = False) -> str:
    """Render starter template metadata as JSON text."""
    return json.dumps(template.model_dump(mode="json"), indent=2 if pretty else None)


def templates_to_json(templates: list[StarterTemplateMetadata], *, pretty: bool = False) -> str:
    """Render starter template inventory as JSON text."""
    payload = [template.model_dump(mode="json") for template in templates]
    return json.dumps(payload, indent=2 if pretty else None)


def template_metadata_to_markdown(template: StarterTemplateMetadata) -> str:
    """Render starter template metadata as Markdown."""
    lines = [
        f"# {template.title}",
        "",
        template.summary,
        "",
        "## Safety Boundaries",
        "",
    ]
    lines.extend(f"- {item}" for item in template.safety_boundaries)
    lines.extend(["", "## Read-Only Routes", ""])
    lines.extend(f"- `{route}`" for route in template.read_only_routes)
    lines.extend(["", "## Files", ""])
    lines.extend(f"- `{file.path}`: {file.description}" for file in template.files)
    lines.extend(
        [
            "",
            "## Runtime Flags",
            "",
            f"- Procore API call required: {str(template.procore_api_call_required).lower()}",
            f"- External AI/model call required: {str(template.external_ai_call_required).lower()}",
            f"- MCP execution enabled: {str(template.mcp_execution_enabled).lower()}",
            (
                "- Procore write actions enabled: "
                f"{str(template.procore_write_actions_enabled).lower()}"
            ),
            "",
        ]
    )
    return "\n".join(lines)


def templates_to_markdown(templates: list[StarterTemplateMetadata]) -> str:
    """Render starter template inventory as Markdown."""
    lines = ["# PyProcore Starter Templates", ""]
    for template in templates:
        lines.extend(
            [
                f"## {template.name}",
                "",
                template.summary,
                "",
                f"- Category: `{template.category}`",
                f"- Files: {len(template.files)}",
                f"- Read-only routes: {len(template.read_only_routes)}",
                "- Copy only; no install, execution, Procore calls, or remote fetching.",
                "",
            ]
        )
    return "\n".join(lines)


def template_copy_result_to_json(result: TemplateCopyResult, *, pretty: bool = False) -> str:
    """Render template copy result as JSON text."""
    return json.dumps(result.model_dump(mode="json"), indent=2 if pretty else None, default=str)


def template_copy_result_to_markdown(result: TemplateCopyResult) -> str:
    """Render template copy result as Markdown."""
    lines = [
        f"# Template Copy Result: {result.template_name}",
        "",
        f"- Output directory: `{result.output_dir}`",
        f"- Dry run: {str(result.dry_run).lower()}",
        f"- Overwrite: {str(result.overwrite).lower()}",
        f"- Planned files: {result.planned_count}",
        f"- Written files: {result.written_count}",
        f"- Skipped files: {result.skipped_count}",
        f"- Procore API calls required: {str(result.procore_api_call_required).lower()}",
        f"- External AI/model calls required: {str(result.external_ai_call_required).lower()}",
        f"- MCP execution enabled: {str(result.mcp_execution_enabled).lower()}",
        f"- Procore write actions enabled: {str(result.procore_write_actions_enabled).lower()}",
        "",
    ]
    if result.findings:
        lines.extend(["## Findings", ""])
        lines.extend(
            f"- {finding.severity.upper()}: {finding.message}"
            + (f" (`{finding.path}`)" if finding.path else "")
            for finding in result.findings
        )
        lines.append("")
    lines.extend(["## Files", ""])
    lines.extend(f"- `{file.path}`: {file.status}" for file in result.files)
    lines.append("")
    return "\n".join(lines)


def template_to_summary_dict(template: StarterTemplateMetadata) -> dict[str, Any]:
    """Return compact JSON-compatible starter template metadata."""
    return {
        "name": template.name,
        "title": template.title,
        "category": template.category,
        "file_count": len(template.files),
        "read_only_routes": list(template.read_only_routes),
        "safety_boundaries": list(template.safety_boundaries),
    }
