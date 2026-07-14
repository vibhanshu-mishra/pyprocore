"""Command-line entrypoint for Procore SDK operations."""

from __future__ import annotations

import argparse
import json
from ipaddress import ip_address
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel

from pyprocore import __version__
from pyprocore.agent import (
    AgentEvalResult,
    AgentEvalSuite,
    AgentManifest,
    AgentReplayResult,
    AgentRun,
    AgentTool,
    AgentToolNotFoundError,
    build_agent_manifest,
    export_agent_eval_results_json,
    export_agent_openapi_json,
    export_agent_openapi_yaml,
    export_agent_run_bundle,
    export_agent_tool_schemas_json,
    export_mcp_manifest_json,
    export_mcp_prompts_json,
    export_mcp_resources_json,
    export_mcp_tools_json,
    format_agent_eval_summary,
    get_agent_eval_suite,
    get_agent_tool,
    list_agent_eval_suites,
    list_agent_runs,
    list_agent_tools,
    load_agent_run,
    replay_agent_run,
    run_agent_api_server,
    run_agent_eval_suite,
    run_all_agent_eval_suites,
    run_mcp_stdio_server,
    write_agent_eval_results,
)
from pyprocore.auth.diagnostics import (
    AuthClientCredentialsResult,
    AuthExchangeResult,
    AuthLoginUrlResult,
    AuthRefreshResult,
    AuthStatusReport,
    build_authorization_url,
    exchange_code_and_save,
    format_auth_exchange,
    format_auth_refresh,
    format_auth_status,
    format_client_credentials_result,
    format_login_url,
    get_auth_status,
    refresh_auth_token,
    request_client_credentials_token_and_save,
)
from pyprocore.automation import AutomationInput, build_workflow_package
from pyprocore.core.config import get_settings
from pyprocore.core.doctor import DoctorReport, format_doctor_report, run_doctor
from pyprocore.core.exceptions import (
    AuthorizationError,
    ConfigurationError,
    ProcoreAPIError,
    ResourceNotFoundError,
    ValidationError,
)
from pyprocore.services import (
    download_document,
    download_drawing,
    download_photo,
    download_photo_album,
    download_rfi_attachments,
    download_specification_section_revision,
    download_submittal_attachments,
    find_company,
    find_correspondence,
    find_document,
    find_document_folder,
    find_drawing,
    find_drawings_contains,
    find_incident,
    find_inspection,
    find_meeting,
    find_observation,
    find_photo,
    find_photo_album,
    find_project,
    find_punch_item,
    find_rfi,
    find_specification_section,
    find_submittal,
    get_correspondence,
    get_daily_log,
    get_daily_log_counts,
    get_daily_log_header,
    get_document,
    get_document_folder,
    get_drawing,
    get_drawing_area,
    get_generic_tool,
    get_incident,
    get_inspection,
    get_meeting,
    get_observation,
    get_photo,
    get_photo_album,
    get_project_incident_configuration,
    get_punch_item,
    get_rfi,
    get_specification_section,
    get_specification_section_revision,
    get_submittal,
    list_accident_logs,
    list_call_logs,
    list_companies,
    list_correspondences,
    list_daily_construction_report_logs,
    list_daily_log_headers,
    list_daily_logs,
    list_daily_logs_for_date,
    list_delay_log_types,
    list_delay_logs,
    list_delivery_logs,
    list_document_folders,
    list_documents,
    list_drawing_areas,
    list_drawing_disciplines,
    list_drawings,
    list_dumpster_logs,
    list_generic_tools,
    list_incidents,
    list_inspections,
    list_manpower_logs,
    list_meetings,
    list_notes_logs,
    list_observations,
    list_photo_albums,
    list_photos,
    list_plan_revision_logs,
    list_productivity_logs,
    list_projects,
    list_punch_items,
    list_rfis,
    list_specification_section_revisions,
    list_specification_sections,
    list_specification_sets,
    list_submittals,
    list_visitor_logs,
)
from pyprocore.webhooks import (
    WebhookDispatchResult,
    WebhookEvent,
    WebhookEventStoreResult,
    dispatch_webhook_event,
    list_webhook_events,
    load_webhook_event,
    save_webhook_event,
)
from pyprocore.workflows import (
    AIExportResult,
    EnhancedRFIPackageResult,
    EnhancedSubmittalPackageResult,
    ProjectContextResult,
    ProjectSyncResult,
    SyncResult,
    WorkflowPlan,
    WorkflowRunResult,
    build_ai_prompt_pack,
    build_ai_review_export,
    build_enhanced_rfi_package,
    build_enhanced_submittal_package,
    build_project_context_package,
    export_correspondences_to_csv,
    export_incidents_to_csv,
    export_inspections_to_csv,
    export_meetings_to_csv,
    export_observations_to_csv,
    export_punch_items_to_csv,
    export_rfis_to_csv,
    export_submittals_to_csv,
    list_available_workflows,
    load_workflow_plan,
    run_workflow_plan,
    sync_documents_to_folder,
    sync_project_to_folder,
    sync_rfis_to_folder,
    sync_submittals_to_folder,
    validate_workflow_plan,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description="Procore SDK utility commands")
    parser.add_argument("--version", action="version", version=f"pyprocore {__version__}")
    subcommands = parser.add_subparsers(dest="command", required=True)

    doctor_parser = subcommands.add_parser("doctor", help="Check local SDK setup")
    doctor_parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Print structured JSON output",
    )
    doctor_parser.add_argument(
        "--live",
        action="store_true",
        help="Run one authenticated Procore API check",
    )

    auth_parser = subcommands.add_parser("auth", help="Authentication helper commands")
    auth_subcommands = auth_parser.add_subparsers(dest="auth_command", required=True)

    auth_status_parser = auth_subcommands.add_parser("status", help="Show local auth status")
    auth_status_parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Print structured JSON output",
    )

    auth_subcommands.add_parser("refresh", help="Refresh the stored access token")
    auth_subcommands.add_parser("login-url", help="Print the OAuth authorization URL")
    client_credentials_parser = auth_subcommands.add_parser(
        "client-credentials-token",
        aliases=["service-token"],
        help="Request and save a client credentials access token",
    )
    client_credentials_parser.set_defaults(auth_command="client-credentials-token")
    auth_exchange_parser = auth_subcommands.add_parser(
        "exchange-code",
        aliases=["exchange"],
        help="Exchange an OAuth authorization code and save tokens",
    )
    auth_exchange_parser.set_defaults(auth_command="exchange-code")
    auth_exchange_parser.add_argument("code", help="Authorization code returned by Procore")

    agent_parser = subcommands.add_parser("agent", help="Inspect the local agent tool registry")
    agent_subcommands = agent_parser.add_subparsers(dest="agent_command", required=True)

    agent_manifest_parser = agent_subcommands.add_parser(
        "manifest",
        help="Show agent tool manifest metadata",
    )
    agent_manifest_parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Print structured JSON output",
    )
    agent_manifest_parser.add_argument(
        "--pretty",
        action="store_true",
        help="Print pretty JSON output",
    )

    agent_tools_parser = agent_subcommands.add_parser("tools", help="List registered agent tools")
    agent_tools_parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Print structured JSON output",
    )
    agent_tools_parser.add_argument(
        "--pretty",
        action="store_true",
        help="Print pretty JSON output",
    )

    agent_tool_parser = agent_subcommands.add_parser(
        "tool",
        help="Show metadata for one registered agent tool",
    )
    agent_tool_parser.add_argument("tool_name")
    agent_tool_parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Print structured JSON output",
    )
    agent_tool_parser.add_argument(
        "--pretty",
        action="store_true",
        help="Print pretty JSON output",
    )

    agent_openapi_parser = agent_subcommands.add_parser(
        "openapi",
        help="Export the local Agent API OpenAPI document",
    )
    agent_openapi_format = agent_openapi_parser.add_mutually_exclusive_group()
    agent_openapi_format.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Print JSON output. This is the default.",
    )
    agent_openapi_format.add_argument(
        "--yaml",
        action="store_true",
        help="Print YAML output using PyProcore's built-in minimal emitter.",
    )
    agent_openapi_parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write the OpenAPI document to this path.",
    )
    agent_openapi_parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )

    agent_schemas_parser = agent_subcommands.add_parser(
        "schemas",
        help="Export JSON schemas for agent models and registered tools",
    )
    agent_schemas_parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Print JSON output. This is the default.",
    )
    agent_schemas_parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write the schema export to this path.",
    )
    agent_schemas_parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )

    agent_serve_parser = agent_subcommands.add_parser(
        "serve",
        help="Run the local agent discovery API server",
    )
    agent_serve_parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bind host. Defaults to 127.0.0.1 for local-only access.",
    )
    agent_serve_parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Bind port. Defaults to 8765.",
    )
    agent_serve_parser.add_argument(
        "--allow-public-bind",
        action="store_true",
        help="Allow binding outside 127.0.0.1 when you intentionally want that.",
    )
    agent_serve_parser.add_argument(
        "--run-log-dir",
        type=Path,
        default=None,
        help="Opt in to local Agent API run logging under this directory.",
    )
    agent_serve_parser.add_argument(
        "--run-id",
        default=None,
        help="Optional run ID to use when --run-log-dir is enabled.",
    )

    agent_runs_parser = agent_subcommands.add_parser(
        "runs",
        help="Inspect and replay local Agent API run logs",
    )
    agent_runs_subcommands = agent_runs_parser.add_subparsers(
        dest="agent_runs_command",
        required=True,
    )
    agent_runs_list_parser = agent_runs_subcommands.add_parser(
        "list",
        help="List local Agent API runs",
    )
    agent_runs_list_parser.add_argument("--run-log-dir", type=Path, required=True)
    agent_runs_list_parser.add_argument("--json", dest="json_output", action="store_true")
    agent_runs_list_parser.add_argument("--pretty", action="store_true")

    agent_runs_show_parser = agent_runs_subcommands.add_parser(
        "show",
        help="Show one local Agent API run",
    )
    agent_runs_show_parser.add_argument("run_id")
    agent_runs_show_parser.add_argument("--run-log-dir", type=Path, required=True)
    agent_runs_show_parser.add_argument("--json", dest="json_output", action="store_true")
    agent_runs_show_parser.add_argument("--pretty", action="store_true")

    agent_runs_replay_parser = agent_runs_subcommands.add_parser(
        "replay",
        help="Replay one local Agent API run without executing tools",
    )
    agent_runs_replay_parser.add_argument("run_id")
    agent_runs_replay_parser.add_argument("--run-log-dir", type=Path, required=True)
    agent_runs_replay_parser.add_argument("--json", dest="json_output", action="store_true")
    agent_runs_replay_parser.add_argument("--pretty", action="store_true")

    agent_runs_export_parser = agent_runs_subcommands.add_parser(
        "export",
        help="Export one local Agent API run bundle",
    )
    agent_runs_export_parser.add_argument("run_id")
    agent_runs_export_parser.add_argument("--run-log-dir", type=Path, required=True)
    agent_runs_export_parser.add_argument("--output-dir", type=Path, required=True)
    agent_runs_export_parser.add_argument("--json", dest="json_output", action="store_true")

    agent_mcp_parser = agent_subcommands.add_parser(
        "mcp",
        help="Export discovery-only MCP adapter metadata",
    )
    agent_mcp_subcommands = agent_mcp_parser.add_subparsers(
        dest="agent_mcp_command",
        required=True,
    )

    agent_mcp_tools_parser = agent_mcp_subcommands.add_parser(
        "tools",
        help="Export MCP-style tool definitions",
    )
    agent_mcp_tools_parser.add_argument("--json", dest="json_output", action="store_true")
    agent_mcp_tools_parser.add_argument("--pretty", action="store_true")
    agent_mcp_tools_parser.add_argument("--output", type=Path, default=None)

    agent_mcp_resources_parser = agent_mcp_subcommands.add_parser(
        "resources",
        help="Export MCP-style resource definitions",
    )
    agent_mcp_resources_parser.add_argument("--json", dest="json_output", action="store_true")
    agent_mcp_resources_parser.add_argument("--pretty", action="store_true")
    agent_mcp_resources_parser.add_argument("--output", type=Path, default=None)

    agent_mcp_prompts_parser = agent_mcp_subcommands.add_parser(
        "prompts",
        help="Export MCP-style prompt definitions",
    )
    agent_mcp_prompts_parser.add_argument("--json", dest="json_output", action="store_true")
    agent_mcp_prompts_parser.add_argument("--pretty", action="store_true")
    agent_mcp_prompts_parser.add_argument("--output", type=Path, default=None)

    agent_mcp_manifest_parser = agent_mcp_subcommands.add_parser(
        "manifest",
        help="Export the discovery-only MCP manifest",
    )
    agent_mcp_manifest_parser.add_argument("--json", dest="json_output", action="store_true")
    agent_mcp_manifest_parser.add_argument("--pretty", action="store_true")
    agent_mcp_manifest_parser.add_argument("--output", type=Path, default=None)

    agent_mcp_subcommands.add_parser(
        "stdio",
        help="Run the experimental discovery-only MCP stdio adapter",
    )

    agent_evals_parser = agent_subcommands.add_parser(
        "evals",
        help="Run local deterministic agent safety evals",
    )
    agent_evals_subcommands = agent_evals_parser.add_subparsers(
        dest="agent_evals_command",
        required=True,
    )

    agent_evals_list_parser = agent_evals_subcommands.add_parser(
        "list",
        help="List built-in agent eval suites",
    )
    agent_evals_list_parser.add_argument("--json", dest="json_output", action="store_true")
    agent_evals_list_parser.add_argument("--pretty", action="store_true")

    agent_evals_show_parser = agent_evals_subcommands.add_parser(
        "show",
        help="Show one built-in agent eval suite",
    )
    agent_evals_show_parser.add_argument("suite_name")
    agent_evals_show_parser.add_argument("--json", dest="json_output", action="store_true")
    agent_evals_show_parser.add_argument("--pretty", action="store_true")

    agent_evals_run_parser = agent_evals_subcommands.add_parser(
        "run",
        help="Run all agent eval suites or one named suite",
    )
    agent_evals_run_parser.add_argument("suite_name", nargs="?")
    agent_evals_run_parser.add_argument("--json", dest="json_output", action="store_true")
    agent_evals_run_parser.add_argument("--pretty", action="store_true")
    agent_evals_run_parser.add_argument("--output", type=Path, default=None)
    agent_evals_run_parser.add_argument(
        "--fail-on-warning",
        action="store_true",
        help="Exit nonzero when eval warnings are present",
    )

    subcommands.add_parser("companies", help="List companies")

    find_company_parser = subcommands.add_parser("find-company", help="Find one company")
    find_company_parser.add_argument("name")

    projects_parser = subcommands.add_parser("projects", help="List projects")
    projects_parser.add_argument("--company-id", type=int, default=None)

    find_project_parser = subcommands.add_parser("find-project", help="Find one project")
    find_project_parser.add_argument("query", nargs="?")
    find_project_parser.add_argument("--number", default=None)
    find_project_parser.add_argument("--company-id", type=int, default=None)

    rfis_parser = subcommands.add_parser("rfis", help="List RFIs for a project")
    rfis_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    _add_filter_options(rfis_parser)

    rfi_parser = subcommands.add_parser("rfi", help="Get one RFI")
    rfi_parser.add_argument("--project", "--project-id", dest="project_id", type=int, required=True)
    rfi_parser.add_argument("--id", "--rfi-id", dest="rfi_id", type=int, required=True)

    find_rfi_parser = subcommands.add_parser("find-rfi", help="Find one RFI by number")
    find_rfi_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    find_rfi_parser.add_argument("--number", required=True)

    rfi_download_parser = _add_alias_parser(
        subcommands,
        "download-rfi",
        ["download-rfi-attachments"],
        "download-rfi-attachments",
        help="Download RFI attachments",
    )
    rfi_download_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    rfi_download_parser.add_argument("--id", "--rfi-id", dest="rfi_id", type=int, required=True)
    rfi_download_parser.add_argument("--destination-dir", type=Path, default=None)

    submittals_parser = subcommands.add_parser(
        "submittals",
        help="List submittals for a project",
    )
    submittals_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    _add_filter_options(submittals_parser)

    submittal_parser = subcommands.add_parser("submittal", help="Get one submittal")
    submittal_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    submittal_parser.add_argument(
        "--id", "--submittal-id", dest="submittal_id", type=int, required=True
    )

    find_submittal_parser = subcommands.add_parser(
        "find-submittal",
        help="Find one submittal by number",
    )
    find_submittal_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    find_submittal_parser.add_argument("--number", required=True)

    submittal_download_parser = _add_alias_parser(
        subcommands,
        "download-submittal",
        ["download-submittal-attachments"],
        "download-submittal-attachments",
        help="Download submittal attachments",
    )
    submittal_download_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    submittal_download_parser.add_argument(
        "--id", "--submittal-id", dest="submittal_id", type=int, required=True
    )
    submittal_download_parser.add_argument("--destination-dir", type=Path, default=None)

    observations_parser = subcommands.add_parser(
        "observations",
        help="List observation items for a project",
    )
    _add_project_company_options(observations_parser)
    _add_filter_options(observations_parser)

    observation_parser = subcommands.add_parser("observation", help="Get one observation item")
    _add_project_company_options(observation_parser)
    observation_parser.add_argument(
        "--id",
        "--observation-id",
        dest="observation_id",
        type=int,
        required=True,
    )

    find_observation_parser = subcommands.add_parser(
        "find-observation",
        help="Find one observation by number, title, or text",
    )
    _add_project_company_options(find_observation_parser)
    _add_number_title_query_options(find_observation_parser)

    punch_items_parser = subcommands.add_parser(
        "punch-items",
        help="List punch items for a project",
    )
    _add_project_company_options(punch_items_parser)
    _add_filter_options(punch_items_parser)

    punch_item_parser = subcommands.add_parser("punch-item", help="Get one punch item")
    _add_project_company_options(punch_item_parser)
    punch_item_parser.add_argument(
        "--id",
        "--punch-item-id",
        dest="punch_item_id",
        type=int,
        required=True,
    )

    find_punch_item_parser = subcommands.add_parser(
        "find-punch-item",
        help="Find one punch item by number, title, or text",
    )
    _add_project_company_options(find_punch_item_parser)
    _add_number_title_query_options(find_punch_item_parser)

    generic_tools_parser = subcommands.add_parser(
        "generic-tools",
        help="List Generic Tools for a project",
    )
    _add_project_company_options(generic_tools_parser)

    generic_tool_parser = subcommands.add_parser("generic-tool", help="Get one Generic Tool")
    _add_project_company_options(generic_tool_parser)
    generic_tool_parser.add_argument(
        "--id",
        "--generic-tool-id",
        dest="generic_tool_id",
        type=int,
        required=True,
    )

    correspondences_parser = subcommands.add_parser(
        "correspondences",
        help="List correspondence items for a Generic Tool",
    )
    _add_project_company_options(correspondences_parser)
    correspondences_parser.add_argument(
        "--generic-tool",
        "--generic-tool-id",
        dest="generic_tool_id",
        type=int,
        required=True,
    )
    _add_filter_options(correspondences_parser)

    correspondence_parser = subcommands.add_parser(
        "correspondence",
        help="Get one correspondence item",
    )
    _add_project_company_options(correspondence_parser)
    correspondence_parser.add_argument(
        "--id",
        "--correspondence-id",
        dest="correspondence_id",
        type=int,
        required=True,
    )

    find_correspondence_parser = subcommands.add_parser(
        "find-correspondence",
        help="Find one correspondence by number, title, subject, or text",
    )
    _add_project_company_options(find_correspondence_parser)
    find_correspondence_parser.add_argument(
        "--generic-tool",
        "--generic-tool-id",
        dest="generic_tool_id",
        type=int,
        required=True,
    )
    _add_number_title_query_options(find_correspondence_parser)

    meetings_parser = subcommands.add_parser("meetings", help="List meetings for a project")
    _add_project_company_options(meetings_parser)
    _add_filter_options(meetings_parser)

    meeting_parser = subcommands.add_parser("meeting", help="Get one meeting")
    _add_project_company_options(meeting_parser)
    meeting_parser.add_argument(
        "--id",
        "--meeting-id",
        dest="meeting_id",
        type=int,
        required=True,
    )

    find_meeting_parser = subcommands.add_parser(
        "find-meeting",
        help="Find one meeting by number, title, or text",
    )
    _add_project_company_options(find_meeting_parser)
    _add_number_title_query_options(find_meeting_parser)

    inspections_parser = subcommands.add_parser(
        "inspections",
        help="List checklist-backed inspections for a project",
    )
    _add_project_company_options(inspections_parser)
    _add_filter_options(inspections_parser)

    inspection_parser = subcommands.add_parser("inspection", help="Get one inspection")
    _add_project_company_options(inspection_parser)
    inspection_parser.add_argument(
        "--id",
        "--inspection-id",
        dest="inspection_id",
        type=int,
        required=True,
    )

    find_inspection_parser = subcommands.add_parser(
        "find-inspection",
        help="Find one inspection by number, title, or text",
    )
    _add_project_company_options(find_inspection_parser)
    _add_number_title_query_options(find_inspection_parser)

    incidents_parser = subcommands.add_parser("incidents", help="List incidents for a project")
    _add_project_company_options(incidents_parser)
    _add_filter_options(incidents_parser)

    incident_parser = subcommands.add_parser("incident", help="Get one incident")
    _add_project_company_options(incident_parser)
    incident_parser.add_argument(
        "--id",
        "--incident-id",
        dest="incident_id",
        type=int,
        required=True,
    )

    incident_configuration_parser = subcommands.add_parser(
        "incident-configuration",
        help="Get project incident configuration",
    )
    _add_project_company_options(incident_configuration_parser)

    find_incident_parser = subcommands.add_parser(
        "find-incident",
        help="Find one incident by number, title, or text",
    )
    _add_project_company_options(find_incident_parser)
    _add_number_title_query_options(find_incident_parser)

    document_folders_parser = subcommands.add_parser(
        "document-folders",
        help="List document folders for a project",
    )
    document_folders_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    document_folders_parser.add_argument("--parent", "--parent-id", dest="parent_id", type=int)
    document_folders_parser.add_argument("--company-id", type=int, default=None)

    document_folder_parser = subcommands.add_parser(
        "document-folder",
        help="Get one document folder",
    )
    document_folder_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    document_folder_parser.add_argument(
        "--id", "--folder-id", dest="folder_id", type=int, required=True
    )
    document_folder_parser.add_argument("--company-id", type=int, default=None)

    find_document_folder_parser = subcommands.add_parser(
        "find-document-folder",
        help="Find one document folder by name",
    )
    find_document_folder_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    find_document_folder_parser.add_argument("--name", required=True)

    documents_parser = subcommands.add_parser("documents", help="List documents for a project")
    documents_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    documents_parser.add_argument("--folder", "--folder-id", dest="folder_id", type=int)
    documents_parser.add_argument(
        "--recursive",
        action="store_true",
        help="Traverse child folders discovered by the Documents API",
    )
    documents_parser.add_argument("--company-id", type=int, default=None)

    document_parser = subcommands.add_parser("document", help="Get one document")
    document_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    document_parser.add_argument(
        "--id", "--document-id", dest="document_id", type=int, required=True
    )
    document_parser.add_argument("--company-id", type=int, default=None)

    find_document_parser = subcommands.add_parser(
        "find-document",
        help="Find one document by name or filename",
    )
    find_document_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    find_document_parser.add_argument("--name", default=None)
    find_document_parser.add_argument("--filename", default=None)

    document_download_parser = subcommands.add_parser(
        "download-document",
        help="Download one document",
    )
    document_download_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    document_download_parser.add_argument(
        "--id", "--document-id", dest="document_id", type=int, required=True
    )
    document_download_parser.add_argument("--output", dest="output_dir", type=Path, default=None)
    document_download_parser.add_argument("--filename", default=None)
    document_download_parser.add_argument("--company-id", type=int, default=None)
    document_download_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the local document file if it exists",
    )

    drawing_areas_parser = subcommands.add_parser(
        "drawing-areas",
        help="List drawing areas for a project",
    )
    drawing_areas_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    drawing_areas_parser.add_argument("--company-id", type=int, default=None)

    drawing_area_parser = subcommands.add_parser(
        "drawing-area",
        help="Get one drawing area",
    )
    drawing_area_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    drawing_area_parser.add_argument(
        "--id", "--area-id", dest="drawing_area_id", type=int, required=True
    )
    drawing_area_parser.add_argument("--company-id", type=int, default=None)

    drawing_disciplines_parser = subcommands.add_parser(
        "drawing-disciplines",
        help="List drawing disciplines for a project",
    )
    drawing_disciplines_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    drawing_disciplines_parser.add_argument("--company-id", type=int, default=None)

    drawings_parser = subcommands.add_parser("drawings", help="List drawings for a project")
    drawings_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    drawings_parser.add_argument("--area", "--area-id", dest="drawing_area_id", type=int)
    drawings_parser.add_argument("--discipline", "--discipline-id", dest="discipline_id", type=int)
    drawings_parser.add_argument(
        "--current",
        action="store_true",
        default=None,
        help="Request only current drawings when supported by Procore",
    )
    drawings_parser.add_argument("--company-id", type=int, default=None)

    drawing_parser = subcommands.add_parser("drawing", help="Get one drawing")
    drawing_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    drawing_parser.add_argument("--id", "--drawing-id", dest="drawing_id", type=int, required=True)
    drawing_parser.add_argument("--area", "--area-id", dest="drawing_area_id", type=int)
    drawing_parser.add_argument("--company-id", type=int, default=None)

    find_drawing_parser = subcommands.add_parser(
        "find-drawing",
        help="Find one drawing by number or title",
    )
    find_drawing_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    find_drawing_parser.add_argument("--number", default=None)
    find_drawing_parser.add_argument("--title", default=None)
    find_drawing_parser.add_argument("--company-id", type=int, default=None)

    find_drawings_parser = subcommands.add_parser(
        "find-drawings",
        help="Find drawings containing text",
    )
    find_drawings_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    find_drawings_parser.add_argument("--contains", dest="text", required=True)
    find_drawings_parser.add_argument("--company-id", type=int, default=None)

    download_drawing_parser = subcommands.add_parser(
        "download-drawing",
        help="Download one drawing",
    )
    download_drawing_parser.add_argument(
        "--project", "--project-id", dest="project_id", type=int, required=True
    )
    download_drawing_parser.add_argument(
        "--id", "--drawing-id", dest="drawing_id", type=int, required=True
    )
    download_drawing_parser.add_argument("--area", "--area-id", dest="drawing_area_id", type=int)
    download_drawing_parser.add_argument("--output", dest="output_dir", type=Path, default=None)
    download_drawing_parser.add_argument("--filename", default=None)
    download_drawing_parser.add_argument("--company-id", type=int, default=None)
    download_drawing_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the local drawing file if it exists",
    )

    photo_albums_parser = subcommands.add_parser(
        "photo-albums",
        help="List photo albums for a project",
    )
    _add_photo_project_company_options(photo_albums_parser)
    photo_albums_parser.add_argument("--page", type=int)
    photo_albums_parser.add_argument("--per-page", type=int)

    photo_album_parser = subcommands.add_parser("photo-album", help="Get one photo album")
    _add_photo_project_company_options(photo_album_parser)
    photo_album_parser.add_argument(
        "--album", "--album-id", dest="album_id", type=int, required=True
    )

    find_photo_album_parser = subcommands.add_parser(
        "find-photo-album",
        help="Find one photo album by name",
    )
    _add_photo_project_company_options(find_photo_album_parser)
    find_photo_album_parser.add_argument("--name", required=True)

    photos_parser = subcommands.add_parser("photos", help="List photos for a project or album")
    _add_photo_project_company_options(photos_parser)
    _add_photo_filter_options(photos_parser)

    photo_parser = subcommands.add_parser("photo", help="Get one photo")
    _add_photo_project_company_options(photo_parser)
    photo_parser.add_argument("--photo", "--photo-id", dest="photo_id", type=int, required=True)

    find_photo_parser = subcommands.add_parser("find-photo", help="Find one photo")
    _add_photo_project_company_options(find_photo_parser)
    find_photo_parser.add_argument("--photo", "--photo-id", dest="photo_id", type=int)
    find_photo_parser.add_argument("--filename", default=None)
    find_photo_parser.add_argument("--description", default=None)
    find_photo_parser.add_argument("--query", default=None)

    download_photo_parser = subcommands.add_parser("download-photo", help="Download one photo")
    _add_photo_project_company_options(download_photo_parser)
    download_photo_parser.add_argument(
        "--photo",
        "--photo-id",
        dest="photo_id",
        type=int,
        required=True,
    )
    download_photo_parser.add_argument("--output-dir", "--output", dest="output_dir", type=Path)
    download_photo_parser.add_argument("--filename", default=None)
    download_photo_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the local photo file if it exists",
    )

    download_photo_album_parser = subcommands.add_parser(
        "download-photo-album",
        help="Download photos from one album",
    )
    _add_photo_project_company_options(download_photo_album_parser)
    download_photo_album_parser.add_argument(
        "--album",
        "--album-id",
        dest="album_id",
        type=int,
        required=True,
    )
    download_photo_album_parser.add_argument(
        "--output-dir", "--output", dest="output_dir", type=Path
    )
    download_photo_album_parser.add_argument("--limit", type=int)
    download_photo_album_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite local photo files if they exist",
    )

    daily_log_counts_parser = subcommands.add_parser(
        "daily-log-counts",
        help="Get Daily Log counts for a project",
    )
    _add_daily_log_options(daily_log_counts_parser)

    daily_log_headers_parser = subcommands.add_parser(
        "daily-log-headers",
        help="List Daily Log headers for a project",
    )
    _add_daily_log_options(daily_log_headers_parser)

    daily_log_header_parser = subcommands.add_parser(
        "daily-log-header",
        help="Get one Daily Log header by ID or date",
    )
    _add_daily_log_options(daily_log_header_parser)
    daily_log_header_parser.add_argument("--header", "--header-id", dest="header_id", type=int)

    daily_logs_parser = subcommands.add_parser(
        "daily-logs",
        help="List Daily Logs by type",
    )
    _add_daily_log_options(daily_logs_parser)
    daily_logs_parser.add_argument("--log-type", required=True)

    daily_log_parser = subcommands.add_parser("daily-log", help="Get one Daily Log by type and ID")
    _add_daily_log_options(daily_log_parser)
    daily_log_parser.add_argument("--log-type", required=True)
    daily_log_parser.add_argument("--log", "--log-id", dest="log_id", type=int, required=True)

    daily_logs_date_parser = subcommands.add_parser(
        "daily-logs-date",
        help="List multiple Daily Log types for one date",
    )
    _add_daily_log_options(daily_logs_date_parser)
    daily_logs_date_parser.add_argument(
        "--types",
        default=None,
        help="Comma-separated Daily Log types, for example manpower,notes",
    )

    delay_log_types_parser = subcommands.add_parser(
        "delay-log-types",
        help="List Daily Logs delay types",
    )
    _add_daily_log_options(delay_log_types_parser)

    for command_name, help_text in {
        "manpower-logs": "List manpower logs",
        "notes-logs": "List notes logs",
        "daily-construction-report-logs": "List daily construction report logs",
        "delay-logs": "List delay logs",
        "delivery-logs": "List delivery logs",
        "call-logs": "List call logs",
        "accident-logs": "List accident logs",
        "dumpster-logs": "List dumpster logs",
        "visitor-logs": "List visitor logs",
        "productivity-logs": "List productivity logs",
        "plan-revision-logs": "List plan revision logs",
    }.items():
        convenience_parser = subcommands.add_parser(command_name, help=help_text)
        _add_daily_log_options(convenience_parser)

    specification_sets_parser = subcommands.add_parser(
        "specification-sets",
        help="List specification sets for a project",
    )
    _add_spec_project_company_options(specification_sets_parser)

    specification_sections_parser = subcommands.add_parser(
        "specification-sections",
        help="List specification sections for a project",
    )
    _add_spec_project_company_options(specification_sections_parser)
    specification_sections_parser.add_argument("--specification-area-id", type=int)
    specification_sections_parser.add_argument("--specification-set-id", type=int)
    specification_sections_parser.add_argument("--division-id", type=int)
    specification_sections_parser.add_argument("--sort", default=None)

    specification_section_parser = subcommands.add_parser(
        "specification-section",
        help="Get one specification section",
    )
    _add_spec_project_company_options(specification_section_parser)
    specification_section_parser.add_argument(
        "--section",
        "--section-id",
        dest="specification_section_id",
        type=int,
        required=True,
    )

    find_specification_section_parser = subcommands.add_parser(
        "find-specification-section",
        help="Find one specification section by number, title, or text",
    )
    _add_spec_project_company_options(find_specification_section_parser)
    find_specification_section_parser.add_argument("--number", default=None)
    find_specification_section_parser.add_argument("--title", default=None)
    find_specification_section_parser.add_argument("--query", default=None)

    specification_revisions_parser = subcommands.add_parser(
        "specification-revisions",
        help="List specification section revisions for a project",
    )
    _add_spec_project_company_options(specification_revisions_parser)
    specification_revisions_parser.add_argument(
        "--section",
        "--section-id",
        dest="specification_section_id",
        type=int,
    )
    specification_revisions_parser.add_argument("--page", type=int)
    specification_revisions_parser.add_argument("--per-page", type=int)

    specification_revision_parser = subcommands.add_parser(
        "specification-revision",
        help="Get one specification section revision",
    )
    _add_spec_project_company_options(specification_revision_parser)
    specification_revision_parser.add_argument(
        "--revision",
        "--revision-id",
        dest="revision_id",
        type=int,
        required=True,
    )

    download_specification_revision_parser = subcommands.add_parser(
        "download-specification-revision",
        help="Download one specification section revision",
    )
    _add_spec_project_company_options(download_specification_revision_parser)
    download_specification_revision_parser.add_argument(
        "--revision",
        "--revision-id",
        dest="revision_id",
        type=int,
        required=True,
    )
    download_specification_revision_parser.add_argument(
        "--output-dir",
        "--output",
        dest="output_dir",
        type=Path,
        default=None,
    )
    download_specification_revision_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the local specification file if it exists",
    )

    package_rfi_parser = subcommands.add_parser(
        "package-rfi",
        help="Build an automation package for one RFI",
    )
    _add_package_options(package_rfi_parser)

    enhanced_rfi_parser = subcommands.add_parser(
        "enhanced-rfi-package",
        help="Build an enhanced AI-ready RFI review package",
    )
    enhanced_rfi_parser.add_argument(
        "--project",
        "--project-id",
        dest="project_id",
        type=int,
        required=True,
    )
    enhanced_rfi_parser.add_argument("--company-id", "--company", dest="company_id", type=int)
    enhanced_rfi_parser.add_argument("--rfi-id", type=int)
    enhanced_rfi_parser.add_argument("--rfi-number")
    enhanced_rfi_parser.add_argument(
        "--output-dir",
        "--output",
        dest="output_dir",
        type=Path,
        default=None,
    )
    enhanced_rfi_parser.add_argument(
        "--include-related",
        dest="include_related",
        action="store_true",
        default=True,
        help="Include related project context",
    )
    enhanced_rfi_parser.add_argument(
        "--no-related",
        dest="include_related",
        action="store_false",
        help="Skip related project context",
    )
    enhanced_rfi_parser.add_argument("--related-sections")
    enhanced_rfi_parser.add_argument("--exclude-related")
    enhanced_rfi_parser.add_argument(
        "--search-term",
        dest="search_terms",
        action="append",
        default=None,
        help="Search term to use for related context. Can be repeated or comma-separated.",
    )
    enhanced_rfi_parser.add_argument("--start-date")
    enhanced_rfi_parser.add_argument("--end-date")
    enhanced_rfi_parser.add_argument("--log-date")
    enhanced_rfi_parser.add_argument("--max-related-items", type=int, default=25)
    enhanced_rfi_parser.add_argument(
        "--download-files",
        action="store_true",
        help="Download RFI attachments. Off by default.",
    )
    enhanced_rfi_parser.add_argument("--overwrite", action="store_true")
    enhanced_rfi_parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on the first related section error",
    )

    package_submittal_parser = subcommands.add_parser(
        "package-submittal",
        help="Build an automation package for one submittal",
    )
    _add_package_options(package_submittal_parser)

    enhanced_submittal_parser = subcommands.add_parser(
        "enhanced-submittal-package",
        help="Build an enhanced AI-ready submittal review package",
    )
    enhanced_submittal_parser.add_argument(
        "--project",
        "--project-id",
        dest="project_id",
        type=int,
        required=True,
    )
    enhanced_submittal_parser.add_argument("--company-id", "--company", dest="company_id", type=int)
    enhanced_submittal_parser.add_argument("--submittal-id", type=int)
    enhanced_submittal_parser.add_argument("--submittal-number")
    enhanced_submittal_parser.add_argument(
        "--output-dir",
        "--output",
        dest="output_dir",
        type=Path,
        default=None,
    )
    enhanced_submittal_parser.add_argument(
        "--include-related",
        dest="include_related",
        action="store_true",
        default=True,
        help="Include related project context",
    )
    enhanced_submittal_parser.add_argument(
        "--no-related",
        dest="include_related",
        action="store_false",
        help="Skip related project context",
    )
    enhanced_submittal_parser.add_argument("--related-sections")
    enhanced_submittal_parser.add_argument("--exclude-related")
    enhanced_submittal_parser.add_argument(
        "--search-term",
        dest="search_terms",
        action="append",
        default=None,
        help="Search term to use for related context. Can be repeated or comma-separated.",
    )
    enhanced_submittal_parser.add_argument("--start-date")
    enhanced_submittal_parser.add_argument("--end-date")
    enhanced_submittal_parser.add_argument("--log-date")
    enhanced_submittal_parser.add_argument("--max-related-items", type=int, default=25)
    enhanced_submittal_parser.add_argument(
        "--download-files",
        action="store_true",
        help="Download submittal attachments. Off by default.",
    )
    enhanced_submittal_parser.add_argument("--overwrite", action="store_true")
    enhanced_submittal_parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on the first related section error",
    )

    export_rfis_parser = subcommands.add_parser(
        "export-rfis",
        help="Export project RFIs to CSV",
    )
    _add_project_output_options(export_rfis_parser, output_help="CSV output path")
    _add_filter_options(export_rfis_parser)

    export_submittals_parser = subcommands.add_parser(
        "export-submittals",
        help="Export project submittals to CSV",
    )
    _add_project_output_options(export_submittals_parser, output_help="CSV output path")
    _add_filter_options(export_submittals_parser)

    export_observations_parser = subcommands.add_parser(
        "export-observations",
        help="Export project observations to CSV",
    )
    _add_project_company_options(export_observations_parser)
    export_observations_parser.add_argument(
        "--output",
        dest="output_path",
        type=Path,
        required=True,
        help="CSV output path",
    )
    _add_filter_options(export_observations_parser)

    export_punch_items_parser = subcommands.add_parser(
        "export-punch-items",
        help="Export project punch items to CSV",
    )
    _add_project_company_options(export_punch_items_parser)
    export_punch_items_parser.add_argument(
        "--output",
        dest="output_path",
        type=Path,
        required=True,
        help="CSV output path",
    )
    _add_filter_options(export_punch_items_parser)

    export_correspondences_parser = subcommands.add_parser(
        "export-correspondences",
        help="Export Generic Tool correspondence items to CSV",
    )
    _add_project_company_options(export_correspondences_parser)
    export_correspondences_parser.add_argument(
        "--generic-tool",
        "--generic-tool-id",
        dest="generic_tool_id",
        type=int,
        required=True,
    )
    export_correspondences_parser.add_argument(
        "--output",
        dest="output_path",
        type=Path,
        required=True,
        help="CSV output path",
    )
    _add_filter_options(export_correspondences_parser)

    export_meetings_parser = subcommands.add_parser(
        "export-meetings",
        help="Export project meetings to CSV",
    )
    _add_project_company_options(export_meetings_parser)
    export_meetings_parser.add_argument(
        "--output",
        dest="output_path",
        type=Path,
        required=True,
        help="CSV output path",
    )
    _add_filter_options(export_meetings_parser)

    export_inspections_parser = subcommands.add_parser(
        "export-inspections",
        help="Export project inspections to CSV",
    )
    _add_project_company_options(export_inspections_parser)
    export_inspections_parser.add_argument(
        "--output",
        dest="output_path",
        type=Path,
        required=True,
        help="CSV output path",
    )
    _add_filter_options(export_inspections_parser)

    export_incidents_parser = subcommands.add_parser(
        "export-incidents",
        help="Export project incidents to CSV",
    )
    _add_project_company_options(export_incidents_parser)
    export_incidents_parser.add_argument(
        "--output",
        dest="output_path",
        type=Path,
        required=True,
        help="CSV output path",
    )
    _add_filter_options(export_incidents_parser)

    ai_review_export_parser = subcommands.add_parser(
        "ai-review-export",
        help="Build a local AI review export from a package folder",
    )
    ai_review_export_parser.add_argument("--package-dir", type=Path, required=True)
    ai_review_export_parser.add_argument("--output-dir", type=Path)
    ai_review_export_parser.add_argument("--export-name")
    ai_review_export_parser.add_argument("--format", default="markdown")
    ai_review_export_parser.add_argument(
        "--include-json",
        dest="include_json",
        action="store_true",
        default=True,
        help="Write ai_review.json",
    )
    ai_review_export_parser.add_argument(
        "--no-json",
        dest="include_json",
        action="store_false",
        help="Skip ai_review.json",
    )
    ai_review_export_parser.add_argument(
        "--include-prompt",
        dest="include_prompt",
        action="store_true",
        default=True,
        help="Write prompt.md and system_context.md",
    )
    ai_review_export_parser.add_argument(
        "--no-prompt",
        dest="include_prompt",
        action="store_false",
        help="Skip prompt.md and system_context.md",
    )
    ai_review_export_parser.add_argument(
        "--include-checklists",
        dest="include_checklists",
        action="store_true",
        default=True,
        help="Write checklist files",
    )
    ai_review_export_parser.add_argument(
        "--no-checklists",
        dest="include_checklists",
        action="store_false",
        help="Skip checklist files",
    )
    ai_review_export_parser.add_argument("--max-chunk-chars", type=int, default=12000)
    ai_review_export_parser.add_argument("--overwrite", action="store_true")

    ai_prompt_pack_parser = subcommands.add_parser(
        "ai-prompt-pack",
        help="Build a prompt-focused local AI export from a package folder",
    )
    ai_prompt_pack_parser.add_argument("--package-dir", type=Path, required=True)
    ai_prompt_pack_parser.add_argument("--output-dir", type=Path)
    ai_prompt_pack_parser.add_argument("--review-type", default="general")
    ai_prompt_pack_parser.add_argument("--max-chunk-chars", type=int, default=12000)
    ai_prompt_pack_parser.add_argument("--overwrite", action="store_true")

    workflow_plan_parser = subcommands.add_parser(
        "workflow-plan",
        help="Validate or run a local workflow plan",
    )
    workflow_plan_subcommands = workflow_plan_parser.add_subparsers(
        dest="workflow_plan_command",
        required=True,
    )
    workflow_plan_list_parser = workflow_plan_subcommands.add_parser(
        "list",
        help="List workflow names supported by local plans",
    )
    workflow_plan_list_parser.add_argument("--json", dest="json_output", action="store_true")

    workflow_plan_validate_parser = workflow_plan_subcommands.add_parser(
        "validate",
        help="Validate a local workflow plan without running it",
    )
    workflow_plan_validate_parser.add_argument("plan_path", type=Path)
    workflow_plan_validate_parser.add_argument("--json", dest="json_output", action="store_true")

    workflow_plan_run_parser = workflow_plan_subcommands.add_parser(
        "run",
        help="Run or dry-run a local workflow plan",
    )
    workflow_plan_run_parser.add_argument("plan_path", type=Path)
    workflow_plan_run_parser.add_argument("--output-dir", type=Path)
    workflow_plan_run_parser.add_argument("--dry-run", action="store_true")
    workflow_plan_run_parser.add_argument(
        "--fail-fast",
        dest="continue_on_error",
        action="store_false",
        default=True,
        help="Stop after the first failed step",
    )
    workflow_plan_run_parser.add_argument(
        "--continue-on-error",
        dest="continue_on_error",
        action="store_true",
        help="Continue independent steps after failures",
    )
    workflow_plan_run_parser.add_argument("--json", dest="json_output", action="store_true")

    webhook_parser = subcommands.add_parser(
        "webhook",
        help="Validate, save, list, or dry-run local webhook event payloads",
    )
    webhook_subcommands = webhook_parser.add_subparsers(
        dest="webhook_command",
        required=True,
    )

    webhook_validate_parser = webhook_subcommands.add_parser(
        "validate",
        help="Validate and summarize a local webhook event JSON payload",
    )
    webhook_validate_parser.add_argument("event_json", type=Path)
    webhook_validate_parser.add_argument("--json", dest="json_output", action="store_true")

    webhook_save_parser = webhook_subcommands.add_parser(
        "save",
        help="Save a local webhook event JSON payload to the event store",
    )
    webhook_save_parser.add_argument("event_json", type=Path)
    webhook_save_parser.add_argument("--event-dir", type=Path)
    webhook_save_parser.add_argument("--json", dest="json_output", action="store_true")

    webhook_list_parser = webhook_subcommands.add_parser(
        "list",
        help="List saved local webhook events",
    )
    _add_webhook_filter_options(webhook_list_parser)
    webhook_list_parser.add_argument("--event-dir", type=Path)
    webhook_list_parser.add_argument("--json", dest="json_output", action="store_true")

    webhook_dispatch_parser = webhook_subcommands.add_parser(
        "dispatch",
        help="Dry-run or dispatch a local webhook event to a workflow plan",
    )
    webhook_dispatch_parser.add_argument("event_json", type=Path)
    webhook_dispatch_parser.add_argument("--workflow-plan", type=Path)
    webhook_dispatch_parser.add_argument("--output-dir", type=Path)
    webhook_dispatch_parser.add_argument("--event-dir", type=Path)
    webhook_dispatch_parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        default=True,
        help="Validate and resolve the workflow plan without live execution",
    )
    webhook_dispatch_parser.add_argument(
        "--no-dry-run",
        dest="dry_run",
        action="store_false",
        help="Allow the workflow plan to execute. Use with care.",
    )
    webhook_dispatch_parser.add_argument("--json", dest="json_output", action="store_true")

    sync_rfis_parser = subcommands.add_parser(
        "sync-rfis",
        help="Sync project RFIs to a local folder",
    )
    _add_project_output_options(sync_rfis_parser, output_help="Output folder")
    _add_filter_options(sync_rfis_parser)
    _add_sync_options(sync_rfis_parser)

    sync_submittals_parser = subcommands.add_parser(
        "sync-submittals",
        help="Sync project submittals to a local folder",
    )
    _add_project_output_options(sync_submittals_parser, output_help="Output folder")
    _add_filter_options(sync_submittals_parser)
    _add_sync_options(sync_submittals_parser)

    sync_documents_parser = subcommands.add_parser(
        "sync-documents",
        help="Sync project documents to a local folder",
    )
    _add_project_output_options(sync_documents_parser, output_help="Output folder")
    sync_documents_parser.add_argument("--folder", "--folder-id", dest="folder_id", type=int)
    sync_documents_parser.add_argument(
        "--recursive",
        action="store_true",
        help="Traverse child folders discovered by the Documents API",
    )
    sync_documents_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing downloaded documents",
    )
    sync_documents_parser.add_argument(
        "--no-tracker",
        dest="create_tracker",
        action="store_false",
        default=True,
        help="Skip tracker CSV creation",
    )
    sync_documents_parser.add_argument(
        "--no-markdown",
        dest="create_markdown",
        action="store_false",
        default=True,
        help="Skip per-document Markdown summaries",
    )
    sync_documents_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan the sync without writing files or downloading documents",
    )
    sync_documents_parser.add_argument(
        "--incremental",
        action="store_true",
        help="Skip unchanged documents using local sync state",
    )

    sync_project_parser = subcommands.add_parser(
        "sync-project",
        help="Sync project RFIs and submittals to a local folder",
    )
    _add_project_output_options(sync_project_parser, output_help="Output folder")
    _add_filter_options(sync_project_parser)
    _add_sync_options(sync_project_parser)
    sync_project_parser.add_argument(
        "--rfis-only",
        action="store_true",
        help="Sync only RFIs",
    )
    sync_project_parser.add_argument(
        "--submittals-only",
        action="store_true",
        help="Sync only submittals",
    )

    project_context_parser = subcommands.add_parser(
        "project-context",
        help="Build an AI-ready read-only project context package",
    )
    _add_project_output_options(project_context_parser, output_help="Output folder")
    project_context_parser.add_argument("--company-id", "--company", dest="company_id", type=int)
    project_context_parser.add_argument(
        "--include",
        help="Comma-separated sections to include, such as rfis,submittals",
    )
    project_context_parser.add_argument(
        "--exclude",
        help="Comma-separated sections to skip, such as photos,documents",
    )
    project_context_parser.add_argument("--start-date")
    project_context_parser.add_argument("--end-date")
    project_context_parser.add_argument("--log-date")
    project_context_parser.add_argument("--max-items", type=int)
    project_context_parser.add_argument(
        "--download-files",
        action="store_true",
        help="Download supported files. Off by default.",
    )
    project_context_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow file downloads to overwrite existing files",
    )
    project_context_parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on the first section error instead of recording it",
    )

    return parser


