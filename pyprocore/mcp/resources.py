"""Local discovery-only MCP resources for PyProcore."""

from __future__ import annotations

import json
from typing import Any

from pyprocore.agent.openapi import build_agent_openapi_spec, build_agent_tool_schemas
from pyprocore.agent.registry import build_agent_manifest
from pyprocore.evals import list_builtin_dataset_names, sample_eval_report
from pyprocore.mcp.models import McpResource, McpResourceKind, McpSafetyBoundary

JsonObject = dict[str, Any]

DISCOVERY_ONLY_NOTES = [
    "MCP resources are local metadata only.",
    "No Procore API call is made while reading this resource.",
    "No model API call, plugin execution, upload, approval, or write action is performed.",
]


def list_mcp_resources() -> list[McpResource]:
    """Return all static local MCP resources sorted by URI."""
    resources = [
        _resource(
            "pyprocore://agent/manifest",
            "PyProcore Agent Manifest",
            "Local agent tool registry manifest.",
            McpResourceKind.AGENT_MANIFEST,
            ["agent", "tools"],
        ),
        _resource(
            "pyprocore://agent/tools",
            "PyProcore Agent Tools",
            "MCP-style metadata for registered agent tools. Execution remains disabled.",
            McpResourceKind.AGENT_TOOL_SCHEMA,
            ["agent", "tools", "schema"],
        ),
        _resource(
            "pyprocore://agent/schemas",
            "PyProcore Agent Schemas",
            "JSON Schema export for agent models and registered tool inputs.",
            McpResourceKind.JSON_SCHEMA,
            ["agent", "schema"],
        ),
        _resource(
            "pyprocore://agent/openapi",
            "PyProcore Agent OpenAPI",
            "OpenAPI document for the local Agent API discovery surface.",
            McpResourceKind.OPENAPI_SCHEMA,
            ["agent", "openapi"],
        ),
        _resource(
            "pyprocore://evals/suites",
            "PyProcore Eval Suites",
            "Names and safety metadata for bundled local deterministic eval suites.",
            McpResourceKind.EVAL_SUITE,
            ["evals", "golden"],
        ),
        _resource(
            "pyprocore://evals/sample-report",
            "PyProcore Sample Eval Report",
            "Placeholder local eval report for integration planning.",
            McpResourceKind.EVAL_REPORT,
            ["evals", "report"],
        ),
        _resource(
            "pyprocore://plugins/manifest",
            "PyProcore Plugin Manifest Metadata",
            "Metadata-only plugin manifest summary. Plugins are not executed.",
            McpResourceKind.PLUGIN_MANIFEST,
            ["plugins", "metadata"],
        ),
        _resource(
            "pyprocore://plugins/hooks",
            "PyProcore Plugin Hook Metadata",
            "Local hook capability summary. Hook callables are not invoked.",
            McpResourceKind.PLUGIN_MANIFEST,
            ["plugins", "hooks"],
        ),
        _resource(
            "pyprocore://plugins/config-template",
            "PyProcore Plugin Config Template",
            "Safe local plugin configuration guidance.",
            McpResourceKind.PLUGIN_CONFIG,
            ["plugins", "config"],
        ),
        _resource(
            "pyprocore://async/capabilities",
            "PyProcore Async Capabilities",
            "Summary of async read/export helpers available in the SDK.",
            McpResourceKind.ASYNC_CAPABILITY,
            ["async", "exports"],
        ),
        _resource(
            "pyprocore://ai-workflows/templates",
            "PyProcore AI Workflow Templates",
            "Model-agnostic local workflow template metadata.",
            McpResourceKind.AI_WORKFLOW_TEMPLATE,
            ["ai-workflows", "templates"],
        ),
        _resource(
            "pyprocore://safety/boundaries",
            "PyProcore MCP Safety Boundaries",
            "Explicit discovery-only safety and unsupported-action boundaries.",
            McpResourceKind.SAFETY_BOUNDARY,
            ["safety", "mcp"],
        ),
        _resource(
            "pyprocore://docs/index",
            "PyProcore Documentation Index",
            "Local documentation entry points for SDK, agent, MCP, eval, plugin, and async topics.",
            McpResourceKind.DOCS_REFERENCE,
            ["docs"],
        ),
    ]
    return sorted(resources, key=lambda resource: resource.uri)


