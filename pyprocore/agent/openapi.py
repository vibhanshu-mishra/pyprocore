"""OpenAPI and JSON Schema exports for the local PyProcore Agent API."""

from __future__ import annotations

import json
from typing import Any

from pyprocore.agent.models import AgentManifest, AgentTool, AgentToolRegistry
from pyprocore.agent.registry import get_agent_registry

JsonObject = dict[str, Any]


def build_agent_openapi_spec(
    registry: AgentToolRegistry | None = None,
) -> JsonObject:
    """Build a deterministic OpenAPI document for the local Agent API.

    Args:
        registry: Optional registry to describe. When omitted, the current
            static PyProcore agent registry is used.

    Returns:
        JSON-serializable OpenAPI 3.1 document.
    """
    active_registry = registry or get_agent_registry()
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "PyProcore Agent API",
            "version": _service_version(),
            "description": (
                "Local-first discovery API for PyProcore agent tool metadata. "
                "The API is specification and discovery only; tool execution "
                "is disabled in this phase."
            ),
        },
        "servers": [{"url": "http://127.0.0.1:8765", "description": "Local development server"}],
        "tags": [{"name": "agent", "description": "Agent discovery metadata"}],
        "x-pyprocore-safety": {
            "local_first": True,
            "requires_credentials": False,
            "calls_live_procore_api": False,
            "tool_execution_enabled": False,
            "notes": [
                "Bind the local server to 127.0.0.1 unless you intentionally opt in.",
                "The /call endpoint is documented for future adapters but returns 501.",
                "No access tokens, refresh tokens, client secrets, or .env values are exported.",
            ],
        },
        "paths": _build_paths(active_registry),
        "components": {
            "schemas": _build_openapi_components(active_registry),
        },
    }


def export_agent_openapi_json(
    *,
    pretty: bool = False,
    registry: AgentToolRegistry | None = None,
) -> str:
    """Return the Agent API OpenAPI document as deterministic JSON.

    Args:
        pretty: Whether to format JSON with two-space indentation.
        registry: Optional registry to describe.

    Returns:
        JSON string.
    """
    indent = 2 if pretty else None
    return json.dumps(
        build_agent_openapi_spec(registry=registry),
        indent=indent,
        sort_keys=True,
    )


def export_agent_openapi_yaml(
    *,
    registry: AgentToolRegistry | None = None,
) -> str:
    """Return the Agent API OpenAPI document as simple deterministic YAML.

    The project intentionally avoids a YAML dependency for this export. The
    generated YAML supports the JSON-compatible structures used by the OpenAPI
    document.

    Args:
        registry: Optional registry to describe.

    Returns:
        YAML string.
    """
    return _to_yaml(build_agent_openapi_spec(registry=registry))


def build_agent_tool_schemas(
    registry: AgentToolRegistry | None = None,
) -> JsonObject:
    """Build JSON Schema metadata for agent models and registered tools.

    Args:
        registry: Optional registry to describe.

    Returns:
        JSON-serializable schema export containing model schemas and per-tool
        input/output schemas.
    """
    active_registry = registry or get_agent_registry()
    tools: JsonObject = {}
    for tool in active_registry.tools:
        tools[tool.name] = {
            "title": tool.title,
            "description": tool.description,
            "requires_auth": tool.requires_auth,
            "calls_live_api": tool.calls_live_api,
            "produces_files": tool.produces_files,
            "safety_level": tool.safety_level.value,
            "input_schema": tool.input_schema,
            "output_schema": tool.output_schema,
        }

    return {
        "package": "pyprocore",
        "version": _service_version(),
        "registry_version": active_registry.registry_version,
        "tool_count": active_registry.tool_count,
        "schemas": {
            "AgentManifest": AgentManifest.model_json_schema(ref_template="#/$defs/{model}"),
            "AgentTool": AgentTool.model_json_schema(ref_template="#/$defs/{model}"),
            "AgentToolRegistry": AgentToolRegistry.model_json_schema(
                ref_template="#/$defs/{model}"
            ),
            "AgentToolList": {
                "type": "array",
                "items": {"$ref": "#/$defs/AgentTool"},
            },
        },
        "tools": tools,
    }


def export_agent_tool_schemas_json(
    *,
    pretty: bool = False,
    registry: AgentToolRegistry | None = None,
) -> str:
    """Return agent model and tool schemas as deterministic JSON.

    Args:
        pretty: Whether to format JSON with two-space indentation.
        registry: Optional registry to describe.

    Returns:
        JSON string.
    """
    indent = 2 if pretty else None
    return json.dumps(
        build_agent_tool_schemas(registry=registry),
        indent=indent,
        sort_keys=True,
    )


