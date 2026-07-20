"""Discovery builders for PyProcore's MCP metadata surface."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from pyprocore.agent.models import AgentTool, AgentToolRegistry
from pyprocore.agent.registry import get_agent_registry
from pyprocore.mcp.capabilities import build_mcp_capability_summary
from pyprocore.mcp.compatibility import COMPATIBILITY_SCHEMA_VERSION
from pyprocore.mcp.contracts import CONTRACT_SCHEMA_VERSION, build_mcp_contract_report
from pyprocore.mcp.models import (
    McpDiscoveryManifest,
    McpResourceKind,
    McpResourceTemplate,
    McpSafetyBoundary,
    McpServerInfo,
)
from pyprocore.mcp.prompts import list_mcp_prompts, safe_mcp_prompt_not_found
from pyprocore.mcp.resources import (
    disabled_mcp_execution_response,
    list_mcp_resources,
    safe_mcp_resource_not_found,
)
from pyprocore.mcp.snapshots import SNAPSHOT_SCHEMA_VERSION

JsonObject = dict[str, Any]


def build_mcp_server_info(registry: AgentToolRegistry | None = None) -> McpServerInfo:
    """Build typed MCP server information for local discovery."""
    from pyprocore import __version__

    active_registry = registry or get_agent_registry()
    return McpServerInfo(
        name="pyprocore-agent-mcp",
        title="PyProcore Agent MCP Adapter",
        version=__version__,
        protocol_version="2024-11-05",
        description=(
            "Discovery-only MCP adapter for PyProcore metadata. Tool execution "
            "and Procore live calls are disabled."
        ),
        registry_version=active_registry.registry_version,
        tool_count=active_registry.tool_count,
        capabilities={
            "tools": {"listChanged": False},
            "resources": {"subscribe": False, "listChanged": False},
            "prompts": {"listChanged": False},
            "logging": {},
        },
        safety=McpSafetyBoundary(
            notes=[
                "MCP clients can inspect metadata only.",
                "tools/call returns a disabled execution response.",
                "No access tokens, refresh tokens, client secrets, or .env values are exported.",
            ]
        ),
    )


def build_mcp_tool_definitions(
    registry: AgentToolRegistry | None = None,
) -> list[JsonObject]:
    """Build MCP-style tool definitions from static agent metadata."""
    active_registry = registry or get_agent_registry()
    return [
        _build_mcp_tool(tool) for tool in sorted(active_registry.tools, key=lambda item: item.name)
    ]


def build_mcp_resource_templates() -> list[McpResourceTemplate]:
    """Return resource template metadata for local discovery patterns."""
    return [
        McpResourceTemplate(
            uri_template="pyprocore://agent/tool/{tool_name}",
            name="Agent Tool Metadata",
            description="Template for future local tool metadata lookup. Execution stays disabled.",
            kind=McpResourceKind.AGENT_TOOL_SCHEMA,
            arguments=["tool_name"],
        ),
        McpResourceTemplate(
            uri_template="pyprocore://evals/suites/{suite_name}",
            name="Eval Suite Metadata",
            description="Template for local deterministic eval suite metadata.",
            kind=McpResourceKind.EVAL_SUITE,
            arguments=["suite_name"],
        ),
        McpResourceTemplate(
            uri_template="pyprocore://evals/model-fixtures/{fixture_suite}",
            name="Model Fixture Suite Metadata",
            description="Template for local model-response fixture suite metadata.",
            kind=McpResourceKind.MODEL_FIXTURE,
            arguments=["fixture_suite"],
        ),
    ]


def build_mcp_discovery_manifest(
    registry: AgentToolRegistry | None = None,
) -> McpDiscoveryManifest:
    """Build the complete typed MCP discovery manifest."""
    active_registry = registry or get_agent_registry()
    return McpDiscoveryManifest(
        server=build_mcp_server_info(active_registry),
        tools=build_mcp_tool_definitions(active_registry),
        resources=list_mcp_resources(),
        resource_templates=build_mcp_resource_templates(),
        prompts=list_mcp_prompts(),
        capabilities=build_mcp_capability_summary(active_registry),
    )


def build_mcp_stdio_discovery_payload(
    registry: AgentToolRegistry | None = None,
) -> JsonObject:
    """Return stdio-friendly local discovery payload."""
    manifest = build_mcp_discovery_manifest(registry)
    manifest_data = manifest.model_dump(mode="json", by_alias=True)
    contract_report = build_mcp_contract_report(manifest_data)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "server": manifest_data["server"],
        "capabilities": manifest_data["capabilities"],
        "resourceKindCounts": manifest.capabilities.mcp_resource_metadata.get(
            "resource_kinds",
            {},
        ),
        "promptKindCounts": manifest.capabilities.mcp_prompt_metadata.get("prompt_kinds", {}),
        "tools": manifest.tools,
        "resources": manifest_data["resources"],
        "resourceTemplates": [
            item.model_dump(mode="json", by_alias=True) for item in manifest.resource_templates
        ],
        "prompts": manifest_data["prompts"],
        "disabledExecutionStatus": manifest.capabilities.disabled_execution_status,
        "unsupportedActions": manifest.capabilities.unsupported_actions,
        "safetyBoundaries": manifest.capabilities.safety_boundaries,
        "safety": manifest.capabilities.safety.model_dump(mode="json", by_alias=True),
        "contract": {
            "schemaVersion": CONTRACT_SCHEMA_VERSION,
            "passed": contract_report["passed"],
            "findingCount": contract_report["finding_count"],
        },
        "snapshot": {"schemaVersion": SNAPSHOT_SCHEMA_VERSION},
        "compatibility": {
            "schemaVersion": COMPATIBILITY_SCHEMA_VERSION,
            "discoveryOnly": True,
            "executionEnabled": False,
        },
        "disabledExecutionResponseShape": disabled_mcp_execution_response("procore.example"),
        "unknownResourceResponseShape": safe_mcp_resource_not_found("pyprocore://missing"),
        "unknownPromptResponseShape": safe_mcp_prompt_not_found("missing_prompt"),
        "compatibilityNotes": [
            "Static local metadata only.",
            "Tool calls return disabled responses.",
            "No credentials or live Procore data are exported.",
        ],
    }


def mcp_manifest_to_json(
    manifest: McpDiscoveryManifest,
    *,
    pretty: bool = False,
) -> str:
    """Serialize a typed MCP manifest deterministically."""
    return json.dumps(
        manifest.model_dump(mode="json", by_alias=True),
        indent=2 if pretty else None,
        sort_keys=True,
    )


def _build_mcp_tool(tool: AgentTool) -> JsonObject:
    """Convert one AgentTool into an MCP-style tool definition."""
    return {
        "name": tool.name,
        "title": tool.title,
        "description": tool.description,
        "inputSchema": tool.input_schema,
        "metadata": {
            "category": tool.category.value,
            "permissions": [permission.value for permission in tool.permissions],
            "requires_auth": tool.requires_auth,
            "calls_live_api": tool.calls_live_api,
            "produces_files": tool.produces_files,
            "side_effects": list(tool.side_effects),
            "safety_level": tool.safety_level.value,
            "version_added": tool.version_added,
            "service_path": tool.service_path,
            "operation_path": tool.operation_path,
            "cli_command": tool.cli_command,
            "examples": list(tool.examples),
            "execution_enabled": False,
            "discovery_only": True,
            "mcp_execution_enabled": False,
        },
    }
