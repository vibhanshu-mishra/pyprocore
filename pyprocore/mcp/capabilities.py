"""Capability summaries for discovery-only PyProcore MCP metadata."""

from __future__ import annotations

from collections import Counter

from pyprocore.agent.models import AgentToolRegistry
from pyprocore.agent.registry import get_agent_registry
from pyprocore.mcp.models import McpCapabilitySummary, McpSafetyBoundary, McpToolSummary
from pyprocore.mcp.prompts import list_mcp_prompts
from pyprocore.mcp.resources import list_mcp_resources


def build_mcp_tool_summary(registry: AgentToolRegistry | None = None) -> McpToolSummary:
    """Build a compact tool summary without enabling tool calls."""
    active_registry = registry or get_agent_registry()
    categories = Counter(tool.category.value for tool in active_registry.tools)
    safety_levels = Counter(tool.safety_level.value for tool in active_registry.tools)
    return McpToolSummary(
        total_tools=active_registry.tool_count,
        categories=dict(sorted(categories.items())),
        safety_levels=dict(sorted(safety_levels.items())),
    )


def build_mcp_capability_summary(
    registry: AgentToolRegistry | None = None,
) -> McpCapabilitySummary:
    """Build the high-level discovery-only MCP capability summary."""
    from pyprocore import __version__

    resources = list_mcp_resources()
    prompts = list_mcp_prompts()
    resource_kinds = Counter(resource.kind.value for resource in resources)
    prompt_kinds = Counter(prompt.kind.value for prompt in prompts)

    return McpCapabilitySummary(
        server_name="pyprocore-agent-mcp",
        package_version=__version__,
        protocol_version="2024-11-05",
        discovery_capabilities=[
            "tools/list",
            "resources/list",
            "resources/read",
            "prompts/list",
            "prompts/get",
            "initialize",
            "ping",
        ],
        supported_sdk_areas=[
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
            "workflows",
        ],
        resource_count=len(resources),
        prompt_count=len(prompts),
        tool_summary=build_mcp_tool_summary(registry),
        async_coverage=[
            "async client",
            "async pagination",
            "async downloads",
            "async multi-project exports",
            "async batch dry-run planning",
        ],
        plugin_metadata=[
            "metadata-only manifests",
            "safe config summaries",
            "hook metadata discovery",
            "scaffold templates",
        ],
        eval_metadata=[
            "agent eval suites",
            "golden datasets",
            "workflow evals",
            "offline model response fixtures",
            "baseline and regression reports",
        ],
        ai_workflow_templates=[
            "project context packages",
            "enhanced RFI packages",
            "enhanced submittal packages",
            "AI review exports",
            "AI prompt packs",
        ],
        agent_metadata={
            "registry_available": True,
            "tool_execution_enabled": False,
            "tool_metadata_only": True,
        },
        mcp_resource_metadata={
            "resource_kinds": dict(sorted(resource_kinds.items())),
            "supports_kind_filtering": True,
            "dynamic_templates": [
                "pyprocore://evals/suites/{suite_name}",
                "pyprocore://evals/model-fixtures/{fixture_suite}",
            ],
        },
        mcp_prompt_metadata={
            "prompt_kinds": dict(sorted(prompt_kinds.items())),
            "supports_kind_filtering": True,
        },
        disabled_execution_status={
            "mcp_tool_calls": False,
            "procore_tool_calls": False,
            "plugin_hooks": False,
            "external_model_calls": False,
            "remote_fetches": False,
            "remote_report_uploads": False,
        },
        baseline_regression_metadata=[
            "baseline templates",
            "regression templates",
            "history templates",
            "sample local eval report",
        ],
        model_fixture_metadata=[
            "offline model-response fixture suites",
            "grounding checks",
            "source-label checks",
            "safety-boundary checks",
        ],
        plugin_scaffold_metadata=[
            "plugin manifests",
            "hook metadata",
            "config templates",
            "extension pack templates",
            "scaffold templates",
        ],
        async_metadata=[
            "async read coverage",
            "async export metadata",
            "async batch planning metadata",
            "async download patterns",
        ],
        ai_workflow_metadata=[
            "RFI review packages",
            "submittal review packages",
            "project context Q&A packages",
            "drawing/spec comparison packages",
            "engineering assistant packages",
            "field issue summaries",
            "change risk reviews",
            "vector export patterns",
        ],
        safety_boundaries=[
            "discovery-only MCP",
            "no Procore writes",
            "no plugin execution",
            "no external model calls",
            "no remote resource fetch",
            "no remote report upload",
        ],
        unsupported_actions=[
            "approvals",
            "submissions",
            "record changes",
            "record removals",
            "remote file transfers",
            "money actions",
            "data mutation",
        ],
        safety=McpSafetyBoundary(
            notes=[
                "Execution is disabled.",
                "Discovery does not make live Procore calls.",
                "Discovery does not call external model APIs.",
                "Discovery does not execute plugins or MCP tools.",
            ]
        ),
    )
