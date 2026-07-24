"""JSON and Markdown reports for local codebase usage and impact scans."""

from __future__ import annotations

import json
from collections.abc import Sequence

from pyprocore.maintenance.models import ApiImpactReport, CodebaseScanReport, PyprocoreUsage


def codebase_scan_report_to_json(
    report: CodebaseScanReport,
    *,
    pretty: bool = False,
) -> str:
    """Serialize a local codebase usage scan report to JSON."""
    return json.dumps(
        report.model_dump(mode="json"),
        indent=2 if pretty else None,
        sort_keys=pretty,
    )


def api_impact_report_to_json(report: ApiImpactReport, *, pretty: bool = False) -> str:
    """Serialize a local API impact report to JSON."""
    return json.dumps(
        report.model_dump(mode="json"),
        indent=2 if pretty else None,
        sort_keys=pretty,
    )


def codebase_scan_report_to_markdown(report: CodebaseScanReport) -> str:
    """Render a local customer-codebase usage report as Markdown."""
    lines = [
        "# PyProcore Local Usage Scan",
        "",
        _SAFETY_NOTE,
        "",
        "## Summary",
        "",
        f"- Scanned path: `{report.scanned_path}`",
        f"- Files scanned: {len(report.files_scanned)}",
        f"- Files skipped: {len(report.files_skipped)}",
        f"- Imports found: {len(report.imports)}",
        f"- Calls found: {len(report.calls)}",
        f"- CLI usages found: {len(report.cli_usages)}",
        f"- Total usage rows: {len(report.usages)}",
        "",
        "## Capability Map",
        "",
        "| Capability | Usages |",
        "| --- | ---: |",
    ]
    lines.extend(
        [f"| {family} | {count} |" for family, count in report.capability_counts.items()]
        or ["| None | 0 |"]
    )
    lines.extend(["", "## Imports", ""])
    lines.extend(_usage_bullets(report.imports))
    lines.extend(["", "## Object And Helper Calls", ""])
    lines.extend(_usage_bullets(report.calls))
    lines.extend(["", "## CLI Usage", ""])
    lines.extend(_usage_bullets(report.cli_usages))
    lines.extend(["", "## Skipped Files", ""])
    lines.extend(
        [f"- `{item.path}` - {item.reason or 'skipped'}" for item in report.files_skipped]
        or ["- None"]
    )
    lines.extend(["", "Human review is required. No files were modified."])
    return "\n".join(lines).rstrip() + "\n"


def api_impact_report_to_markdown(report: ApiImpactReport) -> str:
    """Render a local codebase API impact report as Markdown."""
    lines = [
        "# PyProcore Local API Impact Report",
        "",
        _SAFETY_NOTE,
        "",
        "## Summary",
        "",
        f"- Scanned path: `{report.scanned_path}`",
        f"- OAS comparison provided: {'yes' if report.oas_comparison_provided else 'no'}",
        f"- Usage rows: {len(report.scan_report.usages)}",
        f"- Impact findings: {len(report.findings)}",
        "",
        "## Possible Impact",
        "",
        "| Classification | Capability | Related paths |",
        "| --- | --- | ---: |",
    ]
    lines.extend(
        [
            f"| {finding.classification} | {finding.capability_family} | "
            f"{len(finding.changed_endpoint_paths)} |"
            for finding in report.findings
        ]
        or ["| unknown | None | 0 |"]
    )
    for classification in [
        "likely_affected",
        "deprecated_or_risky_usage",
        "possibly_affected",
        "unknown",
        "not_affected",
    ]:
        lines.extend(["", f"## {classification.replace('_', ' ').title()}", ""])
        matching = [
            finding for finding in report.findings if finding.classification == classification
        ]
        lines.extend(
            [f"- **{finding.capability_family}**: {finding.message}" for finding in matching]
            or ["- None"]
        )
    lines.extend(["", "## Suggested Manual Review Actions", ""])
    lines.extend(
        [
            f"- **{item.capability_family}** ({item.priority}): {item.action}"
            for item in report.migration_suggestions
        ]
        or ["- None"]
    )
    lines.extend(["", *[f"- {note}" for note in report.notes]])
    lines.extend(["", "Human review is required. No customer files were modified."])
    return "\n".join(lines).rstrip() + "\n"


def _usage_bullets(usages: Sequence[PyprocoreUsage]) -> list[str]:
    """Render usage rows without exposing unredacted source text."""
    if not usages:
        return ["- None"]
    return [
        f"- `{usage.file_path}:{usage.line_number or '?'}` "
        f"`{usage.symbol}` ({usage.capability_family}, {usage.confidence})"
        for usage in usages
    ]


_SAFETY_NOTE = (
    "Local scan only. No files are modified or executed; no remote repository or "
    "OAS access, Procore calls, AI/model calls, automatic commits, pull requests, "
    "tool execution, or write actions are enabled."
)
