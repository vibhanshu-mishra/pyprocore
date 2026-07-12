"""Local deterministic evaluation harness for PyProcore agent metadata.

The eval harness checks registry quality, schema shape, discovery exports,
run-log replay, redaction, and disabled-execution guarantees. It never loads
credentials, calls Procore, executes tools, or calls external AI/model APIs.
"""

from __future__ import annotations

import json
import tempfile
from collections.abc import Callable
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import Field

from pyprocore.agent.mcp import (
    build_mcp_resource_definitions,
    build_mcp_server_info,
    build_mcp_tool_definitions,
    build_mcp_tool_execution_disabled_response,
    export_mcp_manifest_json,
)
from pyprocore.agent.openapi import build_agent_openapi_spec
from pyprocore.agent.registry import get_agent_registry
from pyprocore.agent.runs import (
    append_agent_run_event,
    create_agent_run,
    redact_agent_event_payload,
    replay_agent_run,
)
from pyprocore.models.base import ProcoreModel

JsonObject = dict[str, Any]

BUILT_IN_AGENT_EVAL_SUITES = [
    "registry_safety",
    "schema_quality",
    "openapi_completeness",
    "mcp_discovery",
    "run_replay_safety",
    "redaction_safety",
    "execution_disabled",
]
DESTRUCTIVE_TERMS = ("create", "update", "delete", "remove", "patch")
DESTRUCTIVE_SIDE_EFFECT_TERMS = (
    "delete",
    "update",
    "remove",
    "patch",
    "mutate",
    "email",
    "send",
)


class AgentEvalSeverity(str, Enum):
    """Severity for one agent evaluation finding."""

    PASS = "pass"
    INFO = "info"
    WARNING = "warning"
    FAILURE = "failure"


class AgentEvalFinding(ProcoreModel):
    """One finding produced by an agent eval case."""

    severity: AgentEvalSeverity
    message: str
    case_id: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class AgentEvalCase(ProcoreModel):
    """Metadata for one deterministic agent eval case."""

    case_id: str
    suite_name: str
    description: str


class AgentEvalSuite(ProcoreModel):
    """Metadata for one built-in agent eval suite."""

    name: str
    description: str
    cases: list[AgentEvalCase] = Field(default_factory=list)


class AgentEvalCaseResult(ProcoreModel):
    """Result for one eval case."""

    case_id: str
    suite_name: str
    passed: bool
    findings: list[AgentEvalFinding] = Field(default_factory=list)


class AgentEvalResult(ProcoreModel):
    """Result for one complete eval suite."""

    suite_name: str
    passed: bool
    total_cases: int
    passed_cases: int
    failed_cases: int
    warnings: int
    findings: list[AgentEvalFinding] = Field(default_factory=list)
    cases: list[AgentEvalCaseResult] = Field(default_factory=list)
    created_at: datetime
    pyprocore_version: str


def list_agent_eval_suites() -> list[AgentEvalSuite]:
    """Return metadata for all built-in agent eval suites."""
    return [_build_suite(name) for name in BUILT_IN_AGENT_EVAL_SUITES]


def get_agent_eval_suite(name: str) -> AgentEvalSuite:
    """Return one built-in agent eval suite by name.

    Args:
        name: Suite name.

    Raises:
        ValueError: If the suite is not registered.

    Returns:
        Suite metadata.
    """
    if name not in BUILT_IN_AGENT_EVAL_SUITES:
        raise ValueError(f"Unknown agent eval suite: {name}")
    return _build_suite(name)


def run_agent_eval_suite(name: str) -> AgentEvalResult:
    """Run one built-in agent eval suite.

    Args:
        name: Suite name.

    Returns:
        Structured eval result.
    """
    suite = get_agent_eval_suite(name)
    runner = _suite_runners()[name]
    return _build_result(suite, runner())


def run_all_agent_eval_suites() -> list[AgentEvalResult]:
    """Run every built-in agent eval suite.

    Returns:
        Results sorted by suite name.
    """
    return [run_agent_eval_suite(name) for name in BUILT_IN_AGENT_EVAL_SUITES]


