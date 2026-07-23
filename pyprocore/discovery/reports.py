"""Report rendering helpers for local discovery metadata."""

from __future__ import annotations

import json

from pyprocore.discovery.models import (
    DiscoveryBundle,
    DiscoveryCapability,
    DiscoveryReport,
    DiscoveryRouteResult,
)


def discovery_bundle_to_json(bundle: DiscoveryBundle, *, pretty: bool = False) -> str:
    """Serialize a discovery capability inventory to JSON."""
    return json.dumps(
        bundle.model_dump(mode="json"),
        indent=2 if pretty else None,
        sort_keys=pretty,
    )


def discovery_report_to_json(report: DiscoveryReport, *, pretty: bool = False) -> str:
    """Serialize a discovery safety and inventory report to JSON."""
    return json.dumps(
        report.model_dump(mode="json"),
        indent=2 if pretty else None,
        sort_keys=pretty,
    )


def discovery_route_result_to_json(
    result: DiscoveryRouteResult,
    *,
    pretty: bool = False,
) -> str:
    """Serialize route suggestions to JSON."""
    return json.dumps(
        result.model_dump(mode="json"),
        indent=2 if pretty else None,
        sort_keys=pretty,
    )


def discovery_capability_to_json(
    capability: DiscoveryCapability,
    *,
    pretty: bool = False,
) -> str:
    """Serialize one capability to JSON."""
    return json.dumps(
        capability.model_dump(mode="json"),
        indent=2 if pretty else None,
        sort_keys=pretty,
    )


def discovery_bundle_to_markdown(bundle: DiscoveryBundle) -> str:
    """Render a capability inventory as Markdown."""
    lines = [
        "# Discovery Capabilities",
        "",
        "This inventory is local metadata only. It does not call Procore, execute SDK "
        "functions, enable MCP execution, fetch remote catalogs, or enable write actions.",
        "",
        f"- Capabilities: {len(bundle.capabilities)}",
        "- Metadata only: true",
        "- Execution enabled: false",
        "- Procore API call required: false",
        "- Write enabled: false",
        "- MCP execution enabled: false",
        "- External AI required: false",
        "",
        "| Capability | Resource Family | Description |",
        "| --- | --- | --- |",
    ]
    for capability in bundle.capabilities:
        lines.append(
            f"| `{capability.name}` | {capability.resource_family} | {capability.description} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def discovery_capability_to_markdown(capability: DiscoveryCapability) -> str:
    """Render one capability as Markdown."""
    lines = [
        f"# {capability.title}",
        "",
        capability.description,
        "",
        f"- Name: `{capability.name}`",
        f"- Resource family: {capability.resource_family}",
        f"- Source: {capability.source}",
        "- Metadata only: true",
        "- Execution enabled: false",
        "- Procore API call required: false",
        "- Write enabled: false",
        "- MCP execution enabled: false",
        "- External AI required: false",
        "",
        "## Operations",
        "",
        *_bullets(capability.operations),
        "",
        "## Keywords",
        "",
        *_bullets(capability.keywords),
        "",
        "## Safety Labels",
        "",
        *_bullets(capability.safety_labels),
    ]
    return "\n".join(lines).rstrip() + "\n"


def discovery_route_result_to_markdown(result: DiscoveryRouteResult) -> str:
    """Render route suggestions as Markdown."""
    lines = [
        "# Discovery Route Suggestions",
        "",
        f"- Query: `{result.query.text}`",
        "- Mode: local discovery metadata only",
        "- Metadata only: true",
        "- Execution enabled: false",
        "- Procore API call required: false",
        "- Write enabled: false",
        "- MCP execution enabled: false",
        "- External AI required: false",
        "- Remote OAS fetch enabled: false",
        "",
        "| Score | Capability | Resource Family | Reasons |",
        "| ---: | --- | --- | --- |",
    ]
    if not result.candidates:
        lines.append("| 0 | No candidate matched. | - | Try a resource name such as `rfis`. |")
    for candidate in result.candidates:
        reasons = "; ".join(candidate.reasons) or "matched local metadata"
        lines.append(
            "| "
            + " | ".join(
                [
                    f"{candidate.score:.1f}",
                    f"`{candidate.capability.name}`",
                    candidate.capability.resource_family,
                    reasons,
                ]
            )
            + " |"
        )
    return "\n".join(lines).rstrip() + "\n"


def discovery_report_to_markdown(report: DiscoveryReport) -> str:
    """Render a discovery inventory and safety report as Markdown."""
    lines = [
        "# Discovery Metadata Safety Report",
        "",
        "This report describes local discovery metadata. It does not call Procore, "
        "execute SDK functions, enable MCP execution, call external AI/model APIs, "
        "fetch remote OAS files, or enable write actions.",
        "",
        f"- Capabilities: {report.capability_count}",
        "- Metadata only: true",
        "- Execution enabled: false",
        "- Procore API call required: false",
        "- Write enabled: false",
        "- MCP execution enabled: false",
        "- External AI required: false",
        "",
        "## Resource Families",
        "",
        *_bullets(report.resource_families),
        "",
        "## Safety Boundaries",
        "",
        *_bullets(report.safety_boundaries),
    ]
    return "\n".join(lines).rstrip() + "\n"


def _bullets(items: list[str]) -> list[str]:
    """Render strings as Markdown bullets."""
    if not items:
        return ["- None"]
    return [f"- {item}" for item in items]
