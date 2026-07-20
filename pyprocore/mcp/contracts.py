"""Contract validation for PyProcore discovery-only MCP metadata."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, cast

from pydantic import Field

from pyprocore.mcp.models import (
    McpCapabilitySummary,
    McpDiscoveryManifest,
    McpPrompt,
    McpResource,
)
from pyprocore.models.base import ProcoreModel

CONTRACT_SCHEMA_VERSION = "mcp-contract-v1"
SECRET_MARKERS = (
    "access_token",
    "refresh_token",
    "client_secret",
    "authorization:",
)
DISABLED_STATUS_KEYS = (
    "mcp_tool_calls",
    "procore_tool_calls",
    "plugin_hooks",
    "external_model_calls",
    "remote_fetches",
    "remote_report_uploads",
)
SAFETY_FALSE_KEYS = (
    "mcp_execution_enabled",
    "procore_tool_execution_enabled",
    "procore_write_actions_enabled",
    "calls_live_procore_api",
    "calls_external_model_api",
    "executes_plugins",
    "fetches_remote_resources",
    "uploads_remote_reports",
)


class McpContractFinding(ProcoreModel):
    """One validation finding for a discovery-only MCP contract check."""

    code: str
    message: str
    severity: str = "error"
    path: str = ""


class McpContractValidationResult(ProcoreModel):
    """Result for one MCP contract validation area."""

    name: str
    passed: bool
    findings: list[McpContractFinding] = Field(default_factory=list)
    checked_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )


class McpDiscoveryContract(ProcoreModel):
    """Expected discovery-only MCP contract shape."""

    schema_version: str = CONTRACT_SCHEMA_VERSION
    discovery_only: bool = True
    disabled_execution_required: bool = True
    required_manifest_sections: list[str] = Field(
        default_factory=lambda: [
            "server",
            "tools",
            "resources",
            "resource_templates",
            "prompts",
            "capabilities",
        ]
    )
    required_capability_sections: list[str] = Field(
        default_factory=lambda: [
            "discovery_capabilities",
            "supported_sdk_areas",
            "disabled_execution_status",
            "unsupported_actions",
            "safety_boundaries",
            "safety",
        ]
    )
    required_disabled_status_keys: list[str] = Field(
        default_factory=lambda: list(DISABLED_STATUS_KEYS)
    )


class McpDisabledExecutionResponse(ProcoreModel):
    """Standard response returned when an MCP tool call is requested."""

    is_error: bool = True
    content: list[dict[str, str]]
    metadata: dict[str, Any]


class McpSampleRequest(ProcoreModel):
    """Safe sample request for MCP integrator fixtures."""

    method: str
    params: dict[str, Any] = Field(default_factory=dict)
    id: int | str | None = None
    jsonrpc: str = "2.0"


class McpSampleResponse(ProcoreModel):
    """Safe sample response for MCP integrator fixtures."""

    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    id: int | str | None = None
    jsonrpc: str = "2.0"


def validate_mcp_discovery_manifest(
    manifest: McpDiscoveryManifest | dict[str, Any] | None = None,
) -> McpContractValidationResult:
    """Validate that the full manifest exposes required discovery sections."""
    document = _manifest_dict(manifest)
    contract = McpDiscoveryContract()
    findings: list[McpContractFinding] = []

    for section in contract.required_manifest_sections:
        if section not in document:
            findings.append(_finding("missing_section", f"Missing manifest section: {section}"))

    if _contains_secret_marker(document):
        findings.append(_finding("secret_marker", "Manifest contains a protected secret marker."))

    server = document.get("server", {})
    safety = _get_nested(document, "capabilities", "safety") or server.get("safety", {})
    findings.extend(_safety_findings(safety, "manifest.capabilities.safety"))

    return _result("manifest", findings)


def validate_mcp_resource_manifest(
    resources: list[McpResource] | list[dict[str, Any]] | None = None,
) -> McpContractValidationResult:
    """Validate MCP resource metadata without reading remote data."""
    if resources is None:
        from pyprocore.mcp.resources import list_mcp_resources

        items = [item.model_dump(mode="json") for item in list_mcp_resources()]
    else:
        items = [_model_or_dict(item) for item in resources]

    findings: list[McpContractFinding] = []
    if not items:
        findings.append(_finding("empty_resources", "At least one MCP resource is required."))

    for index, item in enumerate(items):
        path = f"resources[{index}]"
        for field_name in ("uri", "name", "description", "kind"):
            if not item.get(field_name):
                findings.append(_finding("missing_resource_field", field_name, path))
        if _contains_secret_marker(item):
            findings.append(_finding("secret_marker", "Resource contains a secret marker.", path))
        findings.extend(_safety_findings(item.get("safety", {}), f"{path}.safety"))

    return _result("resources", findings)


def validate_mcp_prompt_manifest(
    prompts: list[McpPrompt] | list[dict[str, Any]] | None = None,
) -> McpContractValidationResult:
    """Validate MCP prompt templates as static local text."""
    if prompts is None:
        from pyprocore.mcp.prompts import list_mcp_prompts

        items = [item.model_dump(mode="json") for item in list_mcp_prompts()]
    else:
        items = [_model_or_dict(item) for item in prompts]

    findings: list[McpContractFinding] = []
    if not items:
        findings.append(_finding("empty_prompts", "At least one MCP prompt is required."))

    for index, item in enumerate(items):
        path = f"prompts[{index}]"
        for field_name in ("name", "description", "kind", "template"):
            if not item.get(field_name):
                findings.append(_finding("missing_prompt_field", field_name, path))
        template = str(item.get("template", "")).lower()
        if not any(marker in template for marker in ("ground", "cite", "source label")):
            findings.append(_finding("missing_grounding", "Prompt should mention grounding.", path))
        if _contains_secret_marker(item):
            findings.append(_finding("secret_marker", "Prompt contains a secret marker.", path))
        findings.extend(_safety_findings(item.get("safety", {}), f"{path}.safety"))

    return _result("prompts", findings)


def validate_mcp_capability_summary(
    capabilities: McpCapabilitySummary | dict[str, Any] | None = None,
) -> McpContractValidationResult:
    """Validate the capability summary safety and metadata sections."""
    if capabilities is None:
        from pyprocore.mcp.capabilities import build_mcp_capability_summary

        document = build_mcp_capability_summary().model_dump(mode="json")
    else:
        document = _model_or_dict(capabilities)

    contract = McpDiscoveryContract()
    findings: list[McpContractFinding] = []
    for section in contract.required_capability_sections:
        if section not in document:
            findings.append(_finding("missing_capability_section", section))

    disabled_status = document.get("disabled_execution_status", {})
    for key in contract.required_disabled_status_keys:
        if disabled_status.get(key) is not False:
            findings.append(
                _finding(
                    "disabled_status_not_false",
                    f"Disabled status must be false: {key}",
                    f"disabled_execution_status.{key}",
                )
            )

    tool_summary = document.get("tool_summary", {})
    if tool_summary.get("execution_enabled") is not False:
        findings.append(
            _finding(
                "tool_execution_not_disabled",
                "Tool summary must keep execution disabled.",
                "tool_summary.execution_enabled",
            )
        )
    if not document.get("unsupported_actions"):
        findings.append(
            _finding("missing_unsupported_actions", "Unsupported actions are required.")
        )
    if _contains_secret_marker(document):
        findings.append(_finding("secret_marker", "Capability summary contains a secret marker."))
    findings.extend(_safety_findings(document.get("safety", {}), "capabilities.safety"))

    return _result("capabilities", findings)


def validate_mcp_disabled_execution_contract(
    response: dict[str, Any] | McpDisabledExecutionResponse | None = None,
) -> McpContractValidationResult:
    """Validate the response shape used when execution is requested."""
    if response is None:
        from pyprocore.mcp.resources import disabled_mcp_execution_response

        document = disabled_mcp_execution_response("procore.example")
    else:
        document = _model_or_dict(response)

    findings: list[McpContractFinding] = []
    is_error = document.get("is_error", document.get("isError"))
    if is_error is not True:
        findings.append(_finding("disabled_response_not_error", "Response must be an error."))

    metadata = document.get("metadata", {})
    safety = document.get("safety", {})
    combined_safety = safety if safety else metadata
    for key in ("execution_enabled", "mcp_execution_enabled", "calls_live_api"):
        if metadata.get(key) is not False and key in metadata:
            findings.append(_finding("execution_flag_not_false", key, f"metadata.{key}"))
    findings.extend(_safety_findings(combined_safety, "disabled_response.safety"))

    if _contains_secret_marker(document):
        findings.append(
            _finding("secret_marker", "Disabled execution response contains a secret marker.")
        )
    return _result("disabled_execution", findings)


def validate_mcp_contracts(
    manifest: McpDiscoveryManifest | dict[str, Any] | None = None,
) -> list[McpContractValidationResult]:
    """Validate all discovery-only MCP contract areas."""
    document = _manifest_dict(manifest)
    return [
        validate_mcp_discovery_manifest(document),
        validate_mcp_resource_manifest(document.get("resources", [])),
        validate_mcp_prompt_manifest(document.get("prompts", [])),
        validate_mcp_capability_summary(document.get("capabilities", {})),
        validate_mcp_disabled_execution_contract(),
    ]


def build_mcp_contract_report(
    manifest: McpDiscoveryManifest | dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a JSON-serializable contract validation report."""
    results = validate_mcp_contracts(manifest)
    findings = [
        finding.model_dump(mode="json") for result in results for finding in result.findings
    ]
    return {
        "schema_version": CONTRACT_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "passed": all(result.passed for result in results),
        "results": [result.model_dump(mode="json") for result in results],
        "finding_count": len(findings),
        "findings": findings,
        "discovery_only": True,
        "execution_enabled": False,
    }


