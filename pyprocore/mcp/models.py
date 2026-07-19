"""Typed models for discovery-only PyProcore MCP metadata."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import Field

from pyprocore.models.base import ProcoreModel


class McpResourceKind(str, Enum):
    """Supported local MCP resource categories."""

    AGENT_MANIFEST = "agent_manifest"
    AGENT_TOOL_SCHEMA = "agent_tool_schema"
    OPENAPI_SCHEMA = "openapi_schema"
    JSON_SCHEMA = "json_schema"
    EVAL_SUITE = "eval_suite"
    EVAL_REPORT = "eval_report"
    EVAL_BASELINE = "eval_baseline"
    EVAL_REGRESSION = "eval_regression"
    EVAL_HISTORY = "eval_history"
    MODEL_FIXTURE = "model_fixture"
    PLUGIN_MANIFEST = "plugin_manifest"
    PLUGIN_CONFIG = "plugin_config"
    PLUGIN_EXTENSION_PACK = "plugin_extension_pack"
    PLUGIN_SCAFFOLD = "plugin_scaffold"
    ASYNC_CAPABILITY = "async_capability"
    ASYNC_RESOURCE = "async_resource"
    ASYNC_EXPORT = "async_export"
    ASYNC_BATCH = "async_batch"
    ASYNC_DOWNLOAD_PATTERN = "async_download_pattern"
    AI_WORKFLOW_TEMPLATE = "ai_workflow_template"
    AI_WORKFLOW_REVIEW = "ai_workflow_review"
    SAFETY_BOUNDARY = "safety_boundary"
    DOCS_REFERENCE = "docs_reference"


class McpPromptKind(str, Enum):
    """Supported local MCP prompt template categories."""

    RFI_REVIEW = "rfi_review"
    SUBMITTAL_REVIEW = "submittal_review"
    PROJECT_CONTEXT_QA = "project_context_qa"
    DRAWING_SPEC_COMPARISON = "drawing_spec_comparison"
    ENGINEERING_ASSISTANT = "engineering_assistant"
    FIELD_ISSUE_SUMMARY = "field_issue_summary"
    CHANGE_RISK_REVIEW = "change_risk_review"
    ASYNC_EXPORT_PLANNING = "async_export_planning"
    PLUGIN_DEVELOPER = "plugin_developer"
    EVAL_REPORT_REVIEW = "eval_report_review"
    EVAL_REGRESSION_REVIEW = "eval_regression_review"
    MODEL_FIXTURE_REVIEW = "model_fixture_review"
    PLUGIN_CONFIG_REVIEW = "plugin_config_review"
    EXTENSION_PACK_REVIEW = "extension_pack_review"
    ASYNC_BATCH_PLAN_REVIEW = "async_batch_plan_review"
    ASYNC_EXPORT_MANIFEST_REVIEW = "async_export_manifest_review"
    AI_WORKFLOW_PACKAGE_REVIEW = "ai_workflow_package_review"
    MCP_SAFETY_REVIEW = "mcp_safety_review"
    RELEASE_READINESS_REVIEW = "release_readiness_review"
    SAFETY_BOUNDARY_REVIEW = "safety_boundary_review"


class McpSafetyBoundary(ProcoreModel):
    """Safety flags that apply to MCP discovery metadata."""

    discovery_only: bool = True
    mcp_execution_enabled: bool = False
    procore_tool_execution_enabled: bool = False
    procore_write_actions_enabled: bool = False
    calls_live_procore_api: bool = False
    calls_external_model_api: bool = False
    executes_plugins: bool = False
    fetches_remote_resources: bool = False
    uploads_remote_reports: bool = False
    requires_credentials: bool = False
    notes: list[str] = Field(default_factory=list)


class McpResource(ProcoreModel):
    """Metadata for one local discovery-only MCP resource."""

    uri: str
    name: str
    description: str
    kind: McpResourceKind
    mime_type: str = "application/json"
    tags: list[str] = Field(default_factory=list)
    safety: McpSafetyBoundary = Field(default_factory=McpSafetyBoundary)


class McpResourceTemplate(ProcoreModel):
    """Metadata for a local MCP resource template."""

    uri_template: str
    name: str
    description: str
    kind: McpResourceKind
    arguments: list[str] = Field(default_factory=list)
    mime_type: str = "application/json"
    safety: McpSafetyBoundary = Field(default_factory=McpSafetyBoundary)


class McpPromptArgument(ProcoreModel):
    """Argument accepted by a discovery-only MCP prompt template."""

    name: str
    description: str
    required: bool = False


class McpPrompt(ProcoreModel):
    """Metadata and text for one local MCP prompt template."""

    name: str
    title: str
    description: str
    kind: McpPromptKind
    template: str
    arguments: list[McpPromptArgument] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    safety: McpSafetyBoundary = Field(default_factory=McpSafetyBoundary)


class McpToolSummary(ProcoreModel):
    """Compact summary of registered agent tools exposed through MCP discovery."""

    total_tools: int
    execution_enabled: bool = False
    discovery_only: bool = True
    categories: dict[str, int] = Field(default_factory=dict)
    safety_levels: dict[str, int] = Field(default_factory=dict)


class McpCapabilitySummary(ProcoreModel):
    """High-level capability summary for the discovery-only MCP adapter."""

    server_name: str
    package_version: str
    protocol_version: str
    discovery_capabilities: list[str]
    supported_sdk_areas: list[str]
    resource_count: int
    prompt_count: int
    tool_summary: McpToolSummary
    async_coverage: list[str]
    plugin_metadata: list[str]
    eval_metadata: list[str]
    ai_workflow_templates: list[str]
    agent_metadata: dict[str, Any] = Field(default_factory=dict)
    mcp_resource_metadata: dict[str, Any] = Field(default_factory=dict)
    mcp_prompt_metadata: dict[str, Any] = Field(default_factory=dict)
    disabled_execution_status: dict[str, Any] = Field(default_factory=dict)
    baseline_regression_metadata: list[str] = Field(default_factory=list)
    model_fixture_metadata: list[str] = Field(default_factory=list)
    plugin_scaffold_metadata: list[str] = Field(default_factory=list)
    async_metadata: list[str] = Field(default_factory=list)
    ai_workflow_metadata: list[str] = Field(default_factory=list)
    safety_boundaries: list[str] = Field(default_factory=list)
    unsupported_actions: list[str] = Field(default_factory=list)
    safety: McpSafetyBoundary


class McpServerInfo(ProcoreModel):
    """Server metadata returned by discovery-only MCP initialize calls."""

    name: str
    title: str
    version: str
    protocol_version: str
    description: str
    registry_version: str
    tool_count: int
    capabilities: dict[str, Any]
    safety: McpSafetyBoundary


class McpDiscoveryManifest(ProcoreModel):
    """Complete JSON-serializable MCP discovery manifest."""

    server: McpServerInfo
    tools: list[dict[str, Any]]
    resources: list[McpResource]
    resource_templates: list[McpResourceTemplate] = Field(default_factory=list)
    prompts: list[McpPrompt]
    capabilities: McpCapabilitySummary
