"""Local discovery-only MCP resources for PyProcore."""

from __future__ import annotations

import json
from typing import Any

from pyprocore.agent.openapi import build_agent_openapi_spec, build_agent_tool_schemas
from pyprocore.agent.registry import build_agent_manifest
from pyprocore.evals import list_builtin_dataset_names, sample_eval_report
from pyprocore.evals.model_response_suites import get_model_response_dataset_payloads
from pyprocore.mcp.models import McpResource, McpResourceKind, McpSafetyBoundary

JsonObject = dict[str, Any]

DISCOVERY_ONLY_NOTES = [
    "MCP resources are local metadata only.",
    "No Procore API call is made while reading this resource.",
    "No model API call, plugin execution, upload, approval, or write action is performed.",
]


def list_mcp_resources(kind: McpResourceKind | str | None = None) -> list[McpResource]:
    """Return all static local MCP resources sorted by URI.

    Args:
        kind: Optional resource kind filter.

    Returns:
        Local MCP resources. These are metadata records only.
    """
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
        *[
            _resource(
                f"pyprocore://evals/suites/{suite_name}",
                f"PyProcore Eval Suite: {suite_name}",
                "Metadata for one bundled local deterministic eval suite.",
                McpResourceKind.EVAL_SUITE,
                ["evals", "golden", "suite"],
            )
            for suite_name in list_builtin_dataset_names()
        ],
        _resource(
            "pyprocore://evals/sample-report",
            "PyProcore Sample Eval Report",
            "Placeholder local eval report for integration planning.",
            McpResourceKind.EVAL_REPORT,
            ["evals", "report"],
        ),
        _resource(
            "pyprocore://evals/baseline-template",
            "PyProcore Eval Baseline Template",
            "Schema-shaped metadata for local eval baseline files.",
            McpResourceKind.EVAL_BASELINE,
            ["evals", "baseline"],
        ),
        _resource(
            "pyprocore://evals/regression-template",
            "PyProcore Eval Regression Template",
            "Schema-shaped metadata for comparing local eval reports to baselines.",
            McpResourceKind.EVAL_REGRESSION,
            ["evals", "regression"],
        ),
        _resource(
            "pyprocore://evals/history-template",
            "PyProcore Eval History Template",
            "Schema-shaped metadata for local eval history snapshots.",
            McpResourceKind.EVAL_HISTORY,
            ["evals", "history"],
        ),
        _resource(
            "pyprocore://evals/model-fixtures",
            "PyProcore Model Fixture Suites",
            "Names and safety metadata for bundled local model-response fixtures.",
            McpResourceKind.MODEL_FIXTURE,
            ["evals", "model-fixtures"],
        ),
        *[
            _resource(
                f"pyprocore://evals/model-fixtures/{suite_name}",
                f"PyProcore Model Fixture Suite: {suite_name}",
                "Metadata for one bundled local model-response fixture suite.",
                McpResourceKind.MODEL_FIXTURE,
                ["evals", "model-fixtures", "suite"],
            )
            for suite_name in _model_fixture_suite_names()
        ],
        _resource(
            "pyprocore://evals/safety-boundaries",
            "PyProcore Eval Safety Boundaries",
            "Local deterministic eval safety boundaries and unsupported actions.",
            McpResourceKind.SAFETY_BOUNDARY,
            ["evals", "safety"],
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
            "pyprocore://plugins/extension-pack-template",
            "PyProcore Plugin Extension Pack Template",
            "Metadata-only template for packaging plugin extension metadata.",
            McpResourceKind.PLUGIN_EXTENSION_PACK,
            ["plugins", "extension-pack"],
        ),
        _resource(
            "pyprocore://plugins/scaffold-template",
            "PyProcore Plugin Scaffold Template",
            "Safe local scaffold metadata for plugin authors.",
            McpResourceKind.PLUGIN_SCAFFOLD,
            ["plugins", "scaffold"],
        ),
        _resource(
            "pyprocore://plugins/safety-boundaries",
            "PyProcore Plugin Safety Boundaries",
            "Plugin metadata safety rules. Plugins are never executed by MCP discovery.",
            McpResourceKind.SAFETY_BOUNDARY,
            ["plugins", "safety"],
        ),
        _resource(
            "pyprocore://plugins/capabilities",
            "PyProcore Plugin Capabilities",
            "Summary of supported metadata-only plugin capabilities.",
            McpResourceKind.PLUGIN_MANIFEST,
            ["plugins", "capabilities"],
        ),
        _resource(
            "pyprocore://async/capabilities",
            "PyProcore Async Capabilities",
            "Summary of async read/export helpers available in the SDK.",
            McpResourceKind.ASYNC_CAPABILITY,
            ["async", "exports"],
        ),
        _resource(
            "pyprocore://async/resources",
            "PyProcore Async Resources",
            "Read-only SDK resource areas supported by async helpers.",
            McpResourceKind.ASYNC_RESOURCE,
            ["async", "resources"],
        ),
        _resource(
            "pyprocore://async/exports",
            "PyProcore Async Exports",
            "Metadata for async export helpers and output manifests.",
            McpResourceKind.ASYNC_EXPORT,
            ["async", "exports"],
        ),
        _resource(
            "pyprocore://async/batch",
            "PyProcore Async Batch Planning",
            "Metadata for dry-run batch planning patterns.",
            McpResourceKind.ASYNC_BATCH,
            ["async", "batch"],
        ),
        _resource(
            "pyprocore://async/download-patterns",
            "PyProcore Async Download Patterns",
            "Safe metadata for async download planning and local file writes.",
            McpResourceKind.ASYNC_DOWNLOAD_PATTERN,
            ["async", "downloads"],
        ),
        _resource(
            "pyprocore://async/safety-boundaries",
            "PyProcore Async Safety Boundaries",
            "Safety rules for async reads, exports, and dry-run batch plans.",
            McpResourceKind.SAFETY_BOUNDARY,
            ["async", "safety"],
        ),
        _resource(
            "pyprocore://async/read-only-coverage",
            "PyProcore Async Read-Only Coverage",
            "Read-only coverage metadata for async SDK surfaces.",
            McpResourceKind.ASYNC_RESOURCE,
            ["async", "coverage"],
        ),
        _resource(
            "pyprocore://ai-workflows/templates",
            "PyProcore AI Workflow Templates",
            "Model-agnostic local workflow template metadata.",
            McpResourceKind.AI_WORKFLOW_TEMPLATE,
            ["ai-workflows", "templates"],
        ),
        *[
            _resource(
                f"pyprocore://ai-workflows/{workflow_name}",
                f"PyProcore AI Workflow: {workflow_name}",
                "Metadata-only template for local AI-ready workflow package review.",
                McpResourceKind.AI_WORKFLOW_REVIEW,
                ["ai-workflows", "review"],
            )
            for workflow_name in _ai_workflow_resource_names()
        ],
        _resource(
            "pyprocore://ai-workflows/vector-export-pattern",
            "PyProcore Vector Export Pattern",
            "Metadata-only guidance for preparing local files for vector indexing.",
            McpResourceKind.AI_WORKFLOW_TEMPLATE,
            ["ai-workflows", "vector-export"],
        ),
        _resource(
            "pyprocore://ai-workflows/model-fixture-evals",
            "PyProcore AI Workflow Model Fixture Evals",
            "Local model-response fixture eval metadata for AI workflow packages.",
            McpResourceKind.MODEL_FIXTURE,
            ["ai-workflows", "model-fixtures"],
        ),
        _resource(
            "pyprocore://ai-workflows/safety-boundaries",
            "PyProcore AI Workflow Safety Boundaries",
            "Safety rules for local AI workflow package review.",
            McpResourceKind.SAFETY_BOUNDARY,
            ["ai-workflows", "safety"],
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
    filtered_resources = _filter_resources(resources, kind)
    return sorted(filtered_resources, key=lambda resource: resource.uri)


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
        "pyprocore://evals/baseline-template": _eval_baseline_template_payload,
        "pyprocore://evals/regression-template": _eval_regression_template_payload,
        "pyprocore://evals/history-template": _eval_history_template_payload,
        "pyprocore://evals/model-fixtures": _model_fixtures_payload,
        "pyprocore://evals/safety-boundaries": _eval_safety_boundaries_payload,
        "pyprocore://plugins/manifest": _plugin_manifest_payload,
        "pyprocore://plugins/hooks": _plugin_hooks_payload,
        "pyprocore://plugins/config-template": _plugin_config_template_payload,
        "pyprocore://plugins/extension-pack-template": _plugin_extension_pack_template_payload,
        "pyprocore://plugins/scaffold-template": _plugin_scaffold_template_payload,
        "pyprocore://plugins/safety-boundaries": _plugin_safety_boundaries_payload,
        "pyprocore://plugins/capabilities": _plugin_capabilities_payload,
        "pyprocore://async/capabilities": _async_capabilities_payload,
        "pyprocore://async/resources": _async_resources_payload,
        "pyprocore://async/exports": _async_exports_payload,
        "pyprocore://async/batch": _async_batch_payload,
        "pyprocore://async/download-patterns": _async_download_patterns_payload,
        "pyprocore://async/safety-boundaries": _async_safety_boundaries_payload,
        "pyprocore://async/read-only-coverage": _async_read_only_coverage_payload,
        "pyprocore://ai-workflows/templates": _ai_workflow_templates_payload,
        "pyprocore://ai-workflows/vector-export-pattern": _ai_workflow_vector_export_payload,
        "pyprocore://ai-workflows/model-fixture-evals": _ai_workflow_model_fixture_evals_payload,
        "pyprocore://ai-workflows/safety-boundaries": _ai_workflow_safety_boundaries_payload,
        "pyprocore://safety/boundaries": _safety_boundaries_payload,
        "pyprocore://docs/index": _docs_index_payload,
    }
    if uri.startswith("pyprocore://evals/suites/"):
        suite_name = uri.rsplit("/", 1)[-1]
        payload = _eval_suite_payload(suite_name)
    elif uri.startswith("pyprocore://evals/model-fixtures/"):
        fixture_suite = uri.rsplit("/", 1)[-1]
        payload = _model_fixture_suite_payload(fixture_suite)
    elif uri.startswith("pyprocore://ai-workflows/") and uri not in payloads:
        workflow_name = uri.rsplit("/", 1)[-1]
        payload = _ai_workflow_review_payload(workflow_name)
    else:
        payload = payloads[uri]()
    return {
        "server_name": "pyprocore-agent-mcp",
        "resource": resources[uri].model_dump(mode="json"),
        "payload": payload,
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
            "MCP execution is disabled. PyProcore exposes discovery "
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
        "fixture_suite_count": len(_model_fixture_suite_names()),
        "safety": "Discovery lists local suite metadata only.",
    }