def _manifest_dict(
    manifest: McpDiscoveryManifest | dict[str, Any] | None,
) -> dict[str, Any]:
    if manifest is None:
        from pyprocore.mcp.discovery import build_mcp_discovery_manifest

        return build_mcp_discovery_manifest().model_dump(mode="json", by_alias=True)
    return _model_or_dict(manifest)


def _model_or_dict(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return cast(dict[str, Any], value.model_dump(mode="json", by_alias=True))
    return dict(value)


def _safety_findings(safety: dict[str, Any], path: str) -> list[McpContractFinding]:
    findings: list[McpContractFinding] = []
    if safety.get("discovery_only") is not True and "discovery_only" in safety:
        findings.append(_finding("not_discovery_only", "Discovery-only flag must be true.", path))
    for key in SAFETY_FALSE_KEYS:
        if safety.get(key) is not False and key in safety:
            findings.append(_finding("safety_flag_not_false", key, f"{path}.{key}"))
    return findings


def _contains_secret_marker(value: Any) -> bool:
    lowered = str(value).lower()
    return any(marker in lowered for marker in SECRET_MARKERS)


def _get_nested(document: dict[str, Any], *keys: str) -> dict[str, Any]:
    current: Any = document
    for key in keys:
        if not isinstance(current, dict):
            return {}
        current = current.get(key, {})
    return current if isinstance(current, dict) else {}


def _finding(code: str, message: str, path: str = "") -> McpContractFinding:
    return McpContractFinding(code=code, message=message, path=path)


def _result(name: str, findings: list[McpContractFinding]) -> McpContractValidationResult:
    return McpContractValidationResult(name=name, passed=not findings, findings=findings)