def read_mcp_resource_payload(uri: str) -> JsonObject:
    """Return a local JSON payload for a known MCP resource URI.

    Args:
        uri: Resource URI.

    Raises:
        FileNotFoundError: If the URI is not registered.

    Returns:
        JSON-serializable local payload.
    """
    resources = {resource.uri: resource for resource in list_mcp_resources()}
    if uri not in resources:
        raise FileNotFoundError(f"MCP resource is not registered: {uri}")

    payloads = {
        "pyprocore://agent/manifest": lambda: build_agent_manifest().model_dump(mode="json"),
        "pyprocore://agent/tools": _agent_tools_payload,
        "pyprocore://agent/schemas": build_agent_tool_schemas,
        "pyprocore://agent/openapi": build_agent_openapi_spec,
        "pyprocore://evals/suites": _eval_suites_payload,
        "pyprocore://evals/sample-report": lambda: sample_eval_report().model_dump(mode="json"),
        "pyprocore://plugins/manifest": _plugin_manifest_payload,
        "pyprocore://plugins/hooks": _plugin_hooks_payload,
        "pyprocore://plugins/config-template": _plugin_config_template_payload,
        "pyprocore://async/capabilities": _async_capabilities_payload,
        "pyprocore://ai-workflows/templates": _ai_workflow_templates_payload,
        "pyprocore://safety/boundaries": _safety_boundaries_payload,
        "pyprocore://docs/index": _docs_index_payload,
    }
    return {
        "server_name": "pyprocore-agent-mcp",
        "resource": resources[uri].model_dump(mode="json"),
        "payload": payloads[uri](),
        "safety": _safety().model_dump(mode="json"),
    }


def get_mcp_resource(uri: str) -> JsonObject:
    """Return an MCP resource read response for a known URI."""
    payload = read_mcp_resource_payload(uri)
    return {
        "contents": [
            {
                "uri": uri,
                "mimeType": "application/json",
                "text": json.dumps(payload, indent=2, sort_keys=True),
            }
        ]
    }


def safe_mcp_resource_not_found(uri: str) -> JsonObject:
    """Return a safe JSON-serializable response for an unknown resource URI."""
    return {
        "isError": True,
        "error": "resource_not_found",
        "uri": uri,
        "message": f"MCP resource is not registered: {uri}",
        "safety": _safety().model_dump(mode="json"),
    }


def disabled_mcp_execution_response(action: str) -> JsonObject:
    """Return a safe response for execution-like MCP calls."""
    return {
        "isError": True,
        "error": "execution_disabled",
        "action": action,
        "message": (
            "MCP execution is disabled. PyProcore Phase 15A exposes discovery "
            "metadata only, so no Procore, plugin, model, upload, or write action was run. "
            "no Procore API call was made."
        ),
        "safety": _safety().model_dump(mode="json"),
    }


def _agent_tools_payload() -> JsonObject:
    from pyprocore.agent.mcp import build_mcp_tool_definitions

    return {"tools": build_mcp_tool_definitions()}


def _eval_suites_payload() -> JsonObject:
    return {
        "mode": "local_deterministic",
        "suite_count": len(list_builtin_dataset_names()),
        "suites": list_builtin_dataset_names(),
    }


def _plugin_manifest_payload() -> JsonObject:
    return {
        "mode": "metadata_only",
        "execution_enabled": False,
        "capabilities": ["manifest validation", "registry summaries", "scaffold templates"],
    }


def _plugin_hooks_payload() -> JsonObject:
    return {
        "mode": "metadata_only",
        "hook_execution_enabled": False,
        "hook_types": ["validator", "formatter", "exporter", "record_transformer"],
    }


def _plugin_config_template_payload() -> JsonObject:
    return {
        "mode": "local_template",
        "remote_fetch_enabled": False,
        "example": {
            "enabled_plugins": ["example_exporter_plugin"],
            "disabled_plugins": [],
            "hook_preferences": [],
        },
    }


def _async_capabilities_payload() -> JsonObject:
    return {
        "mode": "sdk_metadata",
        "live_calls_during_discovery": False,
        "areas": [
            "async client",
            "async pagination",
            "async downloads",
            "async resource exports",
            "async batch planning",
        ],
    }


def _ai_workflow_templates_payload() -> JsonObject:
    return {
        "mode": "model_agnostic_local_templates",
        "external_model_calls": False,
        "templates": [
            "project_context_package",
            "enhanced_rfi_package",
            "enhanced_submittal_package",
            "ai_review_export",
            "ai_prompt_pack",
        ],
    }


def _safety_boundaries_payload() -> JsonObject:
    return _safety().model_dump(mode="json")


def _docs_index_payload() -> JsonObject:
    return {
        "docs": [
            "docs/index.md",
            "docs/agent-api.md",
            "docs/mcp.md",
            "docs/evals.md",
            "docs/plugins.md",
            "docs/async-client.md",
            "docs/ai-workflows.md",
        ],
        "external_fetch_enabled": False,
    }


def _resource(
    uri: str,
    name: str,
    description: str,
    kind: McpResourceKind,
    tags: list[str],
) -> McpResource:
    return McpResource(
        uri=uri,
        name=name,
        description=description,
        kind=kind,
        tags=tags,
        safety=_safety(),
    )


def _safety() -> McpSafetyBoundary:
    return McpSafetyBoundary(notes=list(DISCOVERY_ONLY_NOTES))
