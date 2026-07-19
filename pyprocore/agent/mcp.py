"""Discovery-only MCP adapter for the PyProcore agent registry.

This module maps PyProcore's static :class:`AgentTool` metadata into
MCP-style JSON documents. It never loads credentials, calls Procore, or
executes tools.
"""

from __future__ import annotations

import json
from typing import Any

from pyprocore.agent.models import AgentToolRegistry
from pyprocore.mcp import (
    build_mcp_capability_summary,
    build_mcp_discovery_manifest,
)
from pyprocore.mcp import build_mcp_server_info as build_typed_mcp_server_info
from pyprocore.mcp import (
    build_mcp_stdio_discovery_payload,
)
from pyprocore.mcp import build_mcp_tool_definitions as build_typed_mcp_tool_definitions
from pyprocore.mcp import (
    disabled_mcp_execution_response,
    get_mcp_prompt,
    get_mcp_resource,
    list_mcp_prompts,
    list_mcp_resources,
)

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
    return build_typed_mcp_tool_definitions(registry)


def build_mcp_resource_definitions() -> list[JsonObject]:
    """Build static MCP-style resource definitions for local metadata exports.

    Returns:
        JSON-serializable resource definition list.
    """
    return [
        _mcp_resource_to_wire(resource.model_dump(mode="json", by_alias=True))
        for resource in list_mcp_resources()
    ]


def build_mcp_prompt_definitions() -> list[JsonObject]:
    """Build discovery-only MCP prompt definitions.

    Returns:
        JSON-serializable prompt definitions. These are templates only and do
        not execute PyProcore workflows.
    """
    return [_mcp_prompt_to_wire(prompt.model_dump(mode="json")) for prompt in list_mcp_prompts()]


def build_mcp_server_info(
    registry: AgentToolRegistry | None = None,
) -> JsonObject:
    """Build MCP-style server information and capability metadata.

    Args:
        registry: Optional registry to describe.

    Returns:
        JSON-serializable server information.
    """
    server = build_typed_mcp_server_info(registry).model_dump(mode="json")
    server["protocolVersion"] = server.pop("protocol_version")
    server["safety"]["tool_execution_enabled"] = server["safety"]["procore_tool_execution_enabled"]
    server["safety"]["phase"] = "15A"
    return server


def build_mcp_capability_definitions(
    registry: AgentToolRegistry | None = None,
) -> JsonObject:
    """Build the discovery-only MCP capability summary."""
    return build_mcp_capability_summary(registry).model_dump(mode="json")


def build_mcp_safety_boundaries() -> JsonObject:
    """Build the MCP safety boundary summary."""
    return build_mcp_capability_summary().safety.model_dump(mode="json")


def build_mcp_stdio_discovery() -> JsonObject:
    """Build the stdio-friendly discovery payload."""
    return build_mcp_stdio_discovery_payload()


def build_mcp_tool_execution_disabled_response(tool_name: str) -> JsonObject:
    """Build the response returned when an MCP client attempts tool execution.

    Args:
        tool_name: Requested tool name.

    Returns:
        Structured MCP-style response explaining that execution is disabled.
    """
    response = disabled_mcp_execution_response(tool_name)
    return {
        "isError": True,
        "content": [{"type": "text", "text": response["message"]}],
        "metadata": {
            "tool_name": tool_name,
            "execution_enabled": False,
            "discovery_only": True,
            "calls_live_api": False,
            "mcp_execution_enabled": False,
            "phase": "15A",
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


def export_mcp_capabilities_json(*, pretty: bool = False) -> str:
    """Return the MCP capability summary as deterministic JSON."""
    return _json_dumps(build_mcp_capability_definitions(), pretty=pretty)


def export_mcp_safety_json(*, pretty: bool = False) -> str:
    """Return MCP safety boundaries as deterministic JSON."""
    return _json_dumps(build_mcp_safety_boundaries(), pretty=pretty)


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
    manifest = build_mcp_discovery_manifest(registry).model_dump(mode="json", by_alias=True)
    manifest["server"] = build_mcp_server_info(registry)
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
    return get_mcp_resource(uri)


def read_mcp_prompt(name: str) -> JsonObject:
    """Return one local prompt template as an MCP-style response."""
    try:
        prompt = get_mcp_prompt(name)
    except KeyError as exc:
        raise FileNotFoundError(str(exc)) from exc
    return {
        "description": prompt.description,
        "messages": [
            {
                "role": "user",
                "content": {"type": "text", "text": prompt.template},
            }
        ],
        "metadata": prompt.model_dump(mode="json"),
    }


def _mcp_resource_to_wire(resource: JsonObject) -> JsonObject:
    """Convert typed resource data to MCP wire naming."""
    return {
        "uri": resource["uri"],
        "name": resource["name"],
        "description": resource["description"],
        "mimeType": resource.get("mime_type", "application/json"),
        "metadata": {
            "kind": resource["kind"],
            "tags": resource.get("tags", []),
            "safety": resource["safety"],
        },
    }


def _mcp_prompt_to_wire(prompt: JsonObject) -> JsonObject:
    """Convert typed prompt data to MCP wire naming."""
    return {
        "name": prompt["name"],
        "title": prompt["title"],
        "description": prompt["description"],
        "arguments": prompt["arguments"],
        "metadata": {
            "kind": prompt["kind"],
            "tags": prompt.get("tags", []),
            "template": prompt["template"],
            "discovery_only": True,
            "calls_live_api": False,
            "requires_auth": False,
            "safety": prompt["safety"],
        },
    }


def _json_dumps(value: Any, *, pretty: bool) -> str:
    """Serialize a JSON-compatible value deterministically."""
    return json.dumps(value, indent=2 if pretty else None, sort_keys=True)
