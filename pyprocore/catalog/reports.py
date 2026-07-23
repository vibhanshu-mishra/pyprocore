"""Report rendering helpers for local OAS endpoint catalogs."""

from __future__ import annotations

import json

from pyprocore.catalog.models import CatalogEndpoint, CatalogSummary, CoverageReport


def catalog_summary_to_json(summary: CatalogSummary, *, pretty: bool = False) -> str:
    """Serialize a catalog summary to JSON.

    Args:
        summary: Catalog summary to serialize.
        pretty: Whether to indent and sort the JSON output.

    Returns:
        JSON document as a string.
    """
    return json.dumps(
        summary.model_dump(mode="json"),
        indent=2 if pretty else None,
        sort_keys=pretty,
    )


def catalog_endpoints_to_json(
    endpoints: list[CatalogEndpoint],
    *,
    pretty: bool = False,
) -> str:
    """Serialize catalog endpoints to JSON.

    Args:
        endpoints: Endpoint metadata rows.
        pretty: Whether to indent and sort the JSON output.

    Returns:
        JSON document as a string.
    """
    payload = [endpoint.model_dump(mode="json") for endpoint in endpoints]
    return json.dumps(payload, indent=2 if pretty else None, sort_keys=pretty)


def coverage_report_to_json(report: CoverageReport, *, pretty: bool = False) -> str:
    """Serialize a coverage report to JSON.

    Args:
        report: Coverage report to serialize.
        pretty: Whether to indent and sort the JSON output.

    Returns:
        JSON document as a string.
    """
    return json.dumps(
        report.model_dump(mode="json"),
        indent=2 if pretty else None,
        sort_keys=pretty,
    )


def catalog_summary_to_markdown(summary: CatalogSummary) -> str:
    """Render a catalog summary as Markdown."""
    lines = [
        "# OAS Catalog Summary",
        "",
        f"- Source: `{summary.source_path or 'unknown'}`",
        f"- Title: {summary.title or 'Untitled catalog'}",
        f"- Version: {summary.version or 'unknown'}",
        f"- Endpoints: {summary.endpoint_count}",
        f"- Read-only candidates: {summary.read_only_count}",
        f"- Risky/write candidates: {summary.write_or_mutation_count}",
        f"- Unknown safety: {summary.unknown_count}",
        "- Mode: local OAS metadata only",
        "- Execution enabled: false",
        "- Remote OAS fetch enabled: false",
        "",
        "## Methods",
        "",
    ]
    lines.extend(_count_table(summary.method_counts, "Method"))
    lines.extend(["", "## Path Areas", ""])
    lines.extend(_count_table(summary.path_area_counts, "Area"))
    return "\n".join(lines).rstrip() + "\n"


def catalog_endpoints_to_markdown(endpoints: list[CatalogEndpoint]) -> str:
    """Render endpoint rows as Markdown."""
    lines = [
        "# OAS Catalog Endpoints",
        "",
        "| Method | Path | Area | Safety |",
        "| --- | --- | --- | --- |",
    ]
    for endpoint in endpoints:
        lines.append(
            "| "
            + " | ".join(
                [
                    endpoint.method,
                    f"`{endpoint.path}`",
                    endpoint.path_area,
                    endpoint.safety.value,
                ]
            )
            + " |"
        )
    if not endpoints:
        lines.append("| - | No endpoints matched. | - | - |")
    lines.extend(
        [
            "",
            "This command inspects local OAS metadata only. It does not call Procore, "
            "fetch remote OAS files, generate executable clients, or enable tool execution.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def coverage_report_to_markdown(report: CoverageReport) -> str:
    """Render a coverage report as Markdown."""
    lines = [
        "# OAS Coverage and Safety Report",
        "",
        "This report is metadata-only. It does not call Procore, fetch remote OAS "
        "files, generate executable clients, enable MCP execution, or enable "
        "Procore tool execution.",
        "",
        "## Summary",
        "",
        f"- Source: `{report.source_path or 'unknown'}`",
        f"- Endpoints: {report.summary.endpoint_count}",
        f"- Read-only candidates: {len(report.read_only_candidates)}",
        f"- Risky/write candidates: {len(report.risky_write_candidates)}",
        f"- Unknown candidates: {len(report.unknown_candidates)}",
        f"- Supported areas found: {len(report.already_supported_areas)}",
        f"- Unsupported areas found: {len(report.unsupported_areas)}",
        "",
        "## Supported Areas Found",
        "",
    ]
    lines.extend(_bullet_list(report.already_supported_areas))
    lines.extend(["", "## Unsupported Areas", ""])
    lines.extend(_bullet_list(report.unsupported_areas))
    lines.extend(["", "## Area Findings", ""])
    lines.extend(
        [
            "| Area | Supported | Endpoints | Read-only | Risky/write | Unknown |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for finding in report.findings:
        lines.append(
            "| "
            + " | ".join(
                [
                    finding.area,
                    "yes" if finding.supported else "no",
                    str(finding.endpoint_count),
                    str(finding.read_only_count),
                    str(finding.risky_count),
                    str(finding.unknown_count),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Read-only Candidates", ""])
    lines.extend(_endpoint_bullets(report.read_only_candidates))
    lines.extend(["", "## Risky/write Candidates", ""])
    lines.extend(_endpoint_bullets(report.risky_write_candidates))
    lines.extend(["", "## Unknown Candidates", ""])
    lines.extend(_endpoint_bullets(report.unknown_candidates))
    return "\n".join(lines).rstrip() + "\n"


def _count_table(counts: dict[str, int], label: str) -> list[str]:
    """Render count rows as a Markdown table."""
    lines = [f"| {label} | Count |", "| --- | ---: |"]
    if not counts:
        lines.append("| - | 0 |")
        return lines
    for key, count in counts.items():
        lines.append(f"| {key} | {count} |")
    return lines


def _bullet_list(items: list[str]) -> list[str]:
    """Render strings as Markdown bullets."""
    if not items:
        return ["- None"]
    return [f"- {item}" for item in items]


def _endpoint_bullets(endpoints: list[CatalogEndpoint]) -> list[str]:
    """Render endpoint bullets with reasons."""
    if not endpoints:
        return ["- None"]
    lines: list[str] = []
    for endpoint in endpoints:
        reasons = "; ".join(endpoint.safety_reasons) or "No reason recorded."
        lines.append(f"- `{endpoint.method} {endpoint.path}` ({endpoint.path_area}) - {reasons}")
    return lines