def _add_alias_parser(
    subcommands: argparse._SubParsersAction[argparse.ArgumentParser],
    name: str,
    aliases: list[str],
    legacy_name: str,
    **kwargs: Any,
) -> argparse.ArgumentParser:
    """Add a subcommand with aliases when supported by argparse."""
    parser = subcommands.add_parser(name, aliases=aliases, **kwargs)
    parser.set_defaults(command=name, legacy_command=legacy_name)
    return parser


def _add_package_options(parser: argparse.ArgumentParser) -> None:
    """Add shared automation package command options."""
    parser.add_argument("--company", dest="company_id", type=int, default=None)
    parser.add_argument("--project", "--project-id", dest="project_id", type=int, default=None)
    parser.add_argument("--project-name", default=None)
    parser.add_argument("--project-number", default=None)
    parser.add_argument("--id", dest="item_id", type=int, default=None)
    parser.add_argument("--number", dest="item_number", default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument(
        "--no-downloads",
        dest="download_attachments",
        action="store_false",
        default=True,
    )


def _write_text_output(output_path: Path, content: str) -> Path:
    """Write CLI text output to a path and return the saved path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return output_path


def _write_optional_output(content: str, output_path: Path | None) -> str | Path:
    """Return text content or write it to disk when an output path is provided."""
    if output_path is None:
        return content
    return _write_text_output(output_path, content)


def _add_filter_options(parser: argparse.ArgumentParser) -> None:
    """Add shared list filter options."""
    parser.add_argument("--status", default=None)
    parser.add_argument("--updated-after", default=None)
    parser.add_argument("--updated-before", default=None)
    parser.add_argument("--created-after", default=None)
    parser.add_argument("--created-before", default=None)


def _add_spec_project_company_options(parser: argparse.ArgumentParser) -> None:
    """Add shared Specifications command options."""
    parser.add_argument("--project", "--project-id", dest="project_id", type=int, required=True)
    parser.add_argument("--company-id", "--company", dest="company_id", type=int, default=None)


def _add_project_company_options(parser: argparse.ArgumentParser) -> None:
    """Add shared company/project command options."""
    parser.add_argument("--project", "--project-id", dest="project_id", type=int, required=True)
    parser.add_argument("--company-id", "--company", dest="company_id", type=int, default=None)


def _add_number_title_query_options(parser: argparse.ArgumentParser) -> None:
    """Add shared resolver options for number/title/text lookup."""
    parser.add_argument("--number", default=None)
    parser.add_argument("--title", default=None)
    parser.add_argument("--query", default=None)


def _add_photo_project_company_options(parser: argparse.ArgumentParser) -> None:
    """Add shared Photos command options."""
    parser.add_argument("--project", "--project-id", dest="project_id", type=int, required=True)
    parser.add_argument("--company-id", "--company", dest="company_id", type=int, default=None)


def _add_photo_filter_options(parser: argparse.ArgumentParser) -> None:
    """Add shared Photos list filter options."""
    parser.add_argument("--album", "--album-id", dest="album_id", type=int)
    parser.add_argument("--image-category-id", type=int)
    parser.add_argument("--private", action="store_true", default=None)
    parser.add_argument("--starred", action="store_true", default=None)
    parser.add_argument("--created-at", default=None)
    parser.add_argument("--updated-at", default=None)
    parser.add_argument("--log-date", default=None)
    parser.add_argument("--query", default=None)
    parser.add_argument("--uploader-id", dest="uploader_ids", type=int, action="append")
    parser.add_argument("--location-id", dest="location_ids", type=int, action="append")
    parser.add_argument("--trade-id", dest="trade_ids", type=int, action="append")
    parser.add_argument("--projection", default=None)
    parser.add_argument("--serializer-view", default=None)
    parser.add_argument("--sort", default=None)
    parser.add_argument("--page", type=int)
    parser.add_argument("--per-page", type=int)


def _add_daily_log_options(parser: argparse.ArgumentParser) -> None:
    """Add shared Daily Logs command options."""
    parser.add_argument("--project", "--project-id", dest="project_id", type=int, required=True)
    parser.add_argument("--company-id", "--company", dest="company_id", type=int, default=None)
    parser.add_argument("--log-date", default=None)
    parser.add_argument("--start-date", default=None)
    parser.add_argument("--end-date", default=None)
    parser.add_argument("--page", type=int)
    parser.add_argument("--per-page", type=int)


def _add_project_output_options(parser: argparse.ArgumentParser, *, output_help: str) -> None:
    """Add shared project and output options."""
    parser.add_argument("--project", "--project-id", dest="project_id", type=int, required=True)
    parser.add_argument("--output", dest="output_path", type=Path, required=True, help=output_help)


def _add_sync_options(parser: argparse.ArgumentParser) -> None:
    """Add shared local folder sync options."""
    parser.add_argument(
        "--no-attachments",
        dest="download_attachments",
        action="store_false",
        default=True,
        help="Skip attachment downloads",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing downloaded attachments",
    )
    parser.add_argument(
        "--no-tracker",
        dest="create_tracker",
        action="store_false",
        default=True,
        help="Skip tracker CSV creation",
    )
    parser.add_argument(
        "--no-markdown",
        dest="create_markdown",
        action="store_false",
        default=True,
        help="Skip per-item Markdown summaries",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan the sync without writing files or downloading attachments",
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Skip unchanged items using local sync state",
    )


def _add_webhook_filter_options(parser: argparse.ArgumentParser) -> None:
    """Add common webhook event store filter options to a parser."""
    parser.add_argument("--company-id")
    parser.add_argument("--project-id")
    parser.add_argument("--resource-type")
    parser.add_argument("--resource-id")
    parser.add_argument("--event-type")
    parser.add_argument("--action")
    parser.add_argument("--date")


def run_command(args: argparse.Namespace) -> Any:
    """Run a parsed CLI command and return serializable output."""
    if args.command == "doctor":
        return run_doctor(live=args.live)

    if args.command == "auth":
        if args.auth_command == "status":
            return get_auth_status()
        if args.auth_command == "refresh":
            return refresh_auth_token()
        if args.auth_command == "login-url":
            return build_authorization_url()
        if args.auth_command == "client-credentials-token":
            return request_client_credentials_token_and_save()
        if args.auth_command == "exchange-code":
            return exchange_code_and_save(args.code)
        raise ValueError(f"Unsupported auth command: {args.auth_command}")

    if args.command == "agent":
        if args.agent_command == "manifest":
            return build_agent_manifest()
        if args.agent_command == "tools":
            return list_agent_tools()
        if args.agent_command == "tool":
            return get_agent_tool(args.tool_name)
        if args.agent_command == "openapi":
            openapi_text = (
                export_agent_openapi_yaml()
                if args.yaml
                else export_agent_openapi_json(pretty=args.pretty)
            )
            if args.output is not None:
                return _write_text_output(args.output, openapi_text)
            return openapi_text
        if args.agent_command == "schemas":
            schemas_text = export_agent_tool_schemas_json(pretty=args.pretty)
            if args.output is not None:
                return _write_text_output(args.output, schemas_text)
            return schemas_text
        if args.agent_command == "runs":
            if args.agent_runs_command == "list":
                return list_agent_runs(args.run_log_dir)
            if args.agent_runs_command == "show":
                return load_agent_run(args.run_log_dir, args.run_id)
            if args.agent_runs_command == "replay":
                return replay_agent_run(args.run_log_dir, args.run_id)
            if args.agent_runs_command == "export":
                return export_agent_run_bundle(
                    args.run_log_dir,
                    args.run_id,
                    args.output_dir,
                )
            raise ValueError(f"Unsupported agent runs command: {args.agent_runs_command}")
        if args.agent_command == "mcp":
            if args.agent_mcp_command == "tools":
                return _write_optional_output(
                    export_mcp_tools_json(pretty=args.pretty),
                    args.output,
                )
            if args.agent_mcp_command == "resources":
                return _write_optional_output(
                    export_mcp_resources_json(pretty=args.pretty),
                    args.output,
                )
            if args.agent_mcp_command == "prompts":
                return _write_optional_output(
                    export_mcp_prompts_json(pretty=args.pretty),
                    args.output,
                )
            if args.agent_mcp_command == "manifest":
                return _write_optional_output(
                    export_mcp_manifest_json(pretty=args.pretty),
                    args.output,
                )
            if args.agent_mcp_command == "stdio":
                return run_mcp_stdio_server()
            raise ValueError(f"Unsupported agent MCP command: {args.agent_mcp_command}")
        if args.agent_command == "evals":
            if args.agent_evals_command == "list":
                return list_agent_eval_suites()
            if args.agent_evals_command == "show":
                return get_agent_eval_suite(args.suite_name)
            if args.agent_evals_command == "run":
                eval_results = (
                    run_agent_eval_suite(args.suite_name)
                    if args.suite_name
                    else run_all_agent_eval_suites()
                )
                if args.output is not None:
                    write_agent_eval_results(eval_results, args.output, pretty=True)
                return eval_results
            raise ValueError(f"Unsupported agent evals command: {args.agent_evals_command}")
        if args.agent_command == "serve":
            public_bind = _requires_public_bind(args.host)
            if public_bind and not args.allow_public_bind:
                raise ValidationError(
                    "The agent API server binds to 127.0.0.1 by default. "
                    "Use --allow-public-bind only when you intentionally want "
                    "to expose it beyond localhost."
                )
            if public_bind and args.allow_public_bind:
                print(
                    "Warning: binding the agent API server outside localhost. "
                    "Tool execution is still disabled."
                )
            return run_agent_api_server(
                host=args.host,
                port=args.port,
                run_log_dir=args.run_log_dir,
                run_id=args.run_id,
            )
        raise ValueError(f"Unsupported agent command: {args.agent_command}")

    if args.command == "workflow-plan":
        if args.workflow_plan_command == "list":
            return list_available_workflows()
        if args.workflow_plan_command == "validate":
            return validate_workflow_plan(load_workflow_plan(args.plan_path))
        if args.workflow_plan_command == "run":
            return run_workflow_plan(
                args.plan_path,
                output_dir=args.output_dir,
                dry_run=args.dry_run,
                continue_on_error=args.continue_on_error,
            )
        raise ValueError(f"Unsupported workflow-plan command: {args.workflow_plan_command}")

    if args.command == "webhook":
        if args.webhook_command == "validate":
            return load_webhook_event(args.event_json)
        if args.webhook_command == "save":
            return save_webhook_event(
                load_webhook_event(args.event_json),
                event_dir=args.event_dir,
            )
        if args.webhook_command == "list":
            return list_webhook_events(
                event_dir=args.event_dir,
                filters=_webhook_filters_from_args(args),
            )
        if args.webhook_command == "dispatch":
            event = load_webhook_event(args.event_json)
            if args.event_dir is not None:
                save_webhook_event(event, event_dir=args.event_dir)
            return dispatch_webhook_event(
                event,
                workflow_plan=args.workflow_plan,
                output_dir=args.output_dir,
                dry_run=args.dry_run,
            )
        raise ValueError(f"Unsupported webhook command: {args.webhook_command}")

    if args.command == "companies":
        return list_companies()

    if args.command == "find-company":
        return find_company(args.name)

    if args.command == "projects":
        company_id = args.company_id or get_settings().company_id
        return list_projects(company_id)

    if args.command == "find-project":
        return find_project(args.query, number=args.number, company_id=args.company_id)

    if args.command == "rfis":
        return list_rfis(
            args.project_id,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
        )

    if args.command == "rfi":
        return get_rfi(args.project_id, args.rfi_id)

    if args.command == "find-rfi":
        return find_rfi(args.project_id, number=args.number)

    if args.command == "download-rfi":
        return [
            str(path)
            for path in download_rfi_attachments(
                args.project_id,
                args.rfi_id,
                args.destination_dir,
            )
        ]

    if args.command == "submittals":
        return list_submittals(
            args.project_id,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
        )

    if args.command == "submittal":
        return get_submittal(args.project_id, args.submittal_id)

    if args.command == "find-submittal":
        return find_submittal(args.project_id, number=args.number)

    if args.command == "download-submittal":
        return [
            str(path)
            for path in download_submittal_attachments(
                args.project_id,
                args.submittal_id,
                args.destination_dir,
            )
        ]

    if args.command == "observations":
        return list_observations(
            args.company_id,
            args.project_id,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
        )

    if args.command == "observation":
        return get_observation(args.company_id, args.project_id, args.observation_id)

    if args.command == "find-observation":
        return find_observation(
            args.company_id,
            args.project_id,
            number=args.number,
            title=args.title,
            query=args.query,
        )

    if args.command == "punch-items":
        return list_punch_items(
            args.company_id,
            args.project_id,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
        )

    if args.command == "punch-item":
        return get_punch_item(args.company_id, args.project_id, args.punch_item_id)

    if args.command == "find-punch-item":
        return find_punch_item(
            args.company_id,
            args.project_id,
            number=args.number,
            title=args.title,
            query=args.query,
        )

    if args.command == "generic-tools":
        return list_generic_tools(args.company_id, args.project_id)

    if args.command == "generic-tool":
        return get_generic_tool(args.company_id, args.project_id, args.generic_tool_id)

    if args.command == "correspondences":
        return list_correspondences(
            args.company_id,
            args.project_id,
            args.generic_tool_id,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
        )

    if args.command == "correspondence":
        return get_correspondence(args.company_id, args.project_id, args.correspondence_id)

    if args.command == "find-correspondence":
        return find_correspondence(
            args.company_id,
            args.project_id,
            args.generic_tool_id,
            number=args.number,
            title=args.title,
            query=args.query,
        )

    if args.command == "meetings":
        return list_meetings(
            args.company_id,
            args.project_id,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
        )

    if args.command == "meeting":
        return get_meeting(args.company_id, args.project_id, args.meeting_id)

    if args.command == "find-meeting":
        return find_meeting(
            args.company_id,
            args.project_id,
            number=args.number,
            title=args.title,
            query=args.query,
        )

    if args.command == "inspections":
        return list_inspections(
            args.company_id,
            args.project_id,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
        )

    if args.command == "inspection":
        return get_inspection(args.company_id, args.project_id, args.inspection_id)

    if args.command == "find-inspection":
        return find_inspection(
            args.company_id,
            args.project_id,
            number=args.number,
            title=args.title,
            query=args.query,
        )

    if args.command == "incidents":
        return list_incidents(
            args.company_id,
            args.project_id,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
        )

    if args.command == "incident":
        return get_incident(args.company_id, args.project_id, args.incident_id)

    if args.command == "incident-configuration":
        return get_project_incident_configuration(args.company_id, args.project_id)

    if args.command == "find-incident":
        return find_incident(
            args.company_id,
            args.project_id,
            number=args.number,
            title=args.title,
            query=args.query,
        )

    if args.command == "document-folders":
        return list_document_folders(
            args.project_id,
            parent_id=args.parent_id,
            company_id=args.company_id,
        )

    if args.command == "document-folder":
        return get_document_folder(
            args.project_id,
            args.folder_id,
            company_id=args.company_id,
        )

    if args.command == "find-document-folder":
        return find_document_folder(args.project_id, args.name)

    if args.command == "documents":
        return list_documents(
            args.project_id,
            folder_id=args.folder_id,
            recursive=args.recursive,
            company_id=args.company_id,
        )

    if args.command == "document":
        return get_document(args.project_id, args.document_id, company_id=args.company_id)

    if args.command == "find-document":
        return find_document(args.project_id, name=args.name, filename=args.filename)

    if args.command == "download-document":
        output_dir = args.output_dir if args.output_dir is not None else "downloads/documents"
        return download_document(
            args.project_id,
            args.document_id,
            output_dir=output_dir,
            filename=args.filename,
            company_id=args.company_id,
            overwrite=args.overwrite,
        )

    if args.command == "drawing-areas":
        return list_drawing_areas(args.project_id, company_id=args.company_id)

    if args.command == "drawing-area":
        return get_drawing_area(
            args.project_id,
            args.drawing_area_id,
            company_id=args.company_id,
        )

    if args.command == "drawing-disciplines":
        return list_drawing_disciplines(args.project_id, company_id=args.company_id)

    if args.command == "drawings":
        return list_drawings(
            args.project_id,
            company_id=args.company_id,
            drawing_area_id=args.drawing_area_id,
            discipline_id=args.discipline_id,
            current=args.current,
        )

    if args.command == "drawing":
        return get_drawing(
            args.project_id,
            args.drawing_id,
            company_id=args.company_id,
            drawing_area_id=args.drawing_area_id,
        )

    if args.command == "find-drawing":
        return find_drawing(
            args.project_id,
            number=args.number,
            title=args.title,
            company_id=args.company_id,
        )

    if args.command == "find-drawings":
        return find_drawings_contains(args.project_id, args.text, company_id=args.company_id)

    if args.command == "download-drawing":
        output_dir = args.output_dir if args.output_dir is not None else "downloads/drawings"
        return download_drawing(
            args.project_id,
            args.drawing_id,
            output_dir=output_dir,
            filename=args.filename,
            company_id=args.company_id,
            overwrite=args.overwrite,
            drawing_area_id=args.drawing_area_id,
        )

    if args.command == "photo-albums":
        return list_photo_albums(
            args.project_id,
            company_id=args.company_id,
            page=args.page,
            per_page=args.per_page,
        )

    if args.command == "photo-album":
        return get_photo_album(args.project_id, args.album_id, company_id=args.company_id)

    if args.command == "find-photo-album":
        return find_photo_album(args.project_id, name=args.name, company_id=args.company_id)

    if args.command == "photos":
        return list_photos(
            args.project_id,
            company_id=args.company_id,
            album_id=args.album_id,
            image_category_id=args.image_category_id,
            private=args.private,
            starred=args.starred,
            created_at=args.created_at,
            updated_at=args.updated_at,
            log_date=args.log_date,
            query=args.query,
            uploader_ids=args.uploader_ids,
            location_ids=args.location_ids,
            trade_ids=args.trade_ids,
            projection=args.projection,
            serializer_view=args.serializer_view,
            sort=args.sort,
            page=args.page,
            per_page=args.per_page,
        )

    if args.command == "photo":
        return get_photo(args.project_id, args.photo_id, company_id=args.company_id)

    if args.command == "find-photo":
        return find_photo(
            args.project_id,
            photo_id=args.photo_id,
            filename=args.filename,
            description=args.description,
            query=args.query,
            company_id=args.company_id,
        )

    if args.command == "download-photo":
        output_dir = args.output_dir if args.output_dir is not None else "downloads/photos"
        return download_photo(
            args.project_id,
            args.photo_id,
            output_dir=output_dir,
            company_id=args.company_id,
            overwrite=args.overwrite,
            filename=args.filename,
        )

    if args.command == "download-photo-album":
        output_dir = args.output_dir if args.output_dir is not None else "downloads/photos"
        return download_photo_album(
            args.project_id,
            args.album_id,
            output_dir=output_dir,
            company_id=args.company_id,
            overwrite=args.overwrite,
            limit=args.limit,
        )

    if args.command == "daily-log-counts":
        return get_daily_log_counts(
            args.project_id,
            company_id=args.company_id,
            log_date=args.log_date,
            start_date=args.start_date,
            end_date=args.end_date,
        )

    if args.command == "daily-log-headers":
        return list_daily_log_headers(
            args.project_id,
            company_id=args.company_id,
            log_date=args.log_date,
            start_date=args.start_date,
            end_date=args.end_date,
        )

    if args.command == "daily-log-header":
        return get_daily_log_header(
            args.project_id,
            header_id=args.header_id,
            log_date=args.log_date,
            company_id=args.company_id,
        )

    if args.command == "daily-logs":
        return list_daily_logs(
            args.project_id,
            args.log_type,
            company_id=args.company_id,
            log_date=args.log_date,
            start_date=args.start_date,
            end_date=args.end_date,
            page=args.page,
            per_page=args.per_page,
        )

    if args.command == "daily-log":
        return get_daily_log(
            args.project_id,
            args.log_type,
            args.log_id,
            company_id=args.company_id,
            log_date=args.log_date,
            start_date=args.start_date,
            end_date=args.end_date,
        )

    if args.command == "daily-logs-date":
        log_types = [item.strip() for item in args.types.split(",")] if args.types else None
        return list_daily_logs_for_date(
            args.project_id,
            company_id=args.company_id,
            log_date=args.log_date,
            log_types=log_types,
        )

    if args.command == "delay-log-types":
        return list_delay_log_types(args.project_id, company_id=args.company_id)

    daily_log_commands = {
        "manpower-logs": list_manpower_logs,
        "notes-logs": list_notes_logs,
        "daily-construction-report-logs": list_daily_construction_report_logs,
        "delay-logs": list_delay_logs,
        "delivery-logs": list_delivery_logs,
        "call-logs": list_call_logs,
        "accident-logs": list_accident_logs,
        "dumpster-logs": list_dumpster_logs,
        "visitor-logs": list_visitor_logs,
        "productivity-logs": list_productivity_logs,
        "plan-revision-logs": list_plan_revision_logs,
    }
    if args.command in daily_log_commands:
        return daily_log_commands[args.command](
            args.project_id,
            company_id=args.company_id,
            log_date=args.log_date,
            start_date=args.start_date,
            end_date=args.end_date,
            page=args.page,
            per_page=args.per_page,
        )

    if args.command == "specification-sets":
        return list_specification_sets(args.project_id, company_id=args.company_id)

    if args.command == "specification-sections":
        return list_specification_sections(
            args.project_id,
            company_id=args.company_id,
            specification_area_id=args.specification_area_id,
            specification_set_id=args.specification_set_id,
            division_id=args.division_id,
            sort=args.sort,
        )

    if args.command == "specification-section":
        return get_specification_section(
            args.project_id,
            args.specification_section_id,
            company_id=args.company_id,
        )

    if args.command == "find-specification-section":
        return find_specification_section(
            args.project_id,
            number=args.number,
            title=args.title,
            query=args.query,
            company_id=args.company_id,
        )

    if args.command == "specification-revisions":
        return list_specification_section_revisions(
            args.project_id,
            company_id=args.company_id,
            specification_section_id=args.specification_section_id,
            page=args.page,
            per_page=args.per_page,
        )

    if args.command == "specification-revision":
        return get_specification_section_revision(
            args.project_id,
            args.revision_id,
            company_id=args.company_id,
        )

    if args.command == "download-specification-revision":
        output_dir = args.output_dir if args.output_dir is not None else "downloads/specifications"
        return download_specification_section_revision(
            args.project_id,
            args.revision_id,
            output_dir=output_dir,
            company_id=args.company_id,
            overwrite=args.overwrite,
        )

    if args.command == "package-rfi":
        return build_workflow_package(_automation_input(args, item_type="rfi"))

    if args.command == "enhanced-rfi-package":
        return build_enhanced_rfi_package(
            args.project_id,
            rfi_id=args.rfi_id,
            rfi_number=args.rfi_number,
            company_id=args.company_id,
            output_dir=args.output_dir,
            include_related=args.include_related,
            related_sections=_split_csv(args.related_sections),
            exclude_related=_split_csv(args.exclude_related),
            search_terms=_split_csv_list(args.search_terms),
            start_date=args.start_date,
            end_date=args.end_date,
            log_date=args.log_date,
            max_related_items=args.max_related_items,
            download_files=args.download_files,
            overwrite=args.overwrite,
            continue_on_error=not args.fail_fast,
        )

    if args.command == "package-submittal":
        return build_workflow_package(_automation_input(args, item_type="submittal"))

    if args.command == "enhanced-submittal-package":
        return build_enhanced_submittal_package(
            args.project_id,
            submittal_id=args.submittal_id,
            submittal_number=args.submittal_number,
            company_id=args.company_id,
            output_dir=args.output_dir,
            include_related=args.include_related,
            related_sections=_split_csv(args.related_sections),
            exclude_related=_split_csv(args.exclude_related),
            search_terms=_split_csv_list(args.search_terms),
            start_date=args.start_date,
            end_date=args.end_date,
            log_date=args.log_date,
            max_related_items=args.max_related_items,
            download_files=args.download_files,
            overwrite=args.overwrite,
            continue_on_error=not args.fail_fast,
        )

    if args.command == "export-rfis":
        return export_rfis_to_csv(
            args.project_id,
            args.output_path,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
        )

    if args.command == "export-submittals":
        return export_submittals_to_csv(
            args.project_id,
            args.output_path,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
        )

    if args.command == "export-observations":
        return export_observations_to_csv(
            args.company_id,
            args.project_id,
            args.output_path,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
        )

    if args.command == "export-punch-items":
        return export_punch_items_to_csv(
            args.company_id,
            args.project_id,
            args.output_path,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
        )

    if args.command == "export-correspondences":
        return export_correspondences_to_csv(
            args.company_id,
            args.project_id,
            args.generic_tool_id,
            args.output_path,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
        )

    if args.command == "export-meetings":
        return export_meetings_to_csv(
            args.company_id,
            args.project_id,
            args.output_path,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
        )

    if args.command == "export-inspections":
        return export_inspections_to_csv(
            args.company_id,
            args.project_id,
            args.output_path,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
        )

    if args.command == "export-incidents":
        return export_incidents_to_csv(
            args.company_id,
            args.project_id,
            args.output_path,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
        )

    if args.command == "ai-review-export":
        return build_ai_review_export(
            args.package_dir,
            output_dir=args.output_dir,
            export_name=args.export_name,
            format=args.format,
            include_json=args.include_json,
            include_prompt=args.include_prompt,
            include_checklists=args.include_checklists,
            max_chunk_chars=args.max_chunk_chars,
            overwrite=args.overwrite,
        )

    if args.command == "ai-prompt-pack":
        return build_ai_prompt_pack(
            args.package_dir,
            output_dir=args.output_dir,
            review_type=args.review_type,
            max_chunk_chars=args.max_chunk_chars,
            overwrite=args.overwrite,
        )

    if args.command == "sync-rfis":
        return sync_rfis_to_folder(
            args.project_id,
            args.output_path,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
            download_attachments=args.download_attachments,
            overwrite=args.overwrite,
            create_tracker=args.create_tracker,
            create_markdown=args.create_markdown,
            dry_run=args.dry_run,
            incremental=getattr(args, "incremental", False),
        )

    if args.command == "sync-submittals":
        return sync_submittals_to_folder(
            args.project_id,
            args.output_path,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
            download_attachments=args.download_attachments,
            overwrite=args.overwrite,
            create_tracker=args.create_tracker,
            create_markdown=args.create_markdown,
            dry_run=args.dry_run,
            incremental=getattr(args, "incremental", False),
        )

    if args.command == "sync-documents":
        return sync_documents_to_folder(
            args.project_id,
            args.output_path,
            folder_id=args.folder_id,
            recursive=args.recursive,
            overwrite=args.overwrite,
            create_tracker=args.create_tracker,
            create_markdown=args.create_markdown,
            dry_run=args.dry_run,
            incremental=args.incremental,
        )

    if args.command == "sync-project":
        if args.rfis_only and args.submittals_only:
            raise ValueError("Use either --rfis-only or --submittals-only, not both.")
        return sync_project_to_folder(
            args.project_id,
            args.output_path,
            include_rfis=not args.submittals_only,
            include_submittals=not args.rfis_only,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
            download_attachments=args.download_attachments,
            overwrite=args.overwrite,
            create_tracker=args.create_tracker,
            create_markdown=args.create_markdown,
            dry_run=args.dry_run,
            incremental=args.incremental,
        )

    if args.command == "project-context":
        return build_project_context_package(
            args.project_id,
            company_id=args.company_id,
            output_dir=args.output_path,
            include=_split_csv(args.include),
            exclude=_split_csv(args.exclude),
            start_date=args.start_date,
            end_date=args.end_date,
            log_date=args.log_date,
            max_items=args.max_items,
            download_files=args.download_files,
            overwrite=args.overwrite,
            continue_on_error=not args.fail_fast,
        )

    raise ValueError(f"Unsupported command: {args.command}")


def _split_csv(value: str | None) -> list[str] | None:
    """Split a comma-separated CLI value."""
    if value is None:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def _requires_public_bind(host: str) -> bool:
    """Return whether a host requires explicit public-bind confirmation."""
    if host.lower() == "localhost":
        return False
    try:
        return not ip_address(host).is_loopback
    except ValueError:
        return True


def _split_csv_list(values: list[str] | None) -> list[str] | None:
    """Split repeated comma-separated CLI values."""
    if values is None:
        return None
    items: list[str] = []
    for value in values:
        items.extend(item.strip() for item in value.split(",") if item.strip())
    return items


def _automation_input(
    args: argparse.Namespace,
    *,
    item_type: Literal["rfi", "submittal"],
) -> AutomationInput:
    """Build automation workflow input from CLI arguments."""
    return AutomationInput(
        company_id=args.company_id,
        project_id=args.project_id,
        project_name=args.project_name,
        project_number=args.project_number,
        item_type=item_type,
        item_id=args.item_id,
        item_number=args.item_number,
        download_attachments=args.download_attachments,
        output_dir=args.output_dir,
    )


def to_serializable(value: Any) -> Any:
    """Convert SDK output into JSON-serializable data."""
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, list):
        return [to_serializable(item) for item in value]
    if isinstance(value, tuple):
        return [to_serializable(item) for item in value]
    if isinstance(value, dict):
        return {key: to_serializable(item) for key, item in value.items()}
    if isinstance(value, Path):
        return str(value)
    return value


def _webhook_filters_from_args(args: argparse.Namespace) -> dict[str, str | None]:
    """Return webhook event store filters from parsed CLI arguments."""
    return {
        "company_id": args.company_id,
        "project_id": args.project_id,
        "resource_type": args.resource_type,
        "resource_id": args.resource_id,
        "event_type": args.event_type,
        "action": args.action,
        "date": args.date,
    }


def format_export_summary(path: Path) -> str:
    """Return a human-readable export summary."""
    return f"Export complete.\nOutput: {path}"


def format_sync_summary(result: SyncResult) -> str:
    """Return a human-readable folder sync summary."""
    action = "planned" if result.dry_run else "complete"
    item_word = "planned" if result.dry_run else "synced"
    lines = [
        f"{result.item_type.upper()} sync {action}.",
        f"Project: {result.project_id}",
        f"Items {item_word}: {result.item_count}",
        f"Output: {result.output_dir}",
    ]
    if result.tracker_path is not None:
        tracker_label = "Tracker (planned)" if result.dry_run else "Tracker"
        lines.append(f"{tracker_label}: {result.tracker_path}")
    if result.manifest_path is not None:
        lines.append(f"Manifest: {result.manifest_path}")
    elif result.dry_run:
        lines.append("Manifest: not written during dry run")
    lines.append(f"Attachments downloaded: {len(result.downloaded_files)}")
    if result.warnings:
        lines.append("Warnings:")
        lines.extend(f"- {warning}" for warning in result.warnings)
    if result.errors:
        lines.append("Errors:")
        lines.extend(f"- {error}" for error in result.errors)
    return "\n".join(lines)


def format_project_sync_summary(result: ProjectSyncResult) -> str:
    """Return a human-readable project sync summary."""
    action = "planned" if result.dry_run else "complete"
    return "\n".join(
        [
            f"Project sync {action}.",
            f"Project: {result.project_id}",
            f"Items synced: {result.synced_count}",
            f"Items skipped: {result.skipped_count}",
            f"Output: {result.output_dir}",
            f"Manifest: {result.manifest_path or 'not written during dry run'}",
            f"Summary: {result.summary_path or 'not written during dry run'}",
            f"Warnings: {result.warning_count}",
            f"Errors: {result.error_count}",
        ]
    )


def format_project_context_summary(result: ProjectContextResult) -> str:
    """Return a human-readable project context package summary."""
    manifest = result.manifest
    return "\n".join(
        [
            "Project context package complete.",
            f"Project: {result.project_id}",
            f"Output: {result.output_dir}",
            f"Manifest: {result.manifest_path}",
            f"Summary: {result.summary_path}",
            f"Sections completed: {len(manifest.sections_completed)}",
            f"Sections failed: {len(manifest.sections_failed)}",
            f"Downloads enabled: {manifest.live_downloads_enabled}",
        ]
    )


def format_enhanced_rfi_summary(result: EnhancedRFIPackageResult) -> str:
    """Return a human-readable enhanced RFI package summary."""
    manifest = result.manifest
    return "\n".join(
        [
            "Enhanced RFI package complete.",
            f"Project: {result.project_id}",
            f"RFI: {result.rfi_number or result.rfi_id}",
            f"Output: {result.output_dir}",
            f"Manifest: {result.manifest_path}",
            f"Summary: {result.summary_path}",
            f"Related sections completed: {len(manifest.sections_completed)}",
            f"Related sections failed: {len(manifest.sections_failed)}",
            f"Downloads enabled: {manifest.downloads_enabled}",
        ]
    )


def format_enhanced_submittal_summary(result: EnhancedSubmittalPackageResult) -> str:
    """Return a human-readable enhanced submittal package summary."""
    manifest = result.manifest
    return "\n".join(
        [
            "Enhanced submittal package complete.",
            f"Project: {result.project_id}",
            f"Submittal: {result.submittal_number or result.submittal_id}",
            f"Output: {result.output_dir}",
            f"Manifest: {result.manifest_path}",
            f"Summary: {result.summary_path}",
            f"Approval review: {result.approval_review_path}",
            f"Related sections completed: {len(manifest.sections_completed)}",
            f"Related sections failed: {len(manifest.sections_failed)}",
            f"Downloads enabled: {manifest.downloads_enabled}",
        ]
    )


def format_ai_export_summary(result: AIExportResult) -> str:
    """Return a human-readable AI review export summary."""
    lines = [
        "AI review export complete.",
        f"Package type: {result.package_type}",
        f"Source package: {result.package_dir}",
        f"Output: {result.output_dir}",
        f"Manifest: {result.manifest_path}",
        f"AI review: {result.ai_review_path}",
        f"Source index: {result.source_index_md_path}",
        f"Chunks generated: {len(result.chunk_paths)}",
    ]
    if result.prompt_path is not None:
        lines.append(f"Prompt: {result.prompt_path}")
    if result.system_context_path is not None:
        lines.append(f"System context: {result.system_context_path}")
    if result.ai_review_json_path is not None:
        lines.append(f"JSON export: {result.ai_review_json_path}")
    if result.checklist_paths:
        lines.append(f"Checklists: {len(result.checklist_paths)}")
    if result.manifest.warnings:
        lines.append(f"Warnings: {len(result.manifest.warnings)}")
    if result.manifest.errors:
        lines.append(f"Errors: {len(result.manifest.errors)}")
    return "\n".join(lines)


def format_agent_manifest(manifest: AgentManifest) -> str:
    """Return a human-readable agent manifest summary."""
    return "\n".join(
        [
            "PyProcore agent tool registry.",
            f"Package: {manifest.package_name} {manifest.package_version}",
            f"Registry version: {manifest.registry_version}",
            f"Tools: {manifest.tool_count}",
            "Mode: metadata only; no tools are executed by this command.",
        ]
    )


def format_agent_tools(tools: list[AgentTool]) -> str:
    """Return a human-readable list of registered agent tools."""
    if not tools:
        return "No agent tools are registered."
    lines = [f"Registered agent tools: {len(tools)}"]
    lines.extend(f"- {tool.name}: {tool.title}" for tool in tools)
    return "\n".join(lines)


def format_agent_tool(tool: AgentTool) -> str:
    """Return a human-readable summary of one agent tool."""
    lines = [
        tool.name,
        f"Title: {tool.title}",
        f"Category: {tool.category.value}",
        f"Safety: {tool.safety_level.value}",
        f"Requires auth: {tool.requires_auth}",
        f"Calls live API: {tool.calls_live_api}",
        f"Produces files: {tool.produces_files}",
        f"Description: {tool.description}",
    ]
    if tool.cli_command:
        lines.append(f"CLI: {tool.cli_command}")
    if tool.operation_path:
        lines.append(f"Operation: {tool.operation_path}")
    return "\n".join(lines)


def format_agent_runs(runs: list[AgentRun]) -> str:
    """Return a human-readable list of local Agent API runs."""
    if not runs:
        return "No local Agent API runs found."
    lines = [f"Local Agent API runs: {len(runs)}"]
    for run in runs:
        lines.append(f"- {run.run_id}: {len(run.events)} events, source={run.source}")
    return "\n".join(lines)


def format_agent_run(run: AgentRun) -> str:
    """Return a human-readable summary of one local Agent API run."""
    return "\n".join(
        [
            "Local Agent API run.",
            f"Run ID: {run.run_id}",
            f"Created: {run.created_at}",
            f"Source: {run.source}",
            f"PyProcore: {run.pyprocore_version}",
            f"Registry version: {run.registry_version}",
            f"Events: {len(run.events)}",
            "Mode: replay/audit only; no tools are executed.",
        ]
    )


def format_agent_replay_result(result: AgentReplayResult) -> str:
    """Return a human-readable replay result summary."""
    lines = [
        "Agent run replay complete.",
        f"Run ID: {result.run_id}",
        f"Passed: {result.passed}",
        f"Events checked: {result.event_count}",
        f"Warnings: {len(result.warnings)}",
        f"Errors: {len(result.errors)}",
        "Mode: verification only; no tools were executed.",
    ]
    if result.warnings:
        lines.append("Warning details:")
        lines.extend(f"- {warning}" for warning in result.warnings)
    if result.errors:
        lines.append("Error details:")
        lines.extend(f"- {error}" for error in result.errors)
    return "\n".join(lines)


def format_agent_eval_suites(suites: list[AgentEvalSuite]) -> str:
    """Return a human-readable list of built-in agent eval suites."""
    lines = [f"Built-in agent eval suites: {len(suites)}"]
    lines.extend(f"- {suite.name}: {suite.description}" for suite in suites)
    lines.append("Mode: local deterministic checks only; no Procore or AI calls.")
    return "\n".join(lines)


def format_agent_eval_suite(suite: AgentEvalSuite) -> str:
    """Return a human-readable summary of one agent eval suite."""
    lines = [
        f"Agent eval suite: {suite.name}",
        f"Description: {suite.description}",
        f"Cases: {len(suite.cases)}",
    ]
    lines.extend(f"- {case.case_id}: {case.description}" for case in suite.cases)
    lines.append("Mode: local deterministic checks only; no Procore or AI calls.")
    return "\n".join(lines)


def format_agent_eval_results(result: AgentEvalResult | list[AgentEvalResult]) -> str:
    """Return a human-readable summary of agent eval results."""
    active_results = [result] if isinstance(result, AgentEvalResult) else result
    lines = [format_agent_eval_summary(active_results).rstrip()]
    for suite_result in active_results:
        issue_findings = [
            finding
            for finding in suite_result.findings
            if finding.severity.value in {"warning", "failure"}
        ]
        if issue_findings:
            lines.append("")
            lines.append(f"{suite_result.suite_name} findings:")
            lines.extend(
                f"- {finding.severity.value}: {finding.case_id}: {finding.message}"
                for finding in issue_findings
            )
    lines.append("")
    lines.append("Mode: local deterministic checks only; no Procore or AI calls.")
    return "\n".join(lines)


def agent_eval_exit_code(
    result: AgentEvalResult | list[AgentEvalResult],
    *,
    fail_on_warning: bool = False,
) -> int:
    """Return the CLI exit code for agent eval results."""
    active_results = [result] if isinstance(result, AgentEvalResult) else result
    has_failure = any(not suite_result.passed for suite_result in active_results)
    has_warning = any(suite_result.warnings > 0 for suite_result in active_results)
    return 1 if has_failure or (fail_on_warning and has_warning) else 0


def format_workflow_plan_validation(plan: WorkflowPlan) -> str:
    """Return a human-readable workflow plan validation summary."""
    enabled_count = sum(1 for step in plan.steps if step.enabled)
    return "\n".join(
        [
            "Workflow plan is valid.",
            f"Name: {plan.name}",
            f"Steps: {len(plan.steps)}",
            f"Enabled steps: {enabled_count}",
        ]
    )


def format_workflow_run_summary(result: WorkflowRunResult) -> str:
    """Return a human-readable workflow plan run summary."""
    return "\n".join(
        [
            "Workflow plan run complete.",
            f"Plan: {result.plan.name}",
            f"Status: {result.status}",
            f"Dry run: {result.dry_run}",
            f"Output: {result.output_dir}",
            f"Manifest: {result.manifest_path}",
            f"Summary: {result.summary_path}",
            f"Resolved plan: {result.resolved_plan_path}",
            f"Steps: {len(result.manifest.steps)}",
            f"Warnings: {len(result.manifest.warnings)}",
            f"Errors: {len(result.manifest.errors)}",
        ]
    )


def format_webhook_event_summary(event: WebhookEvent) -> str:
    """Return a human-readable webhook event summary."""
    lines = [
        "Webhook event is valid.",
        f"Event ID: {event.event_id}",
        f"Event type: {event.event_type or 'unknown'}",
        f"Action: {event.action or 'unknown'}",
        f"Resource: {event.resource_type or 'unknown'} {event.resource_id or ''}".rstrip(),
        f"Company: {event.company_id or 'unknown'}",
        f"Project: {event.project_id or 'unknown'}",
    ]
    if event.warnings:
        lines.append("Warnings:")
        lines.extend(f"- {warning}" for warning in event.warnings)
    return "\n".join(lines)


def format_webhook_store_summary(result: WebhookEventStoreResult) -> str:
    """Return a human-readable webhook save summary."""
    return "\n".join(
        [
            "Webhook event saved.",
            f"Event ID: {result.event.event_id}",
            f"Original payload: {result.original_path}",
            f"Normalized event: {result.normalized_path}",
        ]
    )


def format_webhook_events_list(events: list[WebhookEvent]) -> str:
    """Return a human-readable list of webhook event summaries."""
    if not events:
        return "No saved webhook events found."
    lines = [f"Saved webhook events: {len(events)}"]
    for event in events:
        lines.append(
            " - ".join(
                [
                    event.event_id,
                    event.event_type or "unknown",
                    event.action or "unknown",
                    event.resource_type or "unknown",
                    event.resource_id or "unknown",
                    f"project={event.project_id or 'unknown'}",
                ]
            )
        )
    return "\n".join(lines)


def format_webhook_dispatch_summary(result: WebhookDispatchResult) -> str:
    """Return a human-readable webhook dispatch summary."""
    lines = [
        "Webhook dispatch complete.",
        f"Event ID: {result.event.event_id}",
        f"Dispatched: {result.dispatched}",
        f"Dry run: {result.dry_run}",
        f"Message: {result.message}",
    ]
    if result.workflow_plan is not None:
        lines.append(f"Workflow plan: {result.workflow_plan}")
    if result.workflow_result is not None:
        lines.extend(
            [
                f"Workflow status: {result.workflow_result.status}",
                f"Workflow output: {result.workflow_result.output_dir}",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    """Run the CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args()
    try:
        result = run_command(args)
    except ConfigurationError as exc:
        print(format_configuration_error(exc))
        raise SystemExit(1) from exc
    except ValidationError as exc:
        print(f"PyProcore input is invalid.\n\nDetails: {exc}")
        raise SystemExit(1) from exc
    except ValueError as exc:
        print(f"PyProcore input is invalid.\n\nDetails: {exc}")
        raise SystemExit(1) from exc
    except AgentToolNotFoundError as exc:
        print(f"PyProcore agent tool lookup failed.\n\nDetails: {exc}")
        raise SystemExit(1) from exc
    except FileNotFoundError as exc:
        print(f"PyProcore local file was not found.\n\nDetails: {exc}")
        raise SystemExit(1) from exc
    except (AuthorizationError, ResourceNotFoundError, ProcoreAPIError) as exc:
        print(format_cli_error(exc))
        raise SystemExit(1) from exc
    if isinstance(result, DoctorReport):
        if args.json_output:
            print(json.dumps(to_serializable(result), indent=2, default=str))
        else:
            print(format_doctor_report(result))
        raise SystemExit(result.exit_code)

    if isinstance(result, AuthStatusReport):
        if args.json_output:
            print(json.dumps(to_serializable(result), indent=2, default=str))
        else:
            print(format_auth_status(result))
        raise SystemExit(result.exit_code)

    if isinstance(result, AuthRefreshResult):
        print(format_auth_refresh(result))
        raise SystemExit(result.exit_code)

    if isinstance(result, AuthExchangeResult):
        print(format_auth_exchange(result))
        raise SystemExit(result.exit_code)

    if isinstance(result, AuthClientCredentialsResult):
        print(format_client_credentials_result(result))
        raise SystemExit(result.exit_code)

    if isinstance(result, AuthLoginUrlResult):
        print(format_login_url(result))
        raise SystemExit(0)

    if args.command == "agent" and args.agent_command in {"openapi", "schemas"}:
        if isinstance(result, Path):
            print(f"Agent specification written to: {result}")
        else:
            print(result)
        return

    if args.command == "agent" and args.agent_command == "mcp":
        if args.agent_mcp_command == "stdio":
            return
        if isinstance(result, Path):
            if args.json_output:
                print(json.dumps({"output_path": str(result)}, indent=2))
            else:
                print(f"MCP metadata written to: {result}")
            return
        print(result)
        return

    if args.command == "agent" and args.agent_command == "runs":
        if isinstance(result, Path):
            if args.json_output:
                print(json.dumps({"output_dir": str(result)}, indent=2))
            else:
                print(f"Agent run bundle exported to: {result}")
            return
        if args.json_output or getattr(args, "pretty", False):
            print(json.dumps(to_serializable(result), indent=2, default=str))
            return
        if isinstance(result, AgentRun):
            print(format_agent_run(result))
            return
        if isinstance(result, AgentReplayResult):
            print(format_agent_replay_result(result))
            return
        if isinstance(result, list):
            print(format_agent_runs(result))
            return

    if args.command == "agent" and args.agent_command == "evals":
        if args.agent_evals_command == "list" and isinstance(result, list):
            if args.json_output or args.pretty:
                print(json.dumps(to_serializable(result), indent=2, default=str))
            else:
                print(format_agent_eval_suites(result))
            return
        if args.agent_evals_command == "show" and isinstance(result, AgentEvalSuite):
            if args.json_output or args.pretty:
                print(json.dumps(to_serializable(result), indent=2, default=str))
            else:
                print(format_agent_eval_suite(result))
            return
        if args.agent_evals_command == "run":
            if args.json_output or args.pretty:
                print(export_agent_eval_results_json(result, pretty=True))
            else:
                if args.output is not None:
                    print(f"Agent eval results written to: {args.output}")
                print(format_agent_eval_results(result))
            raise SystemExit(agent_eval_exit_code(result, fail_on_warning=args.fail_on_warning))

    if isinstance(result, AgentManifest):
        if args.json_output or args.pretty:
            print(json.dumps(to_serializable(result), indent=2, default=str))
        else:
            print(format_agent_manifest(result))
        return

    if isinstance(result, AgentTool):
        if args.json_output or args.pretty:
            print(json.dumps(to_serializable(result), indent=2, default=str))
        else:
            print(format_agent_tool(result))
        return

    if isinstance(result, list) and args.command == "agent" and args.agent_command == "tools":
        if args.json_output or args.pretty:
            print(json.dumps(to_serializable(result), indent=2, default=str))
        else:
            print(format_agent_tools(result))
        return

    if args.command == "workflow-plan" and args.workflow_plan_command == "list":
        if args.json_output:
            print(json.dumps(to_serializable(result), indent=2, default=str))
        else:
            print("\n".join(str(item) for item in result))
        return

    if isinstance(result, WorkflowPlan):
        if args.json_output:
            print(json.dumps(to_serializable(result), indent=2, default=str))
        else:
            print(format_workflow_plan_validation(result))
        return

    if isinstance(result, WorkflowRunResult):
        if args.json_output:
            print(json.dumps(to_serializable(result), indent=2, default=str))
        else:
            print(format_workflow_run_summary(result))
        return

    if isinstance(result, WebhookEvent):
        if args.json_output:
            print(json.dumps(to_serializable(result), indent=2, default=str))
        else:
            print(format_webhook_event_summary(result))
        return

    if isinstance(result, WebhookEventStoreResult):
        if args.json_output:
            print(json.dumps(to_serializable(result), indent=2, default=str))
        else:
            print(format_webhook_store_summary(result))
        return

    if isinstance(result, WebhookDispatchResult):
        if args.json_output:
            print(json.dumps(to_serializable(result), indent=2, default=str))
        else:
            print(format_webhook_dispatch_summary(result))
        return

    if isinstance(result, list) and args.command == "webhook" and args.webhook_command == "list":
        if args.json_output:
            print(json.dumps(to_serializable(result), indent=2, default=str))
        else:
            print(format_webhook_events_list(result))
        return

    if isinstance(result, SyncResult):
        print(format_sync_summary(result))
        return

    if isinstance(result, ProjectSyncResult):
        print(format_project_sync_summary(result))
        return

    if isinstance(result, ProjectContextResult):
        print(format_project_context_summary(result))
        return

    if isinstance(result, EnhancedRFIPackageResult):
        print(format_enhanced_rfi_summary(result))
        return

    if isinstance(result, EnhancedSubmittalPackageResult):
        print(format_enhanced_submittal_summary(result))
        return

    if isinstance(result, AIExportResult):
        print(format_ai_export_summary(result))
        return

    if isinstance(result, Path) and args.command in {
        "export-correspondences",
        "export-incidents",
        "export-inspections",
        "export-meetings",
        "export-observations",
        "export-punch-items",
        "export-rfis",
        "export-submittals",
    }:
        print(format_export_summary(result))
        return

    if isinstance(result, Path) and args.command in {
        "download-document",
        "download-drawing",
        "download-photo",
        "download-specification-revision",
    }:
        print(f"Download complete.\nOutput: {result}")
        return

    print(json.dumps(to_serializable(result), indent=2, default=str))


def _main() -> int:
    """Run the CLI entrypoint and return an operating-system exit code."""
    main()
    return 0


def format_configuration_error(exc: ConfigurationError) -> str:
    """Format configuration errors without exposing secrets."""
    return "\n".join(
        [
            "PyProcore configuration is missing or invalid.",
            "",
            "Next steps:",
            "1. Confirm `.env` exists in your current working directory.",
            "2. Run `procore-sdk doctor` to inspect local setup.",
            "3. Fill in the required Procore OAuth settings.",
            "4. Run this command again.",
            "",
            "Required values:",
            "- PROCORE_CLIENT_ID",
            "- PROCORE_CLIENT_SECRET",
            "- PROCORE_REDIRECT_URI",
            "- PROCORE_LOGIN_URL",
            "- PROCORE_API_BASE",
            "- PROCORE_COMPANY_ID",
            "",
            f"Details: {exc}",
        ]
    )


def format_cli_error(exc: AuthorizationError | ResourceNotFoundError | ProcoreAPIError) -> str:
    """Format common SDK errors for safe CLI output."""
    if isinstance(exc, AuthorizationError):
        return format_authorization_error(exc)
    if isinstance(exc, ProcoreAPIError) and exc.status_code == 403:
        return format_authorization_error(exc)
    if isinstance(exc, ResourceNotFoundError):
        return format_not_found_error(exc)
    return format_procore_api_error(exc)


def format_authorization_error(exc: AuthorizationError | ProcoreAPIError) -> str:
    """Format Procore authorization failures without a traceback."""
    if _is_app_not_connected_error(exc):
        return "\n".join(
            [
                "Procore rejected this request.",
                "Reason:",
                "Your OAuth app is not connected to this Procore company.",
                "",
                "Suggested fixes:",
                "- Run `procore-sdk companies` to see companies available to this token",
                "- Confirm the company ID is correct",
                "- Connect/install the OAuth app to that Procore company",
                "- Confirm the OAuth user has access to the company/project",
                "- Confirm production vs sandbox environment",
                "- Try again after reconnecting the app",
            ]
        )

    return "\n".join(
        [
            "Procore rejected this request.",
            "Reason:",
            "Your token is valid, but Procore denied access to this resource.",
            "",
            "Suggested fixes:",
            "- Confirm company_id/project_id are correct",
            "- Confirm the OAuth user has permission",
            "- Confirm the app is connected to the company",
            "- Confirm production vs sandbox environment",
        ]
    )


def format_not_found_error(exc: ResourceNotFoundError) -> str:
    """Format not-found API errors without a traceback."""
    return "\n".join(
        [
            "Procore could not find this resource.",
            "Reason:",
            "The requested company, project, or resource was not found.",
            "",
            "Suggested fixes:",
            "- Confirm the ID values are correct",
            "- Confirm production vs sandbox environment",
            "- Confirm the OAuth user has access to the resource",
            "",
            f"Details: {exc}",
        ]
    )


def format_procore_api_error(exc: ProcoreAPIError) -> str:
    """Format generic Procore API errors without a traceback."""
    status = f"HTTP status: {exc.status_code}" if exc.status_code is not None else None
    lines = [
        "Procore API request failed.",
        "Reason:",
        "Procore returned an error for this request.",
    ]
    if status is not None:
        lines.extend(["", status])
    lines.extend(["", f"Details: {exc}"])
    return "\n".join(lines)


def _is_app_not_connected_error(exc: AuthorizationError | ProcoreAPIError) -> bool:
    """Return whether Procore reported a disconnected OAuth app."""
    return "app is not connected to this company" in _error_text(exc).casefold()


def _error_text(exc: AuthorizationError | ProcoreAPIError) -> str:
    """Return searchable error text from an SDK exception."""
    parts = [str(exc)]
    if isinstance(exc, ProcoreAPIError) and exc.response_body is not None:
        parts.append(json.dumps(exc.response_body, default=str))
    return " ".join(parts)


if __name__ == "__main__":
    raise SystemExit(_main())