def _eval_suite_payload(suite_name: str) -> JsonObject:
    return {
        "mode": "local_deterministic",
        "suite_name": suite_name,
        "registered": suite_name in list_builtin_dataset_names(),
        "execution_enabled": False,
        "baseline_supported": True,
        "regression_supported": True,
        "history_supported": True,
        "notes": [
            "This resource describes a local eval suite.",
            "Reading this resource does not run the suite.",
        ],
    }


def _eval_baseline_template_payload() -> JsonObject:
    return {
        "mode": "local_template",
        "schema": {
            "schema_version": "baseline-v1",
            "created_at": "{iso_timestamp}",
            "suite_name": "{suite_name}",
            "case_count": 0,
            "passing_score": 0.0,
            "case_results": [],
        },
        "usage": "Use with local eval reports to compare future runs.",
    }


def _eval_regression_template_payload() -> JsonObject:
    return {
        "mode": "local_template",
        "schema": {
            "suite_name": "{suite_name}",
            "baseline_score": 0.0,
            "current_score": 0.0,
            "status": "pass|warn|fail",
            "findings": [],
        },
        "usage": "Use for deterministic local regression review.",
    }


def _eval_history_template_payload() -> JsonObject:
    return {
        "mode": "local_template",
        "schema": {
            "history": [
                {
                    "timestamp": "{iso_timestamp}",
                    "suite_name": "{suite_name}",
                    "status": "pass|warn|fail",
                    "score": 0.0,
                }
            ]
        },
        "usage": "Use to track local eval quality over time.",
    }