def export_agent_eval_results_json(
    results: list[AgentEvalResult] | AgentEvalResult | None = None,
    *,
    pretty: bool = False,
) -> str:
    """Serialize agent eval results as deterministic JSON.

    Args:
        results: Result or result list. When omitted, all suites are run.
        pretty: Whether to format JSON with two-space indentation.

    Returns:
        JSON string.
    """
    active_results: list[AgentEvalResult]
    if results is None:
        active_results = run_all_agent_eval_suites()
    elif isinstance(results, AgentEvalResult):
        active_results = [results]
    else:
        active_results = results
    payload = [result.model_dump(mode="json") for result in active_results]
    return json.dumps(payload, indent=2 if pretty else None, sort_keys=True)


def write_agent_eval_results(
    results: list[AgentEvalResult] | AgentEvalResult,
    output_path: Path | str,
    *,
    pretty: bool = True,
) -> Path:
    """Write agent eval results JSON to disk.

    Args:
        results: Result or result list to write.
        output_path: Destination path.
        pretty: Whether to pretty-print JSON.

    Returns:
        Written output path.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        export_agent_eval_results_json(results, pretty=pretty) + "\n",
        encoding="utf-8",
    )
    return path


def format_agent_eval_summary(results: list[AgentEvalResult] | AgentEvalResult) -> str:
    """Return a Markdown summary for agent eval results.

    Args:
        results: Result or result list.

    Returns:
        Markdown summary.
    """
    active_results = [results] if isinstance(results, AgentEvalResult) else results
    passed = sum(1 for result in active_results if result.passed)
    total = len(active_results)
    lines = [
        "# PyProcore Agent Eval Summary",
        "",
        f"Suites passed: {passed}/{total}",
        "",
        "| Suite | Passed | Cases | Warnings |",
        "| --- | --- | ---: | ---: |",
    ]
    for result in active_results:
        lines.append(
            f"| `{result.suite_name}` | {str(result.passed).lower()} | "
            f"{result.passed_cases}/{result.total_cases} | {result.warnings} |"
        )
    return "\n".join(lines) + "\n"


def _suite_runners() -> dict[str, Callable[[], list[AgentEvalCaseResult]]]:
    """Return eval suite runner functions."""
    return {
        "registry_safety": _run_registry_safety,
        "schema_quality": _run_schema_quality,
        "openapi_completeness": _run_openapi_completeness,
        "mcp_discovery": _run_mcp_discovery,
        "run_replay_safety": _run_run_replay_safety,
        "redaction_safety": _run_redaction_safety,
        "execution_disabled": _run_execution_disabled,
    }


def _build_suite(name: str) -> AgentEvalSuite:
    """Build suite metadata for a known suite."""
    descriptions = {
        "registry_safety": "Validate agent tool names, metadata, and safety flags.",
        "schema_quality": "Validate registered tool input and output schemas.",
        "openapi_completeness": "Validate local Agent API OpenAPI discovery coverage.",
        "mcp_discovery": "Validate discovery-only MCP metadata exports.",
        "run_replay_safety": "Validate local run-log replay without execution.",
        "redaction_safety": "Validate sensitive value redaction.",
        "execution_disabled": "Validate disabled execution guarantees.",
    }
    cases = [
        AgentEvalCase(case_id=case_id, suite_name=name, description=description)
        for case_id, description in _case_definitions()[name]
    ]
    return AgentEvalSuite(name=name, description=descriptions[name], cases=cases)


def _case_definitions() -> dict[str, list[tuple[str, str]]]:
    """Return case definitions for every suite."""
    return {
        "registry_safety": [
            ("tool_names_start_with_procore", "All registered tools use the procore. prefix."),
            ("tools_sorted_deterministically", "Registered tools are sorted by stable name."),
            ("tool_descriptions_present", "Every tool has a description."),
            ("tool_categories_present", "Every tool has a category."),
            ("tool_schemas_present", "Every tool has input and output schema metadata."),
            ("no_destructive_tools", "No destructive tool names or side effects are present."),
            ("safety_metadata_present", "Every tool declares safety metadata."),
        ],
        "schema_quality": [
            ("schemas_json_serializable", "All input and output schemas are JSON serializable."),
            ("required_fields_documented", "Required input fields appear in schema properties."),
            ("important_tools_have_input_properties", "Important tools expose input properties."),
        ],
        "openapi_completeness": [
            ("openapi_builds", "The OpenAPI document builds locally."),
            ("required_paths_present", "Required Agent API paths are present."),
            ("openapi_version_matches_package", "OpenAPI info version matches package version."),
        ],
        "mcp_discovery": [
            ("mcp_tools_build", "MCP tools build locally."),
            ("mcp_resources_build", "MCP resources build locally."),
            ("mcp_manifest_builds", "MCP manifest builds locally."),
            ("mcp_find_rfi_present", "MCP tools include procore.find_rfi."),
            ("mcp_call_disabled", "MCP tools/call response is disabled."),
            ("mcp_no_live_execution", "MCP metadata does not enable live execution."),
        ],
        "run_replay_safety": [
            ("synthetic_run_replay_passes", "Synthetic run logs replay successfully."),
            ("disabled_tool_event_stays_disabled", "Disabled tool-call events remain disabled."),
        ],
        "redaction_safety": [
            ("sensitive_values_redacted", "Sensitive event values are redacted."),
        ],
        "execution_disabled": [
            ("mcp_execution_disabled", "MCP execution-disabled response is explicit."),
            ("agent_registry_has_no_enabled_execution", "Registry exposes metadata only."),
        ],
    }


def _build_result(
    suite: AgentEvalSuite,
    case_results: list[AgentEvalCaseResult],
) -> AgentEvalResult:
    """Build a suite result from case results."""
    from pyprocore import __version__

    findings = [finding for case in case_results for finding in case.findings]
    failed_cases = sum(1 for case in case_results if not case.passed)
    warning_count = sum(1 for finding in findings if finding.severity == AgentEvalSeverity.WARNING)
    return AgentEvalResult(
        suite_name=suite.name,
        passed=failed_cases == 0,
        total_cases=len(case_results),
        passed_cases=len(case_results) - failed_cases,
        failed_cases=failed_cases,
        warnings=warning_count,
        findings=findings,
        cases=case_results,
        created_at=datetime.now(timezone.utc),
        pyprocore_version=__version__,
    )


def _case_result(
    suite_name: str,
    case_id: str,
    passed: bool,
    message: str,
    *,
    details: dict[str, Any] | None = None,
    severity: AgentEvalSeverity | None = None,
) -> AgentEvalCaseResult:
    """Create one case result."""
    finding_severity = severity or (AgentEvalSeverity.PASS if passed else AgentEvalSeverity.FAILURE)
    return AgentEvalCaseResult(
        case_id=case_id,
        suite_name=suite_name,
        passed=passed,
        findings=[
            AgentEvalFinding(
                severity=finding_severity,
                message=message,
                case_id=case_id,
                details=details or {},
            )
        ],
    )


def _run_registry_safety() -> list[AgentEvalCaseResult]:
    """Run registry safety checks."""
    suite = "registry_safety"
    tools = get_agent_registry().tools
    names = [tool.name for tool in tools]
    destructive_names = [
        name
        for name in names
        if any(term in name.lower().split(".")[-1] for term in DESTRUCTIVE_TERMS)
    ]
    destructive_side_effects = [
        tool.name
        for tool in tools
        if any(
            term in " ".join(tool.side_effects).lower() for term in DESTRUCTIVE_SIDE_EFFECT_TERMS
        )
    ]
    return [
        _case_result(
            suite,
            "tool_names_start_with_procore",
            all(name.startswith("procore.") for name in names),
            "All tool names use the procore. prefix.",
        ),
        _case_result(
            suite,
            "tools_sorted_deterministically",
            names == sorted(names),
            "Tools are sorted deterministically.",
        ),
        _case_result(
            suite,
            "tool_descriptions_present",
            all(bool(tool.description.strip()) for tool in tools),
            "Every tool has a description.",
        ),
        _case_result(
            suite,
            "tool_categories_present",
            all(bool(tool.category.value) for tool in tools),
            "Every tool has a category.",
        ),
        _case_result(
            suite,
            "tool_schemas_present",
            all(tool.input_schema and tool.output_schema for tool in tools),
            "Every tool has input and output schema metadata.",
        ),
        _case_result(
            suite,
            "no_destructive_tools",
            not destructive_names and not destructive_side_effects,
            "No destructive tool names or side effects were found.",
            details={
                "destructive_names": destructive_names,
                "destructive_side_effects": destructive_side_effects,
            },
        ),
        _case_result(
            suite,
            "safety_metadata_present",
            all(tool.safety_level.value and isinstance(tool.requires_auth, bool) for tool in tools),
            "Every tool declares safety metadata.",
        ),
    ]


def _run_schema_quality() -> list[AgentEvalCaseResult]:
    """Run schema quality checks."""
    suite = "schema_quality"
    tools = get_agent_registry().tools
    serializable = True
    for tool in tools:
        try:
            json.dumps(tool.input_schema, sort_keys=True)
            json.dumps(tool.output_schema, sort_keys=True)
        except TypeError:
            serializable = False
            break

    required_fields_valid = all(
        set(tool.input_schema.get("required", [])).issubset(
            set(tool.input_schema.get("properties", {}).keys())
        )
        for tool in tools
    )
    important_names = {
        "procore.find_rfi",
        "procore.get_rfi",
        "procore.list_rfis",
        "procore.find_submittal",
        "procore.list_projects",
    }
    important_tools_ok = all(
        bool(tool.input_schema.get("properties")) for tool in tools if tool.name in important_names
    )
    return [
        _case_result(
            suite,
            "schemas_json_serializable",
            serializable,
            "All tool schemas are JSON serializable.",
        ),
        _case_result(
            suite,
            "required_fields_documented",
            required_fields_valid,
            "Required input fields are present in schema properties.",
        ),
        _case_result(
            suite,
            "important_tools_have_input_properties",
            important_tools_ok,
            "Important tools expose input properties.",
        ),
    ]


def _run_openapi_completeness() -> list[AgentEvalCaseResult]:
    """Run OpenAPI completeness checks."""
    from pyprocore import __version__

    suite = "openapi_completeness"
    spec = build_agent_openapi_spec()
    paths = spec.get("paths", {})
    required_paths = {
        "/health",
        "/agent/manifest",
        "/agent/tools",
        "/agent/tools/{tool_name}",
        "/agent/openapi.json",
        "/agent/schemas",
        "/agent/tools/{tool_name}/call",
    }
    return [
        _case_result(suite, "openapi_builds", bool(spec.get("openapi")), "OpenAPI spec builds."),
        _case_result(
            suite,
            "required_paths_present",
            required_paths.issubset(set(paths.keys())),
            "Required Agent API paths are present.",
            details={"missing_paths": sorted(required_paths - set(paths.keys()))},
        ),
        _case_result(
            suite,
            "openapi_version_matches_package",
            spec.get("info", {}).get("version") == __version__,
            "OpenAPI info version matches package version.",
        ),
    ]


def _run_mcp_discovery() -> list[AgentEvalCaseResult]:
    """Run MCP discovery checks."""
    suite = "mcp_discovery"
    tools = build_mcp_tool_definitions()
    resources = build_mcp_resource_definitions()
    manifest = json.loads(export_mcp_manifest_json())
    disabled = build_mcp_tool_execution_disabled_response("procore.find_rfi")
    return [
        _case_result(suite, "mcp_tools_build", bool(tools), "MCP tools build locally."),
        _case_result(
            suite,
            "mcp_resources_build",
            {item["uri"] for item in resources}
            >= {
                "pyprocore://agent/manifest",
                "pyprocore://agent/openapi",
                "pyprocore://agent/schemas",
            },
            "MCP resources include manifest, OpenAPI, and schemas.",
        ),
        _case_result(
            suite,
            "mcp_manifest_builds",
            manifest.get("server", {}).get("name") == "pyprocore-agent-mcp",
            "MCP manifest builds locally.",
        ),
        _case_result(
            suite,
            "mcp_find_rfi_present",
            any(tool["name"] == "procore.find_rfi" for tool in tools),
            "MCP tools include procore.find_rfi.",
        ),
        _case_result(
            suite,
            "mcp_call_disabled",
            disabled.get("isError") is True
            and disabled.get("metadata", {}).get("execution_enabled") is False,
            "MCP tools/call returns a disabled execution response.",
        ),
        _case_result(
            suite,
            "mcp_no_live_execution",
            manifest.get("server", {}).get("safety", {}).get("tool_execution_enabled") is False
            and manifest.get("server", {}).get("safety", {}).get("calls_live_procore_api") is False,
            "MCP metadata does not enable live execution.",
        ),
    ]


def _run_run_replay_safety() -> list[AgentEvalCaseResult]:
    """Run synthetic run replay checks."""
    suite = "run_replay_safety"
    with tempfile.TemporaryDirectory() as temp_dir:
        run = create_agent_run(temp_dir, run_id="eval-run", source="agent-eval")
        append_agent_run_event(
            temp_dir,
            run.run_id,
            method="GET",
            path="/health",
            status_code=200,
            event_type="health",
            response_summary={"status": "ok"},
        )
        append_agent_run_event(
            temp_dir,
            run.run_id,
            method="POST",
            path="/agent/tools/procore.find_rfi/call",
            tool_name="procore.find_rfi",
            status_code=501,
            event_type="tool_execution_disabled",
            response_summary={"error": "tool_execution_disabled"},
            error_type="tool_execution_disabled",
        )
        replay = replay_agent_run(temp_dir, run.run_id)
    disabled_event_ok = any(
        event.path == "/agent/tools/procore.find_rfi/call" and event.passed
        for event in replay.events
    )
    return [
        _case_result(
            suite,
            "synthetic_run_replay_passes",
            replay.passed,
            "Synthetic run replay passed.",
            details={"warnings": replay.warnings, "errors": replay.errors},
        ),
        _case_result(
            suite,
            "disabled_tool_event_stays_disabled",
            disabled_event_ok,
            "Disabled tool-call event stayed disabled during replay.",
        ),
    ]


def _run_redaction_safety() -> list[AgentEvalCaseResult]:
    """Run sensitive-data redaction checks."""
    suite = "redaction_safety"
    raw_values = ["Bearer raw-token", "client-secret", "access-token", "refresh-token"]
    payload = {
        "Authorization": raw_values[0],
        "client_secret": raw_values[1],
        "nested": {"access_token": raw_values[2], "refresh_token": raw_values[3]},
    }
    redacted = redact_agent_event_payload(payload)
    encoded = json.dumps(redacted, sort_keys=True)
    return [
        _case_result(
            suite,
            "sensitive_values_redacted",
            not any(value in encoded for value in raw_values),
            "Sensitive sample values were redacted.",
        )
    ]


def _run_execution_disabled() -> list[AgentEvalCaseResult]:
    """Run disabled execution checks."""
    suite = "execution_disabled"
    disabled = build_mcp_tool_execution_disabled_response("procore.find_rfi")
    registry_metadata_only = all(
        not any(term in tool.name for term in DESTRUCTIVE_TERMS)
        for tool in get_agent_registry().tools
    )
    return [
        _case_result(
            suite,
            "mcp_execution_disabled",
            disabled.get("metadata", {}).get("execution_enabled") is False
            and "no Procore API call was made" in disabled["content"][0]["text"],
            "MCP execution-disabled response confirms no execution.",
        ),
        _case_result(
            suite,
            "agent_registry_has_no_enabled_execution",
            registry_metadata_only
            and build_mcp_server_info()["safety"]["tool_execution_enabled"] is False,
            "Agent registry and MCP server info keep execution disabled.",
        ),
    ]
