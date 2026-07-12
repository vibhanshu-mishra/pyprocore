"""Discovery-only MCP adapter for the PyProcore agent registry.

This module maps PyProcore's static :class:`AgentTool` metadata into
MCP-style JSON documents. It never loads credentials, calls Procore, or
executes tools.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from pyprocore.agent.models import AgentTool, AgentToolRegistry
from pyprocore.agent.openapi import build_agent_openapi_spec, build_agent_tool_schemas
from pyprocore.agent.registry import get_agent_registry

JsonObject = dict[str, Any]


def build_mcp_tool_definitions(
    registry: AgentToolRegistry | None = None,
) -> list[JsonObject]:
    """Build deterministic MCP-style tool definitions.

    Args:
        registry: Optional agent registry to export. When omitted, the static
            PyProcore registry is used.

    Returns:
        JSON-serializable MCP-style tool definition list.
    """
    active_registry = registry or get_agent_registry()
    return [
        _build_mcp_tool(tool) for tool in sorted(active_registry.tools, key=lambda item: item.name)
    ]


def build_mcp_resource_definitions() -> list[JsonObject]:
    """Build static MCP-style resource definitions for local metadata exports.

    Returns:
        JSON-serializable resource definition list.
    """
    resources = [
        {
            "uri": "pyprocore://agent/manifest",
            "name": "PyProcore Agent MCP Manifest",
            "description": "Discovery-only MCP manifest for the local PyProcore agent registry.",
            "mimeType": "application/json",
        },
        {
            "uri": "pyprocore://agent/openapi",
            "name": "PyProcore Agent OpenAPI",
            "description": "OpenAPI document for the local PyProcore Agent API.",
            "mimeType": "application/json",
        },
        {
            "uri": "pyprocore://agent/schemas",
            "name": "PyProcore Agent JSON Schemas",
            "description": "JSON Schema export for PyProcore agent models and tool inputs.",
            "mimeType": "application/json",
        },
    ]
    return sorted(resources, key=lambda resource: str(resource["uri"]))


def build_mcp_prompt_definitions() -> list[JsonObject]:
    """Build discovery-only MCP prompt definitions.

    Returns:
        JSON-serializable prompt definitions. These are templates only and do
        not execute PyProcore workflows.
    """
    return [
        {
            "name": "pyprocore.discovery_summary",
            "description": (
                "Summarize the available PyProcore tools from MCP discovery metadata. "
                "This prompt is informational only."
            ),
            "arguments": [
                {
                    "name": "task",
                    "description": "What the user wants to discover or plan.",
                    "required": False,
                }
            ],
            "metadata": {
                "discovery_only": True,
                "calls_live_api": False,
                "requires_auth": False,
            },
        }
    ]


def build_mcp_server_info(
    registry: AgentToolRegistry | None = None,
) -> JsonObject:
    """Build MCP-style server information and capability metadata.

    Args:
        registry: Optional registry to describe.

    Returns:
        JSON-serializable server information.
    """
    from pyprocore import __version__

    active_registry = registry or get_agent_registry()
    return {
        "name": "pyprocore-agent-mcp",
        "title": "PyProcore Agent MCP Adapter",
        "version": __version__,
        "protocolVersion": "2024-11-05",
        "description": (
            "Discovery-only MCP adapter for PyProcore agent tools. Tool execution "
            "is disabled in Phase 7E."
        ),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "registry_version": active_registry.registry_version,
        "tool_count": active_registry.tool_count,
        "capabilities": {
            "tools": {"listChanged": False},
            "resources": {"subscribe": False, "listChanged": False},
            "prompts": {"listChanged": False},
        },
        "safety": {
            "discovery_only": True,
            "tool_execution_enabled": False,
            "calls_live_procore_api": False,
            "requires_credentials": False,
            "phase": "7E",
            "notes": [
                "MCP clients can inspect tool metadata only.",
                "tools/call returns a disabled execution response.",
                "No access tokens, refresh tokens, client secrets, or .env values are exported.",
            ],
        },
    }


def build_mcp_tool_execution_disabled_response(tool_name: str) -> JsonObject:
    """Build the response returned when an MCP client attempts tool execution.

    Args:
        tool_name: Requested tool name.

    Returns:
        Structured MCP-style response explaining that execution is disabled.
    """
    return {
        "isError": True,
        "content": [
            {
                "type": "text",
                "text": (
                    f"Tool execution is disabled for '{tool_name}'. Phase 7E is "
                    "discovery-only, so no Procore API call was made."
                ),
            }
        ],
        "metadata": {
            "tool_name": tool_name,
            "execution_enabled": False,
            "discovery_only": True,
            "calls_live_api": False,
            "phase": "7E",
        },
    }


def export_mcp_tools_json(
    *,
    pretty: bool = False,
    registry: AgentToolRegistry | None = None,
) -> str:
    """Return MCP-style tool definitions as deterministic JSON.

    Args:
        pretty: Whether to format JSON with two-space indentation.
        registry: Optional registry to export.

    Returns:
        JSON string.
    """
    return _json_dumps(build_mcp_tool_definitions(registry=registry), pretty=pretty)


def export_mcp_resources_json(*, pretty: bool = False) -> str:
    """Return MCP-style resource definitions as deterministic JSON.

    Args:
        pretty: Whether to format JSON with two-space indentation.

    Returns:
        JSON string.
    """
    return _json_dumps(build_mcp_resource_definitions(), pretty=pretty)


def export_mcp_prompts_json(*, pretty: bool = False) -> str:
    """Return MCP-style prompt definitions as deterministic JSON.

    Args:
        pretty: Whether to format JSON with two-space indentation.

    Returns:
        JSON string.
    """
    return _json_dumps(build_mcp_prompt_definitions(), pretty=pretty)


def export_mcp_manifest_json(
    *,
    pretty: bool = False,
    registry: AgentToolRegistry | None = None,
) -> str:
    """Return the discovery-only MCP manifest as deterministic JSON.

    Args:
        pretty: Whether to format JSON with two-space indentation.
        registry: Optional registry to describe.

    Returns:
        JSON string.
    """
    manifest = {
        "server": build_mcp_server_info(registry=registry),
        "tools": build_mcp_tool_definitions(registry=registry),
        "resources": build_mcp_resource_definitions(),
        "prompts": build_mcp_prompt_definitions(),
    }
    return _json_dumps(manifest, pretty=pretty)


def read_mcp_resource(uri: str) -> JsonObject:
    """Return a local MCP resource document by URI.

    Args:
        uri: Resource URI from :func:`build_mcp_resource_definitions`.

    Raises:
        FileNotFoundError: If the URI is not a supported local resource.

    Returns:
        JSON-serializable resource read response.
    """
    if uri == "pyprocore://agent/manifest":
        text = export_mcp_manifest_json(pretty=True)
    elif uri == "pyprocore://agent/openapi":
        text = json.dumps(build_agent_openapi_spec(), indent=2, sort_keys=True)
    elif uri == "pyprocore://agent/schemas":
        text = json.dumps(build_agent_tool_schemas(), indent=2, sort_keys=True)
    else:
        raise FileNotFoundError(f"MCP resource is not registered: {uri}")

    return {
        "contents": [
            {
                "uri": uri,
                "mimeType": "application/json",
                "text": text,
            }
        ]
    }


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
        },
    }


def _json_dumps(value: Any, *, pretty: bool) -> str:
    """Serialize a JSON-compatible value deterministically."""
    return json.dumps(value, indent=2 if pretty else None, sort_keys=True)
