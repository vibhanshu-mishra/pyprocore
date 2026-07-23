"""Report renderers for local integration blueprints."""

from __future__ import annotations

import json
from typing import Any

from pyprocore.integrations.models import (
    IntegrationBlueprint,
    IntegrationReadinessReport,
)


def integration_blueprints_to_json(
    blueprints: list[IntegrationBlueprint],
    *,
    pretty: bool = False,
) -> str:
    """Serialize blueprint inventory to JSON."""
    payload = [blueprint.model_dump(mode="json") for blueprint in blueprints]
    return json.dumps(payload, indent=2 if pretty else None, sort_keys=pretty)


def integration_blueprint_to_json(
    blueprint: IntegrationBlueprint,
    *,
    pretty: bool = False,
) -> str:
    """Serialize one blueprint to JSON."""
    return json.dumps(
        blueprint.model_dump(mode="json"),
        indent=2 if pretty else None,
        sort_keys=pretty,
    )


def integration_readiness_report_to_json(
    report: IntegrationReadinessReport,
    *,
    pretty: bool = False,
) -> str:
    """Serialize a readiness report to JSON."""
    return json.dumps(
        report.model_dump(mode="json"),
        indent=2 if pretty else None,
        sort_keys=pretty,
    )


def sync_run_summary_to_json(summary: dict[str, Any], *, pretty: bool = False) -> str:
    """Serialize a local sync run summary to JSON."""
    return json.dumps(summary, indent=2 if pretty else None, sort_keys=pretty)


def integration_blueprints_to_markdown(blueprints: list[IntegrationBlueprint]) -> str:
    """Render blueprint inventory as Markdown."""
    lines = [
        "# Integration Blueprints",
        "",
        "These blueprints are local templates and guidance only. PyProcore does not "
        "host infrastructure, schedule jobs automatically, store secrets in a database, "
        "call Procore, or enable write actions from this layer.",
        "",
        "| Blueprint | Intended Use |",
        "| --- | --- |",
    ]
    for blueprint in blueprints:
        lines.append(f"| `{blueprint.name}` | {blueprint.intended_use} |")
    return "\n".join(lines).rstrip() + "\n"


def integration_blueprint_to_markdown(blueprint: IntegrationBlueprint) -> str:
    """Render one integration blueprint as Markdown."""
    lines = [
        f"# {blueprint.title}",
        "",
        blueprint.description,
        "",
        f"- Name: `{blueprint.name}`",
        f"- Intended use: {blueprint.intended_use}",
        "- Metadata only: true",
        "- Execution enabled: false",
        "- Procore API call required: false",
        "- Write enabled: false",
        "- Hosted app included: false",
        "- Database dependency required: false",
        "- Automatic scheduler enabled: false",
        "",
        "## Required Environment Variables",
        "",
        *_credential_bullets(blueprint),
        "",
        "## Required PyProcore Capabilities",
        "",
        *_bullets(blueprint.required_pyprocore_capabilities),
        "",
        "## Local Output Files",
        "",
        *_bullets(blueprint.local_output_files),
        "",
        "## Safety Boundaries",
        "",
        *_bullets(blueprint.safety_boundaries),
        "",
        "## Deployment Notes",
        "",
        *_bullets(blueprint.suggested_deployment_notes),
        "",
        "## Test Strategy",
        "",
        *_bullets(blueprint.test_strategy),
        "",
        "## Example Commands",
        "",
        *_bullets(blueprint.example_commands),
        "",
        "## Pseudocode",
        "",
        *_bullets(blueprint.pseudocode),
    ]
    return "\n".join(lines).rstrip() + "\n"


def integration_readiness_report_to_markdown(report: IntegrationReadinessReport) -> str:
    """Render a local readiness report as Markdown."""
    lines = [
        "# Integration Readiness Report",
        "",
        f"- Blueprint: `{report.blueprint_name}`",
        f"- Output dir: `{report.output_dir}`",
        f"- Ready: {str(report.ready).lower()}",
        f"- Findings: {report.finding_count}",
        "- Mode: local integration blueprint metadata only",
        "- Procore API call required: false",
        "- Write enabled: false",
        "- Hosted app included: false",
        "- Database dependency required: false",
        "- Automatic scheduler enabled: false",
        "",
        "| Severity | Code | Message | Suggested Action |",
        "| --- | --- | --- | --- |",
    ]
    for finding in report.findings:
        lines.append(
            "| "
            + " | ".join(
                [
                    finding.severity.value,
                    finding.code,
                    finding.message,
                    finding.suggested_action or "-",
                ]
            )
            + " |"
        )
    if not report.findings:
        lines.append("| info | no_findings | No findings. | - |")
    return "\n".join(lines).rstrip() + "\n"


def sync_run_summary_to_markdown(summary: dict[str, Any]) -> str:
    """Render a local sync run summary as Markdown."""
    status_counts = summary.get("status_counts", {})
    lines = [
        "# Local Sync Run Summary",
        "",
        f"- Path: `{summary.get('path', 'unknown')}`",
        f"- Runs: {summary.get('run_count', 0)}",
        "- Mode: local sync run files only",
        "- Procore API call required: false",
        "- Write enabled: false",
        "",
        "| Status | Count |",
        "| --- | ---: |",
    ]
    if isinstance(status_counts, dict) and status_counts:
        for status, count in sorted(status_counts.items()):
            lines.append(f"| {status} | {count} |")
    else:
        lines.append("| none | 0 |")
    return "\n".join(lines).rstrip() + "\n"


def _credential_bullets(blueprint: IntegrationBlueprint) -> list[str]:
    return [
        f"- `{item.name}`: {item.description}"
        + (" Secret; do not print or commit." if item.secret else "")
        for item in blueprint.required_environment_variables
    ]


def _bullets(items: list[str]) -> list[str]:
    if not items:
        return ["- None"]
    return [f"- {item}" for item in items]