def _build_paths(registry: AgentToolRegistry) -> JsonObject:
    """Build OpenAPI path definitions for discovery endpoints."""
    del registry
    return {
        "/": {
            "get": {
                "tags": ["agent"],
                "summary": "Show service metadata",
                "operationId": "getAgentApiRoot",
                "responses": {
                    "200": {
                        "description": "Service metadata and discovery links.",
                        "content": {"application/json": {"schema": {"type": "object"}}},
                    }
                },
            }
        },
        "/health": {
            "get": {
                "tags": ["agent"],
                "summary": "Check service health",
                "operationId": "getAgentApiHealth",
                "responses": {
                    "200": {
                        "description": "Health check response.",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/HealthResponse"}
                            }
                        },
                    }
                },
            }
        },
        "/agent/manifest": {
            "get": {
                "tags": ["agent"],
                "summary": "Get the agent manifest",
                "operationId": "getAgentManifest",
                "responses": {
                    "200": {
                        "description": "Agent manifest for the local PyProcore installation.",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/AgentManifest"}
                            }
                        },
                    }
                },
            }
        },
        "/agent/tools": {
            "get": {
                "tags": ["agent"],
                "summary": "List registered agent tools",
                "operationId": "listAgentTools",
                "responses": {
                    "200": {
                        "description": "Registered agent tool metadata.",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {"$ref": "#/components/schemas/AgentTool"},
                                }
                            }
                        },
                    }
                },
            }
        },
        "/agent/tools/{tool_name}": {
            "get": {
                "tags": ["agent"],
                "summary": "Get one registered agent tool",
                "operationId": "getAgentTool",
                "parameters": [_tool_name_parameter()],
                "responses": {
                    "200": {
                        "description": "Agent tool metadata.",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/AgentTool"}
                            }
                        },
                    },
                    "404": _error_response("Tool not found."),
                },
            }
        },
        "/agent/tools/{tool_name}/call": {
            "post": {
                "tags": ["agent"],
                "summary": "Disabled future tool execution endpoint",
                "description": (
                    "Tool execution is intentionally disabled in the current "
                    "phase. This endpoint always returns tool_execution_disabled "
                    "for registered tools."
                ),
                "operationId": "callAgentToolDisabled",
                "parameters": [_tool_name_parameter()],
                "requestBody": {
                    "required": False,
                    "content": {"application/json": {"schema": {"type": "object"}}},
                },
                "responses": {
                    "501": {
                        "description": "Tool execution is disabled.",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ToolExecutionDisabledResponse"
                                }
                            }
                        },
                    },
                    "404": _error_response("Tool not found."),
                },
            }
        },
        "/agent/openapi.json": {
            "get": {
                "tags": ["agent"],
                "summary": "Get the Agent API OpenAPI document",
                "operationId": "getAgentOpenApiJson",
                "responses": {
                    "200": {
                        "description": "OpenAPI document for the local Agent API.",
                        "content": {"application/json": {"schema": {"type": "object"}}},
                    }
                },
            }
        },
        "/agent/schemas": {
            "get": {
                "tags": ["agent"],
                "summary": "Get Agent API JSON schemas",
                "operationId": "getAgentSchemas",
                "responses": {
                    "200": {
                        "description": "JSON schemas for agent models and registered tools.",
                        "content": {"application/json": {"schema": {"type": "object"}}},
                    }
                },
            }
        },
    }


def _service_version() -> str:
    """Return the installed PyProcore version without creating import cycles."""
    from pyprocore import __version__

    return __version__


def _build_openapi_components(registry: AgentToolRegistry) -> JsonObject:
    """Build reusable OpenAPI schemas."""
    return {
        "AgentManifest": AgentManifest.model_json_schema(
            ref_template="#/components/schemas/{model}"
        ),
        "AgentTool": AgentTool.model_json_schema(ref_template="#/components/schemas/{model}"),
        "AgentToolRegistry": AgentToolRegistry.model_json_schema(
            ref_template="#/components/schemas/{model}"
        ),
        "AgentToolList": {
            "type": "array",
            "items": {"$ref": "#/components/schemas/AgentTool"},
            "description": f"List of {registry.tool_count} registered PyProcore agent tools.",
        },
        "ErrorResponse": {
            "type": "object",
            "required": ["error", "message"],
            "properties": {
                "error": {"type": "string"},
                "message": {"type": "string"},
            },
            "additionalProperties": True,
        },
        "ToolExecutionDisabledResponse": {
            "type": "object",
            "required": ["error", "message", "tool"],
            "properties": {
                "error": {"type": "string", "const": "tool_execution_disabled"},
                "message": {"type": "string"},
                "tool": {"type": "string"},
            },
            "additionalProperties": False,
        },
        "HealthResponse": {
            "type": "object",
            "required": ["status", "service", "version"],
            "properties": {
                "status": {"type": "string", "const": "ok"},
                "service": {"type": "string", "const": "pyprocore-agent-api"},
                "version": {"type": "string"},
            },
            "additionalProperties": False,
        },
    }


def _tool_name_parameter() -> JsonObject:
    """Return the shared OpenAPI tool-name path parameter."""
    return {
        "name": "tool_name",
        "in": "path",
        "required": True,
        "schema": {"type": "string"},
        "description": "Stable tool name, such as procore.find_rfi.",
    }


def _error_response(description: str) -> JsonObject:
    """Return a shared OpenAPI error response."""
    return {
        "description": description,
        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}},
    }


def _to_yaml(value: Any, indent: int = 0) -> str:
    """Serialize JSON-compatible values to a small deterministic YAML subset."""
    lines = _yaml_lines(value, indent)
    return "\n".join(lines) + "\n"


def _yaml_lines(value: Any, indent: int) -> list[str]:
    """Return YAML lines for a JSON-compatible value."""
    prefix = " " * indent
    if isinstance(value, dict):
        lines: list[str] = []
        for key in sorted(value):
            item = value[key]
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}{_yaml_scalar(key)}:")
                lines.extend(_yaml_lines(item, indent + 2))
            else:
                lines.append(f"{prefix}{_yaml_scalar(key)}: {_yaml_scalar(item)}")
        return lines
    if isinstance(value, list):
        if not value:
            return [f"{prefix}[]"]
        lines = []
        for item in value:
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}-")
                lines.extend(_yaml_lines(item, indent + 2))
            else:
                lines.append(f"{prefix}- {_yaml_scalar(item)}")
        return lines
    return [f"{prefix}{_yaml_scalar(value)}"]


def _yaml_scalar(value: Any) -> str:
    """Return a YAML-safe scalar using JSON quoting for strings."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value))
