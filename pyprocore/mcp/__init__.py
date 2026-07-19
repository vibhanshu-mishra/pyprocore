"""Discovery-only MCP metadata helpers for PyProcore."""

from pyprocore.mcp.capabilities import build_mcp_capability_summary, build_mcp_tool_summary
from pyprocore.mcp.discovery import (
    build_mcp_discovery_manifest,
    build_mcp_resource_templates,
    build_mcp_server_info,
    build_mcp_stdio_discovery_payload,
    build_mcp_tool_definitions,
    mcp_manifest_to_json,
)
from pyprocore.mcp.models import (
    McpCapabilitySummary,
    McpDiscoveryManifest,
    McpPrompt,
    McpPromptArgument,
    McpPromptKind,
    McpResource,
    McpResourceKind,
    McpResourceTemplate,
    McpSafetyBoundary,
    McpServerInfo,
    McpToolSummary,
)
from pyprocore.mcp.prompts import get_mcp_prompt, list_mcp_prompts, safe_mcp_prompt_not_found
from pyprocore.mcp.resources import (
    disabled_mcp_execution_response,
    get_mcp_resource,
    list_mcp_resources,
    read_mcp_resource_payload,
    safe_mcp_resource_not_found,
)

__all__ = [
    "McpCapabilitySummary",
    "McpDiscoveryManifest",
    "McpPrompt",
    "McpPromptArgument",
    "McpPromptKind",
    "McpResource",
    "McpResourceKind",
    "McpResourceTemplate",
    "McpSafetyBoundary",
    "McpServerInfo",
    "McpToolSummary",
    "build_mcp_capability_summary",
    "build_mcp_discovery_manifest",
    "build_mcp_resource_templates",
    "build_mcp_server_info",
    "build_mcp_stdio_discovery_payload",
    "build_mcp_tool_definitions",
    "build_mcp_tool_summary",
    "disabled_mcp_execution_response",
    "get_mcp_prompt",
    "get_mcp_resource",
    "list_mcp_prompts",
    "list_mcp_resources",
    "mcp_manifest_to_json",
    "read_mcp_resource_payload",
    "safe_mcp_prompt_not_found",
    "safe_mcp_resource_not_found",
]
