"""Local snapshot helpers for PyProcore MCP discovery metadata."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import Field

from pyprocore.mcp.contracts import build_mcp_contract_report
from pyprocore.models.base import ProcoreModel

SNAPSHOT_SCHEMA_VERSION = "mcp-snapshot-v1"


def _package_version() -> str:
    from pyprocore import __version__

    return __version__


class McpSnapshotMetadata(ProcoreModel):
    """Metadata for a local MCP discovery snapshot."""

    schema_version: str = SNAPSHOT_SCHEMA_VERSION
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    package_version: str = Field(default_factory=_package_version)
    server_name: str
    resource_count: int
    prompt_count: int
    contract_passed: bool


class McpDiscoverySnapshot(ProcoreModel):
    """Local JSON snapshot of the discovery-only MCP surface."""

    metadata: McpSnapshotMetadata
    server: dict[str, Any]
    capabilities: dict[str, Any]
    resources: list[dict[str, Any]]
    resource_templates: list[dict[str, Any]]
    prompts: list[dict[str, Any]]
    disabled_execution_response: dict[str, Any]
    contract_report: dict[str, Any]
    safety: dict[str, Any]


def build_mcp_discovery_snapshot() -> McpDiscoverySnapshot:
    """Build a local snapshot of current MCP discovery metadata."""
    from pyprocore.mcp.discovery import build_mcp_discovery_manifest
    from pyprocore.mcp.resources import disabled_mcp_execution_response

    manifest = build_mcp_discovery_manifest()
    manifest_data = manifest.model_dump(mode="json", by_alias=True)
    contract_report = build_mcp_contract_report(manifest_data)
    resources = manifest_data["resources"]
    prompts = manifest_data["prompts"]
    return McpDiscoverySnapshot(
        metadata=McpSnapshotMetadata(
            server_name=manifest.server.name,
            resource_count=len(resources),
            prompt_count=len(prompts),
            contract_passed=bool(contract_report["passed"]),
        ),
        server=manifest_data["server"],
        capabilities=manifest_data["capabilities"],
        resources=resources,
        resource_templates=manifest_data["resource_templates"],
        prompts=prompts,
        disabled_execution_response=disabled_mcp_execution_response("procore.example"),
        contract_report=contract_report,
        safety=manifest_data["capabilities"]["safety"],
    )


def mcp_snapshot_to_json(
    snapshot: McpDiscoverySnapshot | dict[str, Any] | None = None,
    *,
    pretty: bool = False,
) -> str:
    """Serialize a discovery snapshot as deterministic JSON."""
    document = _snapshot_dict(snapshot or build_mcp_discovery_snapshot())
    return json.dumps(document, indent=2 if pretty else None, sort_keys=True)


def write_mcp_discovery_snapshot(
    path: str | Path,
    snapshot: McpDiscoverySnapshot | dict[str, Any] | None = None,
    *,
    base_dir: str | Path | None = None,
    pretty: bool = True,
) -> Path:
    """Write a local MCP discovery snapshot to a safe JSON path."""
    target = _resolve_safe_output_path(Path(path), Path(base_dir) if base_dir else None)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(mcp_snapshot_to_json(snapshot, pretty=pretty), encoding="utf-8")
    return target


def load_mcp_discovery_snapshot(path: str | Path) -> McpDiscoverySnapshot:
    """Load a local MCP discovery snapshot from JSON."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return McpDiscoverySnapshot.model_validate(payload)


def compare_mcp_discovery_snapshots(
    before: McpDiscoverySnapshot | dict[str, Any],
    after: McpDiscoverySnapshot | dict[str, Any],
) -> dict[str, Any]:
    """Compare two local MCP discovery snapshots by resource and prompt names."""
    before_data = _snapshot_dict(before)
    after_data = _snapshot_dict(after)
    before_resources = {item["uri"] for item in before_data.get("resources", [])}
    after_resources = {item["uri"] for item in after_data.get("resources", [])}
    before_prompts = {item["name"] for item in before_data.get("prompts", [])}
    after_prompts = {item["name"] for item in after_data.get("prompts", [])}
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "resource_count_before": len(before_resources),
        "resource_count_after": len(after_resources),
        "prompt_count_before": len(before_prompts),
        "prompt_count_after": len(after_prompts),
        "resources_added": sorted(after_resources - before_resources),
        "resources_removed": sorted(before_resources - after_resources),
        "prompts_added": sorted(after_prompts - before_prompts),
        "prompts_removed": sorted(before_prompts - after_prompts),
        "compatible": before_resources.issubset(after_resources)
        and before_prompts.issubset(after_prompts),
    }


def summarize_mcp_discovery_snapshot(
    snapshot: McpDiscoverySnapshot | dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Summarize a local MCP discovery snapshot for CLI output."""
    document = _snapshot_dict(snapshot or build_mcp_discovery_snapshot())
    metadata = document["metadata"]
    capabilities = document["capabilities"]
    return {
        "schema_version": metadata["schema_version"],
        "server_name": metadata["server_name"],
        "package_version": metadata["package_version"],
        "resource_count": metadata["resource_count"],
        "prompt_count": metadata["prompt_count"],
        "contract_passed": metadata["contract_passed"],
        "discovery_only": capabilities["safety"]["discovery_only"],
        "execution_enabled": False,
        "unsupported_actions": capabilities.get("unsupported_actions", []),
    }


def _snapshot_dict(value: McpDiscoverySnapshot | dict[str, Any]) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", by_alias=True)
    return dict(value)


def _resolve_safe_output_path(path: Path, base_dir: Path | None = None) -> Path:
    if ".." in path.parts:
        raise ValueError("Output paths may not contain parent-directory traversal.")
    if base_dir is None:
        return path.expanduser().resolve()
    base = base_dir.expanduser().resolve()
    candidate = (base / path).resolve() if not path.is_absolute() else path.resolve()
    if candidate != base and base not in candidate.parents:
        raise ValueError("Output path must stay inside the selected base directory.")
    return candidate
