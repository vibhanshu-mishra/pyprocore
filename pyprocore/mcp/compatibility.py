"""Compatibility reports for PyProcore discovery-only MCP metadata."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import Field

from pyprocore.mcp.contracts import build_mcp_contract_report
from pyprocore.mcp.snapshots import _resolve_safe_output_path
from pyprocore.models.base import ProcoreModel

COMPATIBILITY_SCHEMA_VERSION = "mcp-compatibility-v1"


def _package_version() -> str:
    from pyprocore import __version__

    return __version__


class McpCompatibilityStatus(str, Enum):
    """Overall MCP compatibility status values."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class McpCompatibilityReport(ProcoreModel):
    """Integrator-facing report for the discovery-only MCP adapter."""

    schema_version: str = COMPATIBILITY_SCHEMA_VERSION
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    server_name: str
    package_version: str = Field(default_factory=_package_version)
    status: McpCompatibilityStatus
    discovery_only: bool = True
    resource_count_by_kind: dict[str, int] = Field(default_factory=dict)
    prompt_count_by_kind: dict[str, int] = Field(default_factory=dict)
    supported_metadata_areas: list[str] = Field(default_factory=list)
    unsupported_actions: list[str] = Field(default_factory=list)
    safety_boundaries: list[str] = Field(default_factory=list)
    contract_validation: dict[str, Any] = Field(default_factory=dict)
    sample_requests: list[dict[str, Any]] = Field(default_factory=list)
    sample_responses: list[dict[str, Any]] = Field(default_factory=list)
    integrator_notes: list[str] = Field(default_factory=list)


def build_mcp_compatibility_report(
    manifest: dict[str, Any] | None = None,
) -> McpCompatibilityReport:
    """Build a local MCP compatibility report without any remote calls."""
    if manifest is None:
        from pyprocore.mcp.discovery import build_mcp_discovery_manifest

        document = build_mcp_discovery_manifest().model_dump(mode="json", by_alias=True)
    else:
        document = dict(manifest)

    capabilities = document["capabilities"]
    resource_counts = Counter(item["kind"] for item in document["resources"])
    prompt_counts = Counter(item["kind"] for item in document["prompts"])
    contract_report = build_mcp_contract_report(document)
    status = (
        McpCompatibilityStatus.PASS if contract_report["passed"] else McpCompatibilityStatus.FAIL
    )
    return McpCompatibilityReport(
        server_name=document["server"]["name"],
        status=status,
        resource_count_by_kind=dict(sorted(resource_counts.items())),
        prompt_count_by_kind=dict(sorted(prompt_counts.items())),
        supported_metadata_areas=list(capabilities.get("supported_sdk_areas", [])),
        unsupported_actions=list(capabilities.get("unsupported_actions", [])),
        safety_boundaries=list(capabilities.get("safety_boundaries", [])),
        contract_validation=contract_report,
        sample_requests=[
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "resources/list", "params": {}},
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "procore.example", "arguments": {}},
            },
        ],
        sample_responses=[
            {"jsonrpc": "2.0", "id": 1, "result": {"serverInfo": document["server"]}},
            {
                "jsonrpc": "2.0",
                "id": 3,
                "result": {
                    "isError": True,
                    "metadata": {
                        "execution_enabled": False,
                        "discovery_only": True,
                    },
                },
            },
        ],
        integrator_notes=[
            "This MCP surface is for metadata discovery only.",
            "MCP clients can list tools, resources, prompts, and capability summaries.",
            "Tool calls return a disabled response and do not contact Procore.",
            "Static fixtures are safe for local client compatibility tests.",
        ],
    )


def mcp_compatibility_report_to_json(
    report: McpCompatibilityReport | dict[str, Any] | None = None,
    *,
    pretty: bool = False,
) -> str:
    """Serialize an MCP compatibility report as deterministic JSON."""
    document = _report_dict(report or build_mcp_compatibility_report())
    return json.dumps(document, indent=2 if pretty else None, sort_keys=True)


def mcp_compatibility_report_to_markdown(
    report: McpCompatibilityReport | dict[str, Any] | None = None,
) -> str:
    """Render an MCP compatibility report as Markdown."""
    document = _report_dict(report or build_mcp_compatibility_report())
    lines = [
        "# PyProcore MCP Compatibility Report",
        "",
        f"- Schema: `{document['schema_version']}`",
        f"- Server: `{document['server_name']}`",
        f"- Package: `{document['package_version']}`",
        f"- Status: `{document['status']}`",
        f"- Discovery only: `{document['discovery_only']}`",
        "",
        "## Resource Counts",
    ]
    lines.extend(
        f"- `{kind}`: {count}" for kind, count in sorted(document["resource_count_by_kind"].items())
    )
    lines.extend(["", "## Prompt Counts"])
    lines.extend(
        f"- `{kind}`: {count}" for kind, count in sorted(document["prompt_count_by_kind"].items())
    )
    lines.extend(["", "## Safety Boundaries"])
    lines.extend(f"- {item}" for item in document["safety_boundaries"])
    lines.extend(["", "## Unsupported Actions"])
    lines.extend(f"- {item}" for item in document["unsupported_actions"])
    lines.extend(["", "## Integrator Notes"])
    lines.extend(f"- {item}" for item in document["integrator_notes"])
    return "\n".join(lines) + "\n"


def write_mcp_compatibility_report(
    path: str | Path,
    *,
    format: str = "json",
    report: McpCompatibilityReport | dict[str, Any] | None = None,
    base_dir: str | Path | None = None,
) -> Path:
    """Write an MCP compatibility report to a safe local path."""
    target = _resolve_safe_output_path(Path(path), Path(base_dir) if base_dir else None)
    target.parent.mkdir(parents=True, exist_ok=True)
    if format == "markdown":
        text = mcp_compatibility_report_to_markdown(report)
    elif format == "json":
        text = mcp_compatibility_report_to_json(report, pretty=True)
    else:
        raise ValueError("Report format must be 'json' or 'markdown'.")
    target.write_text(text, encoding="utf-8")
    return target


def sample_mcp_compatibility_report() -> McpCompatibilityReport:
    """Return the current local sample MCP compatibility report."""
    return build_mcp_compatibility_report()


def _report_dict(value: McpCompatibilityReport | dict[str, Any]) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", by_alias=True)
    return dict(value)
