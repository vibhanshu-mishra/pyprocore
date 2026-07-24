"""JSON and Markdown reports for local API compatibility contracts."""

from __future__ import annotations

import json

from pyprocore.maintenance.models import (
    ApiCompatibilityContract,
    ApiCompatibilityDiffReport,
    ApiCompatibilityValidationReport,
    CodebaseCompatibilityReport,
)

_SAFETY_NOTE = (
    "Local compatibility metadata only. No Procore call, remote fetch, code edit, "
    "patch application, git operation, GitHub API call, pull-request creation, "
    "MCP/tool execution, or external AI/model call is performed. This is not a "
    "production compatibility certification. Human review is required."
)


def compatibility_contract_to_json(
    contract: ApiCompatibilityContract,
    *,
    pretty: bool = False,
) -> str:
    """Serialize a compatibility contract to stable JSON."""
    return json.dumps(
        contract.model_dump(mode="json"),
        indent=2 if pretty else None,
        sort_keys=True,
    )


def compatibility_contract_to_markdown(contract: ApiCompatibilityContract) -> str:
    """Render a compatibility contract for maintainers."""
    lines = [
        "# PyProcore API Compatibility Contract",
        "",
        _SAFETY_NOTE,
        "",
        f"- PyProcore version: `{contract.pyprocore_version}`",
        f"- Contract schema: `{contract.contract_schema_version}`",
        f"- Generated at: `{contract.generated_at or 'not specified'}`",
        f"- Resource families: {len(contract.resources)}",
        f"- Read-only service areas: {len(contract.supported_read_only_service_areas)}",
        "",
        "## Resource Families",
        "",
        *[
            f"- `{resource.name}` ({resource.category}, "
            f"{'local-only' if resource.local_only else 'read-only'})"
            for resource in contract.resources
        ],
        "",
        "## CLI Groups",
        "",
        *[f"- `{group}`" for group in contract.supported_cli_groups],
        "",
        "## Safety Boundaries",
        "",
        *[
            f"- **{boundary.name}**: `{boundary.status}` - {boundary.description}"
            for boundary in contract.safety_boundaries
        ],
        "",
        "## Known Gaps",
        "",
        *(
            [f"- `{gap.family}`: {gap.status} - {gap.reason}" for gap in contract.known_gaps]
            or ["- None"]
        ),
    ]
    return "\n".join(lines).rstrip() + "\n"


def compatibility_validation_report_to_json(
    report: ApiCompatibilityValidationReport,
    *,
    pretty: bool = False,
) -> str:
    """Serialize a contract validation report."""
    return _model_to_json(report, pretty=pretty)


def compatibility_validation_report_to_markdown(
    report: ApiCompatibilityValidationReport,
) -> str:
    """Render contract validation findings as Markdown."""
    lines = [
        "# Compatibility Contract Validation",
        "",
        _SAFETY_NOTE,
        "",
        f"- Valid: {'yes' if report.valid else 'no'}",
        f"- Findings: {len(report.findings)}",
        "",
        "## Findings",
        "",
        *(
            [
                f"- **{finding.severity} / {finding.code}**: {finding.message}"
                for finding in report.findings
            ]
            or ["- None"]
        ),
    ]
    return "\n".join(lines).rstrip() + "\n"


def compatibility_diff_report_to_json(
    report: ApiCompatibilityDiffReport,
    *,
    pretty: bool = False,
) -> str:
    """Serialize a local compatibility diff report."""
    return _model_to_json(report, pretty=pretty)


def compatibility_diff_report_to_markdown(report: ApiCompatibilityDiffReport) -> str:
    """Render local compatibility contract differences."""
    lines = [
        "# API Compatibility Contract Diff",
        "",
        _SAFETY_NOTE,
        "",
        f"- Old contract: `{report.old_contract_path}`",
        f"- New contract: `{report.new_contract_path}`",
        f"- Overall risk: **{report.risk_level}**",
    ]
    for heading, values in [
        ("Added Resource Families", report.added_resource_families),
        ("Removed Resource Families", report.removed_resource_families),
        ("Added CLI Groups", report.added_cli_groups),
        ("Removed CLI Groups", report.removed_cli_groups),
    ]:
        lines.extend(["", f"## {heading}", ""])
        lines.extend([f"- `{value}`" for value in values] or ["- None"])
    lines.extend(["", "## Changes Requiring Review", ""])
    lines.extend(
        [
            f"- **{change.risk_level} / {change.change_type}** "
            f"`{change.subject}`: {change.migration_note}"
            for change in [
                *report.changed_safety_boundaries,
                *report.changed_known_gaps,
            ]
        ]
        or ["- None"]
    )
    return "\n".join(lines).rstrip() + "\n"


def codebase_compatibility_report_to_json(
    report: CodebaseCompatibilityReport,
    *,
    pretty: bool = False,
) -> str:
    """Serialize a local codebase compatibility report."""
    return _model_to_json(report, pretty=pretty)


def codebase_compatibility_report_to_markdown(
    report: CodebaseCompatibilityReport,
) -> str:
    """Render local codebase usage compared with a compatibility contract."""
    lines = [
        "# Codebase Compatibility Scan",
        "",
        _SAFETY_NOTE,
        "",
        f"- Scanned path: `{report.scanned_path}`",
        f"- Contract path: `{report.contract_path}`",
        f"- Contract version: `{report.contract_version}`",
    ]
    for heading, values in [
        ("Compatible", report.compatible),
        ("Local-only Compatible", report.local_only),
        ("Deprecated", report.deprecated),
        ("Removed / High Risk", report.removed),
        ("Unknown / Manual Review", report.unknown_manual_review),
    ]:
        lines.extend(["", f"## {heading}", ""])
        lines.extend(
            [
                f"- `{item.file_path}:{item.symbol}` ({item.family}) - {item.message}"
                + (f" Migration: {item.migration_note}" if item.migration_note else "")
                for item in values
            ]
            or ["- None"]
        )
    return "\n".join(lines).rstrip() + "\n"


def _model_to_json(
    model: (
        ApiCompatibilityValidationReport | ApiCompatibilityDiffReport | CodebaseCompatibilityReport
    ),
    *,
    pretty: bool,
) -> str:
    """Serialize one compatibility report deterministically."""
    return json.dumps(
        model.model_dump(mode="json"),
        indent=2 if pretty else None,
        sort_keys=True,
    )