def _model_fixtures_payload() -> JsonObject:
    fixtures = _model_fixture_suite_names()
    return {
        "mode": "local_deterministic",
        "suite_count": len(fixtures),
        "suites": fixtures,
        "external_model_calls": False,
    }


def _model_fixture_suite_payload(fixture_suite: str) -> JsonObject:
    payload = get_model_response_dataset_payloads().get(fixture_suite, {})
    return {
        "mode": "local_deterministic",
        "fixture_suite": fixture_suite,
        "registered": fixture_suite in _model_fixture_suite_names(),
        "case_count": len(payload.get("cases", [])) if isinstance(payload, dict) else 0,
        "tags": payload.get("metadata", {}).get("tags", []) if isinstance(payload, dict) else [],
        "external_model_calls": False,
        "execution_enabled": False,
    }


def _eval_safety_boundaries_payload() -> JsonObject:
    return {
        "mode": "local_policy",
        "boundaries": [
            "Eval resources are metadata only.",
            "Suite execution must be started explicitly through existing eval commands.",
            "Model-response fixtures use saved local text only.",
            "No Procore or external model connectivity is used during discovery.",
        ],
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


def _plugin_extension_pack_template_payload() -> JsonObject:
    return {
        "mode": "local_template",
        "extension_pack": {
            "name": "example_extension_pack",
            "version": "0.1.0",
            "plugins": [],
            "capabilities": ["metadata_validation"],
            "requires_user_review": True,
        },
        "execution_enabled": False,
    }


def _plugin_scaffold_template_payload() -> JsonObject:
    return {
        "mode": "local_template",
        "scaffold": {
            "manifest_path": "plugin_manifest.json",
            "config_path": "plugin_config.json",
            "docs_path": "README.md",
            "tests_path": "tests/",
        },
        "notes": [
            "Scaffold metadata is descriptive only.",
            "MCP discovery does not create files or load plugin code.",
        ],
    }


def _plugin_safety_boundaries_payload() -> JsonObject:
    return {
        "mode": "local_policy",
        "boundaries": [
            "Plugins are not loaded or executed by MCP discovery.",
            "Plugin hooks are described but never invoked.",
            "Plugin configs must not contain credential values.",
        ],
    }


def _plugin_capabilities_payload() -> JsonObject:
    return {
        "mode": "metadata_only",
        "capabilities": [
            "manifest summaries",
            "hook metadata",
            "config templates",
            "extension pack templates",
            "scaffold templates",
            "local safety guidance",
        ],
        "execution_enabled": False,
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


def _async_resources_payload() -> JsonObject:
    return {
        "mode": "sdk_metadata",
        "resources": [
            "companies",
            "projects",
            "RFIs",
            "submittals",
            "drawings",
            "specifications",
            "documents",
            "photos",
            "daily logs",
            "directory",
            "financial read models",
        ],
    }


def _async_exports_payload() -> JsonObject:
    return {
        "mode": "sdk_metadata",
        "exports": [
            "JSON export",
            "JSONL export",
            "CSV export",
            "manifest-based local package export",
        ],
        "writes_local_files_only": True,
    }


def _async_batch_payload() -> JsonObject:
    return {
        "mode": "dry_run_friendly_metadata",
        "batch_patterns": [
            "multi-project read planning",
            "resource inventory planning",
            "attachment download planning",
            "local export manifest planning",
        ],
        "procore_write_actions_enabled": False,
    }


def _async_download_patterns_payload() -> JsonObject:
    return {
        "mode": "sdk_metadata",
        "patterns": [
            "streaming local download helpers",
            "safe filename handling",
            "skip-existing local file behavior",
            "retry-aware read operations",
        ],
    }


def _async_safety_boundaries_payload() -> JsonObject:
    return {
        "mode": "local_policy",
        "boundaries": [
            "Async discovery does not perform network work.",
            "Async helpers are intended for read-only retrieval and local exports.",
            "Credentials must be supplied through normal SDK configuration when helpers run.",
        ],
    }


def _async_read_only_coverage_payload() -> JsonObject:
    return {
        "mode": "sdk_metadata",
        "read_only_coverage": [
            "core resources",
            "project records",
            "attachments",
            "workflow package inputs",
            "agent registry metadata",
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


def _ai_workflow_resource_names() -> list[str]:
    return [
        "rfi-review",
        "submittal-review",
        "project-context-qa",
        "drawing-spec-comparison",
        "engineering-assistant",
        "field-issue-summary",
        "change-risk-review",
    ]


def _ai_workflow_review_payload(workflow_name: str) -> JsonObject:
    return {
        "mode": "metadata_only",
        "workflow": workflow_name,
        "inputs": [
            "local package manifest",
            "saved Procore resource JSON",
            "source labels",
            "human review question",
        ],
        "grounding_required": True,
        "external_model_calls": False,
        "notes": [
            "This is guidance for local AI-ready package review.",
            "MCP discovery does not run a model or call Procore.",
        ],
    }


def _ai_workflow_vector_export_payload() -> JsonObject:
    return {
        "mode": "metadata_only",
        "pattern": "Prepare local JSON/Markdown package outputs for a separate vector system.",
        "external_vector_database_calls": False,
        "recommended_fields": ["source_label", "resource_type", "project_id", "text", "metadata"],
    }


def _ai_workflow_model_fixture_evals_payload() -> JsonObject:
    return {
        "mode": "local_deterministic",
        "fixture_suites": _model_fixture_suite_names(),
        "usage": "Use saved model responses to check grounding, citation labels, and limits.",
    }


def _ai_workflow_safety_boundaries_payload() -> JsonObject:
    return {
        "mode": "local_policy",
        "boundaries": [
            "AI workflow resources are templates and package metadata only.",
            "No external model request is made during discovery.",
            "Outputs must cite local source labels and state limits.",
            "Human review is required before construction decisions.",
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


def _model_fixture_suite_names() -> list[str]:
    return sorted(get_model_response_dataset_payloads())


def _filter_resources(
    resources: list[McpResource],
    kind: McpResourceKind | str | None,
) -> list[McpResource]:
    if kind is None:
        return resources
    normalized = kind if isinstance(kind, McpResourceKind) else McpResourceKind(kind)
    return [resource for resource in resources if resource.kind == normalized]


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
