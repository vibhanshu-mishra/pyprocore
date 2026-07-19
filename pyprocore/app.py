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
    build_mcp_stdio_discovery,
    export_agent_eval_results_json,
    export_agent_openapi_json,
    export_agent_openapi_yaml,
    export_agent_run_bundle,
    export_agent_tool_schemas_json,
    export_mcp_capabilities_json,
    export_mcp_manifest_json,
    export_mcp_prompts_json,
    export_mcp_resources_json,
    export_mcp_safety_json,
    export_mcp_tools_json,
    format_agent_eval_summary,
    get_agent_eval_suite,
    get_agent_tool,
    list_agent_eval_suites,
    list_agent_runs,
    list_agent_tools,
    load_agent_run,
    read_mcp_prompt,
    read_mcp_resource,
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
from pyprocore.auth.permissions import (
    build_credential_rotation_checklist,
    explain_credential_rotation,
    explain_sandbox_production_separation,
    explain_token_clearance,
)
from pyprocore.auth.token_store import TokenStore, TokenStoreDiagnostic, inspect_token_store
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
from pyprocore.evals import (
    EvalBaseline,
    EvalFinding,
    EvalHistorySnapshot,
    EvalHistorySummary,
    EvalRegressionResult,
    EvalReport,
    EvalSuite,
    GoldenDataset,
    ModelResponseEvalResult,
    ModelResponseFixture,
    append_eval_history_snapshot,
    baseline_to_summary,
    build_eval_baseline,
    build_eval_history_markdown,
    build_eval_history_snapshot,
    build_regression_report_json,
    build_regression_report_markdown,
    compare_current_to_baseline_file,
    default_eval_threshold_policy,
    eval_baseline_to_json,
    eval_history_to_json,
    eval_report_to_json,
    eval_report_to_markdown,
    golden_dataset_to_json,
    list_builtin_eval_suites,
    load_eval_baseline_from_file,
    load_eval_history_file,
    load_golden_dataset_from_file,
    load_model_response_fixture_from_file,
    model_response_fixture_to_json,
    run_builtin_eval_suites,
    run_golden_dataset_file,
    sample_eval_baseline,
    sample_eval_history_summary,
    sample_eval_report,
    sample_golden_dataset,
    sample_model_response_fixture,
    score_model_response_fixture,
    summarize_eval_history,
    summarize_eval_regressions,
    validate_golden_dataset,
    validate_model_response_fixture,
    write_eval_baseline_json,
    write_eval_report_json,
    write_eval_report_markdown,
    write_regression_report_json,
    write_regression_report_markdown,
)
from pyprocore.plugins import (
    PluginCapability,
    PluginConfig,
    PluginConfigSummary,
    PluginConfigValidationResult,
    PluginExtensionPack,
    PluginExtensionPackValidationResult,
    PluginHookMetadata,
    PluginHookRegistry,
    PluginHookRegistryManifest,
    PluginHookResult,
    PluginHookType,
    PluginManifest,
    PluginRegistry,
    PluginRegistryManifest,
    PluginScaffoldPlan,
    PluginScaffoldResult,
    PluginTemplateKind,
    PluginValidationResult,
    builtin_hook_registry,
    discover_plugins,
    export_extension_pack_template,
    export_plugin_config_template,
    export_plugin_scaffold_sample_plan,
    load_extension_pack_manifest_from_file,
    load_local_plugin_manifest_file,
    load_plugin_config_from_file,
    merge_plugin_config_with_registry_metadata,
    scaffold_extension_pack,
    scaffold_hook_pack,
    scaffold_plugin_config,
    scaffold_plugin_pack,
    validate_extension_pack_manifest,
    validate_plugin_config,
    validate_plugin_manifest,
)
from pyprocore.services import (
    download_document,
    download_drawing,
    download_photo,
    download_photo_album,
    download_rfi_attachments,
    download_specification_section_revision,
    download_submittal_attachments,
    find_action_plan,
    find_calendar_item,
    find_change_event,
    find_commitment,
    find_commitment_contract,
    find_company,
    find_company_user,
    find_contract_payment,
    find_coordination_issue,
    find_correspondence,
    find_department,
    find_direct_cost,
    find_document,
    find_document_folder,
    find_drawing,
    find_drawings_contains,
    find_form,
    find_incident,
    find_inspection,
    find_location,
    find_meeting,
    find_observation,
    find_owner_invoice,
    find_photo,
    find_photo_album,
    find_prime_change_order,
    find_prime_contract,
    find_project,
    find_project_distribution_group,
    find_project_user,
    find_punch_item,
    find_purchase_order_contract,
    find_rfi,
    find_specification_section,
    find_subcontractor_invoice,
    find_submittal,
    find_task,
    find_vendor,
    find_work_order_contract,
    get_action_plan,
    get_billing_period,
    get_calendar_item,
    get_change_event,
    get_change_event_settings,
    get_commitment,
    get_commitment_contract,
    get_company_user,
    get_contract_payment,
    get_coordination_issue,
    get_correspondence,
    get_daily_log,
    get_daily_log_counts,
    get_daily_log_header,
    get_department,
    get_direct_cost,
    get_document,
    get_document_folder,
    get_drawing,
    get_drawing_area,
    get_form,
    get_generic_tool,
    get_incident,
    get_inspection,
    get_location,
    get_meeting,
    get_observation,
    get_owner_invoice,
    get_photo,
    get_photo_album,
    get_prime_change_order,
    get_prime_contract,
    get_prime_contract_summary,
    get_project_distribution_group,
    get_project_incident_configuration,
    get_project_schedule,
    get_project_user,
    get_punch_item,
    get_purchase_order_contract,
    get_rfi,
    get_schedule_import_status,
    get_schedule_integration,
    get_schedule_resource_assignment,
    get_schedule_settings,
    get_schedule_type,
    get_specification_section,
    get_specification_section_revision,
    get_subcontractor_invoice,
    get_submittal,
    get_task,
    get_vendor,
    get_work_order_contract,
    list_accident_logs,
    list_action_plan_change_history_events,
    list_action_plans,
    list_billing_periods,
    list_budget_detail_columns,
    list_budget_details,
    list_budget_view_summary_rows,
    list_budget_views,
    list_calendar_items,
    list_call_logs,
    list_change_event_statuses,
    list_change_event_types,
    list_change_events,
    list_change_order_packages,
    list_commitment_change_orders,
    list_commitment_contracts,
    list_commitments,
    list_companies,
    list_company_inactive_users,
    list_company_users,
    list_contract_payments,
    list_coordination_issue_activity_feed,
    list_coordination_issue_change_history,
    list_coordination_issue_filter_options,
    list_coordination_issues,
    list_correspondences,
    list_cost_codes,
    list_cost_types,
    list_daily_construction_report_logs,
    list_daily_log_headers,
    list_daily_logs,
    list_daily_logs_for_date,
    list_delay_log_types,
    list_delay_logs,
    list_delivery_logs,
    list_departments,
    list_direct_costs,
    list_document_folders,
    list_documents,
    list_drawing_areas,
    list_drawing_disciplines,
    list_drawings,
    list_dumpster_logs,
    list_form_templates,
    list_forms,
    list_generic_tools,
    list_incidents,
    list_inspections,
    list_locations,
    list_manpower_logs,
    list_meetings,
    list_notes_logs,
    list_observations,
    list_owner_invoice_line_items,
    list_owner_invoices,
    list_photo_albums,
    list_photos,
    list_plan_revision_logs,
    list_prime_change_orders,
    list_prime_contract_line_items,
    list_prime_contracts,
    list_productivity_logs,
    list_project_distribution_groups,
    list_project_users,
    list_project_vendors,
    list_projects,
    list_punch_items,
    list_purchase_order_contracts,
    list_requisition_change_order_items,
    list_requisition_contract_detail_items,
    list_requisition_contract_items,
    list_rfis,
    list_schedule_resource_assignments,
    list_specification_section_revisions,
    list_specification_sections,
    list_specification_sets,
    list_subcontractor_invoices,
    list_submittals,
    list_task_requested_changes,
    list_tasks,
    list_tax_codes,
    list_vendors,
    list_visitor_logs,
    list_wbs_codes,
    list_work_order_contracts,
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
    AsyncBatchManifest,
    EnhancedRFIPackageResult,
    EnhancedSubmittalPackageResult,
    EnterpriseReadinessReport,
    ProjectContextResult,
    ProjectSyncResult,
    ScheduledExportManifest,
    ScheduledExportValidationReport,
    SyncResult,
    WorkflowPlan,
    WorkflowRunResult,
    build_ai_prompt_pack,
    build_ai_review_export,
    build_async_batch_dry_run_manifest,
    build_enhanced_rfi_package,
    build_enhanced_submittal_package,
    build_production_runbook_summary,
    build_project_context_package,
    evaluate_private_deployment_config,
    explain_async_batch_plan,
    explain_private_deployment_pattern,
    explain_scheduled_export_plan,
    export_action_plan_change_history_to_csv,
    export_action_plans_to_csv,
    export_billing_periods_to_csv,
    export_budget_details_to_csv,
    export_budget_summary_rows_to_csv,
    export_budget_views_to_csv,
    export_calendar_items_to_csv,
    export_change_events_to_csv,
    export_change_order_packages_to_csv,
    export_commitment_change_orders_to_csv,
    export_commitment_contracts_to_csv,
    export_commitments_to_csv,
    export_company_users_to_csv,
    export_contract_payments_to_csv,
    export_coordination_issue_activity_feed_to_csv,
    export_coordination_issue_change_history_to_csv,
    export_coordination_issue_filter_options_to_csv,
    export_coordination_issues_to_csv,
    export_correspondences_to_csv,
    export_cost_codes_to_csv,
    export_cost_types_to_csv,
    export_departments_to_csv,
    export_direct_costs_to_csv,
    export_distribution_groups_to_csv,
    export_form_templates_to_csv,
    export_forms_to_csv,
    export_incidents_to_csv,
    export_inspections_to_csv,
    export_locations_to_csv,
    export_meetings_to_csv,
    export_observations_to_csv,
    export_owner_invoice_line_items_to_csv,
    export_owner_invoices_to_csv,
    export_plan_to_manifest,
    export_prime_change_orders_to_csv,
    export_prime_contract_line_items_to_csv,
    export_prime_contracts_to_csv,
    export_project_users_to_csv,
    export_punch_items_to_csv,
    export_purchase_order_contracts_to_csv,
    export_requisition_change_order_items_to_csv,
    export_requisition_contract_detail_items_to_csv,
    export_requisition_contract_items_to_csv,
    export_rfis_to_csv,
    export_schedule_resource_assignments_to_csv,
    export_subcontractor_invoices_to_csv,
    export_submittals_to_csv,
    export_task_requested_changes_to_csv,
    export_tasks_to_csv,
    export_tax_codes_to_csv,
    export_vendors_to_csv,
    export_work_order_contracts_to_csv,
    list_available_workflows,
    load_async_batch_plan,
    load_scheduled_export_plan,
    load_workflow_plan,
    run_workflow_plan,
    sample_async_batch_plan_json,
    sample_private_folder_layout,
    sample_scheduled_export_plan_json,
    sync_documents_to_folder,
    sync_project_to_folder,
    sync_rfis_to_folder,
    sync_submittals_to_folder,
    validate_scheduled_export_plan,
    validate_workflow_plan,
    write_async_batch_manifest,
    write_scheduled_export_manifest,
)


class TokenStoreClearResult(BaseModel):
    """Safe result for token-store clear operations."""

    cleared: bool
    path: str
    message: str


class AuthRotationChecklistResult(BaseModel):
    """Safe credential rotation checklist result."""

    auth_mode: str
    summary: str
    checklist: list[str]
    token_clearance: str
    environment_separation: str


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
    rotation_parser = auth_subcommands.add_parser(
        "rotation-checklist",
        help="Print a local credential rotation checklist",
    )
    rotation_parser.add_argument(
        "--auth-mode",
        choices=["authorization_code", "client_credentials"],
        default=None,
        help="Auth mode to explain. Defaults to configured auth mode when available.",
    )
    rotation_parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Print structured JSON output",
    )

    token_store_parser = subcommands.add_parser(
        "token-store",
        help="Inspect or clear the local token store safely",
    )
    token_store_subcommands = token_store_parser.add_subparsers(
        dest="token_store_command",
        required=True,
    )
    token_store_status_parser = token_store_subcommands.add_parser(
        "status",
        help="Show safe token-store status",
    )
    token_store_status_parser.add_argument("--path", type=Path, help="Token store path")
    token_store_status_parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Print structured JSON output",
    )
    token_store_inspect_parser = token_store_subcommands.add_parser(
        "inspect",
        help="Inspect token-store safety without printing tokens",
    )
    token_store_inspect_parser.add_argument("--path", type=Path, help="Token store path")
    token_store_inspect_parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Print structured JSON output",
    )
    token_store_clear_parser = token_store_subcommands.add_parser(
        "clear",
        help="Clear the configured token-store file",
    )
    token_store_clear_parser.add_argument("--path", type=Path, help="Token store path")
    token_store_clear_parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirm token-store clearance without prompting",
    )
    token_store_clear_parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Print structured JSON output",
    )
    token_store_subcommands.add_parser(
        "sample-paths",
        help="Show safe token-store path examples",
    )

    enterprise_parser = subcommands.add_parser(
        "enterprise",
        help="Local private deployment readiness helpers",
    )
    enterprise_subcommands = enterprise_parser.add_subparsers(
        dest="enterprise_command",
        required=True,
    )
    enterprise_readiness_parser = enterprise_subcommands.add_parser(
        "readiness-check",
        help="Evaluate private deployment readiness without live API calls",
    )
    enterprise_readiness_parser.add_argument(
        "--auth-mode",
        choices=["authorization_code", "client_credentials"],
        default="client_credentials",
    )
    enterprise_readiness_parser.add_argument("--environment-name", default=None)
    enterprise_readiness_parser.add_argument("--token-store-path", type=Path)
    enterprise_readiness_parser.add_argument("--output-dir", type=Path)
    enterprise_readiness_parser.add_argument("--log-dir", type=Path)
    enterprise_readiness_parser.add_argument("--plan", type=Path)
    enterprise_readiness_parser.add_argument(
        "--allow-no-dry-run",
        action="store_true",
        help="Warn that scheduled exports are planned without a required dry-run",
    )
    enterprise_readiness_parser.add_argument(
        "--user-workflow",
        action="store_true",
        help="Treat the deployment as a user-driven local workflow",
    )
    enterprise_readiness_parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Print structured JSON output",
    )

    enterprise_pattern_parser = enterprise_subcommands.add_parser(
        "deployment-pattern",
        help="Explain a private deployment pattern",
    )
    enterprise_pattern_parser.add_argument(
        "--pattern",
        choices=["local", "private-server", "cron", "docker"],
        default="local",
    )

    enterprise_layout_parser = enterprise_subcommands.add_parser(
        "sample-layout",
        help="Show a private folder layout example",
    )
    enterprise_layout_parser.add_argument(
        "--root",
        default="/opt/pyprocore",
        help="Example private deployment root",
    )

    enterprise_runbook_parser = enterprise_subcommands.add_parser(
        "runbook-summary",
        help="Print a local production runbook summary",
    )
    enterprise_runbook_parser.add_argument(
        "--auth-mode",
        choices=["authorization_code", "client_credentials"],
        default="client_credentials",
    )

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
    agent_mcp_resources_parser.add_argument("--kind", default=None)

    agent_mcp_prompts_parser = agent_mcp_subcommands.add_parser(
        "prompts",
        help="Export MCP-style prompt definitions",
    )
    agent_mcp_prompts_parser.add_argument("--json", dest="json_output", action="store_true")
    agent_mcp_prompts_parser.add_argument("--pretty", action="store_true")
    agent_mcp_prompts_parser.add_argument("--output", type=Path, default=None)
    agent_mcp_prompts_parser.add_argument("--kind", default=None)

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

    mcp_parser = subcommands.add_parser(
        "mcp",
        help="Inspect discovery-only MCP resources, prompts, and capabilities",
    )
    mcp_subcommands = mcp_parser.add_subparsers(dest="mcp_command", required=True)

    mcp_manifest_parser = mcp_subcommands.add_parser(
        "manifest",
        help="Show the complete discovery-only MCP manifest",
    )
    mcp_manifest_parser.add_argument("--json", dest="json_output", action="store_true")
    mcp_manifest_parser.add_argument("--pretty", action="store_true")
    mcp_manifest_parser.add_argument("--output", type=Path, default=None)

    mcp_resources_parser = mcp_subcommands.add_parser(
        "resources",
        help="List local MCP resources",
    )
    mcp_resources_parser.add_argument("--json", dest="json_output", action="store_true")
    mcp_resources_parser.add_argument("--pretty", action="store_true")
    mcp_resources_parser.add_argument("--output", type=Path, default=None)
    mcp_resources_parser.add_argument("--kind", default=None)

    mcp_resource_parser = mcp_subcommands.add_parser(
        "resource",
        help="Read one local MCP resource by URI",
    )
    mcp_resource_parser.add_argument("uri")
    mcp_resource_parser.add_argument("--json", dest="json_output", action="store_true")
    mcp_resource_parser.add_argument("--pretty", action="store_true")

    mcp_prompts_parser = mcp_subcommands.add_parser(
        "prompts",
        help="List MCP prompt templates",
    )
    mcp_prompts_parser.add_argument("--json", dest="json_output", action="store_true")
    mcp_prompts_parser.add_argument("--pretty", action="store_true")
    mcp_prompts_parser.add_argument("--output", type=Path, default=None)
    mcp_prompts_parser.add_argument("--kind", default=None)

    mcp_prompt_parser = mcp_subcommands.add_parser(
        "prompt",
        help="Show one MCP prompt template by name",
    )
    mcp_prompt_parser.add_argument("name")
    mcp_prompt_parser.add_argument("--json", dest="json_output", action="store_true")
    mcp_prompt_parser.add_argument("--pretty", action="store_true")

    mcp_capabilities_parser = mcp_subcommands.add_parser(
        "capabilities",
        help="Show MCP discovery capability summary",
    )
    mcp_capabilities_parser.add_argument("--json", dest="json_output", action="store_true")
    mcp_capabilities_parser.add_argument("--pretty", action="store_true")
    mcp_capabilities_parser.add_argument("--output", type=Path, default=None)

    mcp_safety_parser = mcp_subcommands.add_parser(
        "safety",
        help="Show MCP discovery safety boundaries",
    )
    mcp_safety_parser.add_argument("--json", dest="json_output", action="store_true")
    mcp_safety_parser.add_argument("--pretty", action="store_true")
    mcp_safety_parser.add_argument("--output", type=Path, default=None)

    mcp_stdio_parser = mcp_subcommands.add_parser(
        "stdio-discovery",
        help="Show stdio-friendly discovery payload without starting a server",
    )
    mcp_stdio_parser.add_argument("--json", dest="json_output", action="store_true")
    mcp_stdio_parser.add_argument("--pretty", action="store_true")
    mcp_stdio_parser.add_argument("--output", type=Path, default=None)

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

    evals_parser = subcommands.add_parser(
        "evals",
        help="Run local deterministic golden dataset evals",
    )
    evals_subcommands = evals_parser.add_subparsers(dest="evals_command", required=True)
    evals_list_parser = evals_subcommands.add_parser(
        "list",
        help="List built-in golden eval suites",
    )
    evals_list_parser.add_argument("--json", dest="json_output", action="store_true")
    evals_list_parser.add_argument("--pretty", action="store_true")
    evals_run_parser = evals_subcommands.add_parser(
        "run",
        help="Run built-in golden evals or one local JSON dataset",
    )
    evals_run_parser.add_argument("--suite", default=None)
    evals_run_parser.add_argument("--dataset", dest="dataset_path", type=Path, default=None)
    evals_run_parser.add_argument("--json", dest="json_output", action="store_true")
    evals_run_parser.add_argument("--pretty", action="store_true")
    evals_run_parser.add_argument("--output", type=Path, default=None)
    evals_run_parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    evals_validate_parser = evals_subcommands.add_parser(
        "validate-dataset",
        help="Validate one local JSON golden dataset without live calls",
    )
    evals_validate_parser.add_argument("dataset_path", type=Path)
    evals_validate_parser.add_argument("--json", dest="json_output", action="store_true")
    evals_validate_parser.add_argument("--pretty", action="store_true")
    evals_report_parser = evals_subcommands.add_parser(
        "report",
        help="Build a local deterministic eval report",
    )
    evals_report_parser.add_argument("--suite", default=None)
    evals_report_parser.add_argument("--dataset", dest="dataset_path", type=Path, default=None)
    evals_report_parser.add_argument("--format", choices=["json", "markdown"], default="json")
    evals_report_parser.add_argument("--output", type=Path, default=None)
    evals_report_parser.add_argument("--json", dest="json_output", action="store_true")
    evals_report_parser.add_argument("--pretty", action="store_true")
    evals_sample_dataset_parser = evals_subcommands.add_parser(
        "sample-dataset",
        help="Print a safe sample golden dataset",
    )
    evals_sample_dataset_parser.add_argument("--json", dest="json_output", action="store_true")
    evals_sample_dataset_parser.add_argument("--pretty", action="store_true")
    evals_sample_report_parser = evals_subcommands.add_parser(
        "sample-report",
        help="Print a safe sample deterministic eval report",
    )
    evals_sample_report_parser.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="json",
    )
    evals_sample_report_parser.add_argument("--json", dest="json_output", action="store_true")
    evals_sample_report_parser.add_argument("--pretty", action="store_true")
    evals_model_fixture_parser = evals_subcommands.add_parser(
        "model-fixture",
        help="Sample, validate, and score offline model-response fixtures",
    )
    evals_model_fixture_subcommands = evals_model_fixture_parser.add_subparsers(
        dest="evals_model_fixture_command",
        required=True,
    )
    evals_model_fixture_sample_parser = evals_model_fixture_subcommands.add_parser(
        "sample",
        help="Print a safe sample model-response fixture",
    )
    evals_model_fixture_sample_parser.add_argument(
        "--json", dest="json_output", action="store_true"
    )
    evals_model_fixture_sample_parser.add_argument("--pretty", action="store_true")
    evals_model_fixture_validate_parser = evals_model_fixture_subcommands.add_parser(
        "validate",
        help="Validate one local JSON model-response fixture without running it",
    )
    evals_model_fixture_validate_parser.add_argument("fixture_path", type=Path)
    evals_model_fixture_validate_parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
    )
    evals_model_fixture_validate_parser.add_argument("--pretty", action="store_true")
    evals_model_fixture_score_parser = evals_model_fixture_subcommands.add_parser(
        "score",
        help="Score one local JSON model-response fixture without model calls",
    )
    evals_model_fixture_score_parser.add_argument("fixture_path", type=Path)
    evals_model_fixture_score_parser.add_argument("--json", dest="json_output", action="store_true")
    evals_model_fixture_score_parser.add_argument("--pretty", action="store_true")
    evals_model_fixture_policy_parser = evals_model_fixture_subcommands.add_parser(
        "policy",
        help="Print offline model-response fixture safety policy notes",
    )
    evals_model_fixture_policy_parser.add_argument(
        "--json", dest="json_output", action="store_true"
    )
    evals_model_fixture_policy_parser.add_argument("--pretty", action="store_true")
    evals_baseline_parser = evals_subcommands.add_parser(
        "baseline",
        help="Create and validate local deterministic eval baselines",
    )
    evals_baseline_subcommands = evals_baseline_parser.add_subparsers(
        dest="evals_baseline_command",
        required=True,
    )
    evals_baseline_sample_parser = evals_baseline_subcommands.add_parser(
        "sample",
        help="Print a safe sample eval baseline",
    )
    evals_baseline_sample_parser.add_argument("--json", dest="json_output", action="store_true")
    evals_baseline_sample_parser.add_argument("--pretty", action="store_true")
    evals_baseline_create_parser = evals_baseline_subcommands.add_parser(
        "create",
        help="Create a local baseline from current deterministic eval results",
    )
    evals_baseline_create_parser.add_argument("--suite", default=None)
    evals_baseline_create_parser.add_argument("--output", type=Path, required=True)
    evals_baseline_create_parser.add_argument("--name", default="pyprocore-local-baseline")
    evals_baseline_create_parser.add_argument("--notes", default=None)
    evals_baseline_create_parser.add_argument("--json", dest="json_output", action="store_true")
    evals_baseline_create_parser.add_argument("--pretty", action="store_true")
    evals_baseline_validate_parser = evals_baseline_subcommands.add_parser(
        "validate",
        help="Validate one local JSON eval baseline",
    )
    evals_baseline_validate_parser.add_argument("baseline_path", type=Path)
    evals_baseline_validate_parser.add_argument("--json", dest="json_output", action="store_true")
    evals_baseline_validate_parser.add_argument("--pretty", action="store_true")
    evals_compare_parser = evals_subcommands.add_parser(
        "compare",
        help="Compare current deterministic eval results to a local baseline",
    )
    evals_compare_parser.add_argument("--baseline", dest="baseline_path", type=Path, required=True)
    evals_compare_parser.add_argument("--suite", default=None)
    evals_compare_parser.add_argument("--json", dest="json_output", action="store_true")
    evals_compare_parser.add_argument("--pretty", action="store_true")
    evals_regression_report_parser = evals_subcommands.add_parser(
        "regression-report",
        help="Build a JSON or Markdown regression report from a local baseline",
    )
    evals_regression_report_parser.add_argument(
        "--baseline",
        dest="baseline_path",
        type=Path,
        required=True,
    )
    evals_regression_report_parser.add_argument("--suite", default=None)
    evals_regression_report_parser.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="json",
    )
    evals_regression_report_parser.add_argument("--output", type=Path, default=None)
    evals_regression_report_parser.add_argument("--json", dest="json_output", action="store_true")
    evals_regression_report_parser.add_argument("--pretty", action="store_true")
    evals_history_parser = evals_subcommands.add_parser(
        "history",
        help="Create and summarize local deterministic eval history snapshots",
    )
    evals_history_subcommands = evals_history_parser.add_subparsers(
        dest="evals_history_command",
        required=True,
    )
    evals_history_sample_parser = evals_history_subcommands.add_parser(
        "sample",
        help="Print a safe sample eval history summary",
    )
    evals_history_sample_parser.add_argument("--json", dest="json_output", action="store_true")
    evals_history_sample_parser.add_argument("--pretty", action="store_true")
    evals_history_append_parser = evals_history_subcommands.add_parser(
        "append",
        help="Append a current deterministic eval snapshot to a local history file",
    )
    evals_history_append_parser.add_argument("--suite", default=None)
    evals_history_append_parser.add_argument("--output", type=Path, required=True)
    evals_history_append_parser.add_argument("--label", default=None)
    evals_history_append_parser.add_argument("--json", dest="json_output", action="store_true")
    evals_history_append_parser.add_argument("--pretty", action="store_true")
    evals_history_summary_parser = evals_history_subcommands.add_parser(
        "summary",
        help="Summarize a local JSON eval history file",
    )
    evals_history_summary_parser.add_argument("history_path", type=Path)
    evals_history_summary_parser.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="markdown",
    )
    evals_history_summary_parser.add_argument("--json", dest="json_output", action="store_true")
    evals_history_summary_parser.add_argument("--pretty", action="store_true")

    plugins_parser = subcommands.add_parser(
        "plugins",
        help="Inspect safe metadata-only plugin manifests",
    )
    plugins_subcommands = plugins_parser.add_subparsers(dest="plugins_command", required=True)
    plugins_list_parser = plugins_subcommands.add_parser(
        "list",
        help="List registered metadata-only plugins",
    )
    plugins_list_parser.add_argument("--json", dest="json_output", action="store_true")
    plugins_list_parser.add_argument("--pretty", action="store_true")
    plugins_show_parser = plugins_subcommands.add_parser(
        "show",
        help="Show one metadata-only plugin manifest",
    )
    plugins_show_parser.add_argument("name")
    plugins_show_parser.add_argument("--json", dest="json_output", action="store_true")
    plugins_show_parser.add_argument("--pretty", action="store_true")
    plugins_manifest_parser = plugins_subcommands.add_parser(
        "manifest",
        help="Export the safe plugin registry manifest",
    )
    plugins_manifest_parser.add_argument("--json", dest="json_output", action="store_true")
    plugins_manifest_parser.add_argument("--pretty", action="store_true")
    plugins_sample_parser = plugins_subcommands.add_parser(
        "sample-manifest",
        help="Print a placeholder plugin manifest",
    )
    plugins_sample_parser.add_argument("--json", dest="json_output", action="store_true")
    plugins_sample_parser.add_argument("--pretty", action="store_true")
    plugins_validate_parser = plugins_subcommands.add_parser(
        "validate",
        help="Validate a local JSON plugin manifest without executing plugin code",
    )
    plugins_validate_parser.add_argument("manifest_path", type=Path)
    plugins_validate_parser.add_argument("--json", dest="json_output", action="store_true")
    plugins_validate_parser.add_argument("--pretty", action="store_true")
    plugins_hooks_parser = plugins_subcommands.add_parser(
        "hooks",
        help="List explicitly registered built-in safe local plugin hooks",
    )
    plugins_hooks_parser.add_argument("--type", dest="hook_type", default=None)
    plugins_hooks_parser.add_argument("--json", dest="json_output", action="store_true")
    plugins_hooks_parser.add_argument("--pretty", action="store_true")
    plugins_hook_manifest_parser = plugins_subcommands.add_parser(
        "hook-manifest",
        help="Export the safe local hook registry manifest",
    )
    plugins_hook_manifest_parser.add_argument("--json", dest="json_output", action="store_true")
    plugins_hook_manifest_parser.add_argument("--pretty", action="store_true")
    plugins_sample_hook_parser = plugins_subcommands.add_parser(
        "sample-hook-manifest",
        help="Print a placeholder plugin manifest with hook metadata",
    )
    plugins_sample_hook_parser.add_argument("--json", dest="json_output", action="store_true")
    plugins_sample_hook_parser.add_argument("--pretty", action="store_true")
    plugins_sample_validator_parser = plugins_subcommands.add_parser(
        "run-sample-validator",
        help="Run a built-in validator hook against deterministic sample data",
    )
    plugins_sample_validator_parser.add_argument("--json", dest="json_output", action="store_true")
    plugins_sample_validator_parser.add_argument("--pretty", action="store_true")
    plugins_sample_formatter_parser = plugins_subcommands.add_parser(
        "run-sample-formatter",
        help="Run a built-in formatter hook against deterministic sample data",
    )
    plugins_sample_formatter_parser.add_argument("--json", dest="json_output", action="store_true")
    plugins_sample_formatter_parser.add_argument("--pretty", action="store_true")
    plugins_config_parser = plugins_subcommands.add_parser(
        "config",
        help="Inspect safe JSON plugin configuration metadata",
    )
    plugins_config_subcommands = plugins_config_parser.add_subparsers(
        dest="plugins_config_command",
        required=True,
    )
    plugins_config_sample_parser = plugins_config_subcommands.add_parser(
        "sample",
        help="Print a safe plugin config template",
    )
    plugins_config_sample_parser.add_argument("--json", dest="json_output", action="store_true")
    plugins_config_sample_parser.add_argument("--pretty", action="store_true")
    plugins_config_validate_parser = plugins_config_subcommands.add_parser(
        "validate",
        help="Validate a local JSON plugin config without executing code",
    )
    plugins_config_validate_parser.add_argument("config_path", type=Path)
    plugins_config_validate_parser.add_argument("--json", dest="json_output", action="store_true")
    plugins_config_validate_parser.add_argument("--pretty", action="store_true")
    plugins_config_summary_parser = plugins_config_subcommands.add_parser(
        "summary",
        help="Summarize a local JSON plugin config without executing code",
    )
    plugins_config_summary_parser.add_argument("config_path", type=Path)
    plugins_config_summary_parser.add_argument("--json", dest="json_output", action="store_true")
    plugins_config_summary_parser.add_argument("--pretty", action="store_true")
    plugins_config_manifest_parser = plugins_config_subcommands.add_parser(
        "manifest",
        help="Apply plugin config preferences to registered metadata",
    )
    plugins_config_manifest_parser.add_argument("config_path", type=Path)
    plugins_config_manifest_parser.add_argument("--json", dest="json_output", action="store_true")
    plugins_config_manifest_parser.add_argument("--pretty", action="store_true")
    plugins_pack_parser = plugins_subcommands.add_parser(
        "extension-pack",
        help="Inspect safe local extension-pack metadata",
    )
    plugins_pack_subcommands = plugins_pack_parser.add_subparsers(
        dest="plugins_extension_pack_command",
        required=True,
    )
    plugins_pack_sample_parser = plugins_pack_subcommands.add_parser(
        "sample",
        help="Print a safe extension-pack template",
    )
    plugins_pack_sample_parser.add_argument("--json", dest="json_output", action="store_true")
    plugins_pack_sample_parser.add_argument("--pretty", action="store_true")
    plugins_pack_validate_parser = plugins_pack_subcommands.add_parser(
        "validate",
        help="Validate a local JSON extension-pack manifest",
    )
    plugins_pack_validate_parser.add_argument("extension_pack_path", type=Path)
    plugins_pack_validate_parser.add_argument("--json", dest="json_output", action="store_true")
    plugins_pack_validate_parser.add_argument("--pretty", action="store_true")
    plugins_pack_summary_parser = plugins_pack_subcommands.add_parser(
        "summary",
        help="Summarize a local JSON extension-pack manifest",
    )
    plugins_pack_summary_parser.add_argument("extension_pack_path", type=Path)
    plugins_pack_summary_parser.add_argument("--json", dest="json_output", action="store_true")
    plugins_pack_summary_parser.add_argument("--pretty", action="store_true")
    plugins_scaffold_parser = plugins_subcommands.add_parser(
        "scaffold",
        help="Create safe local plugin template scaffolds without executing code",
    )
    plugins_scaffold_subcommands = plugins_scaffold_parser.add_subparsers(
        dest="plugins_scaffold_command",
        required=True,
    )
    plugins_scaffold_sample_parser = plugins_scaffold_subcommands.add_parser(
        "sample-plan",
        help="Print a safe scaffold plan without writing files",
    )
    plugins_scaffold_sample_parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
    )
    plugins_scaffold_sample_parser.add_argument("--pretty", action="store_true")
    plugins_scaffold_dry_run_parser = plugins_scaffold_subcommands.add_parser(
        "dry-run",
        help="Preview a plugin scaffold without writing files",
    )
    _add_plugin_scaffold_options(plugins_scaffold_dry_run_parser)
    plugins_scaffold_create_parser = plugins_scaffold_subcommands.add_parser(
        "create",
        help="Write a plugin scaffold under the selected output directory",
    )
    _add_plugin_scaffold_options(plugins_scaffold_create_parser)
    plugins_scaffold_extension_parser = plugins_scaffold_subcommands.add_parser(
        "extension-pack",
        help="Write an extension-pack manifest scaffold",
    )
    _add_plugin_scaffold_options(plugins_scaffold_extension_parser, include_kind=False)
    plugins_scaffold_config_parser = plugins_scaffold_subcommands.add_parser(
        "config",
        help="Write a plugin config scaffold",
    )
    _add_plugin_scaffold_options(plugins_scaffold_config_parser, include_kind=False)
    plugins_scaffold_hook_parser = plugins_scaffold_subcommands.add_parser(
        "hook-pack",
        help="Write a hook manifest scaffold",
    )
    _add_plugin_scaffold_options(plugins_scaffold_hook_parser, include_kind=False)

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

    company_users_parser = subcommands.add_parser(
        "company-users",
        help="List company directory users",
    )
    _add_company_options(company_users_parser)
    company_users_parser.add_argument("--inactive", action="store_true")

    company_user_parser = subcommands.add_parser("company-user", help="Get one company user")
    _add_company_options(company_user_parser)
    company_user_parser.add_argument("--id", "--user-id", dest="user_id", type=int, required=True)

    find_company_user_parser = subcommands.add_parser(
        "find-company-user",
        help="Find one company user by name, email, or text",
    )
    _add_company_options(find_company_user_parser)
    _add_name_email_query_options(find_company_user_parser)

    project_users_parser = subcommands.add_parser(
        "project-users",
        help="List project directory users",
    )
    _add_project_company_options(project_users_parser)
    project_users_parser.add_argument("--inactive", action="store_true")

    project_user_parser = subcommands.add_parser("project-user", help="Get one project user")
    _add_project_company_options(project_user_parser)
    project_user_parser.add_argument("--id", "--user-id", dest="user_id", type=int, required=True)

    find_project_user_parser = subcommands.add_parser(
        "find-project-user",
        help="Find one project user by name, email, or text",
    )
    _add_project_company_options(find_project_user_parser)
    _add_name_email_query_options(find_project_user_parser)

    vendors_parser = subcommands.add_parser("vendors", help="List company or project vendors")
    _add_company_options(vendors_parser)
    vendors_parser.add_argument("--project", "--project-id", dest="project_id", type=int)

    vendor_parser = subcommands.add_parser("vendor", help="Get one vendor")
    _add_company_options(vendor_parser)
    vendor_parser.add_argument("--id", "--vendor-id", dest="vendor_id", type=int, required=True)

    find_vendor_parser = subcommands.add_parser(
        "find-vendor",
        help="Find one vendor by name, number, or text",
    )
    _add_company_options(find_vendor_parser)
    _add_name_number_query_options(find_vendor_parser)

    departments_parser = subcommands.add_parser("departments", help="List company departments")
    _add_company_options(departments_parser)

    department_parser = subcommands.add_parser("department", help="Get one department")
    _add_company_options(department_parser)
    department_parser.add_argument(
        "--id",
        "--department-id",
        dest="department_id",
        type=int,
        required=True,
    )

    find_department_parser = subcommands.add_parser(
        "find-department",
        help="Find one department by name, code, or text",
    )
    _add_company_options(find_department_parser)
    _add_name_code_query_options(find_department_parser)

    distribution_groups_parser = subcommands.add_parser(
        "distribution-groups",
        help="List project distribution groups",
    )
    _add_project_company_options(distribution_groups_parser)

    distribution_group_parser = subcommands.add_parser(
        "distribution-group",
        help="Get one project distribution group",
    )
    _add_project_company_options(distribution_group_parser)
    distribution_group_parser.add_argument(
        "--id",
        "--distribution-group-id",
        dest="distribution_group_id",
        type=int,
        required=True,
    )

    find_distribution_group_parser = subcommands.add_parser(
        "find-distribution-group",
        help="Find one project distribution group by name or text",
    )
    _add_project_company_options(find_distribution_group_parser)
    _add_name_query_options(find_distribution_group_parser)

    locations_parser = subcommands.add_parser("locations", help="List project locations")
    _add_project_company_options(locations_parser)

    location_parser = subcommands.add_parser("location", help="Get one project location")
    _add_project_company_options(location_parser)
    location_parser.add_argument(
        "--id",
        "--location-id",
        dest="location_id",
        type=int,
        required=True,
    )

    find_location_parser = subcommands.add_parser(
        "find-location",
        help="Find one project location by name, code, or text",
    )
    _add_project_company_options(find_location_parser)
    _add_name_code_query_options(find_location_parser)

    change_events_parser = subcommands.add_parser("change-events", help="List change events")
    _add_project_company_options(change_events_parser)
    _add_filter_options(change_events_parser)

    change_event_parser = subcommands.add_parser("change-event", help="Get one change event")
    _add_project_company_options(change_event_parser)
    change_event_parser.add_argument(
        "--id", "--change-event-id", dest="change_event_id", type=int, required=True
    )

    find_change_event_parser = subcommands.add_parser(
        "find-change-event", help="Find one change event"
    )
    _add_project_company_options(find_change_event_parser)
    _add_name_number_query_options(find_change_event_parser)

    change_event_statuses_parser = subcommands.add_parser(
        "change-event-statuses", help="List change event statuses"
    )
    _add_project_company_options(change_event_statuses_parser)

    change_event_types_parser = subcommands.add_parser(
        "change-event-types", help="List change event types"
    )
    _add_project_company_options(change_event_types_parser)

    change_event_settings_parser = subcommands.add_parser(
        "change-event-settings", help="Get change event settings"
    )
    _add_project_company_options(change_event_settings_parser)

    prime_change_orders_parser = subcommands.add_parser(
        "prime-change-orders", help="List prime change orders"
    )
    _add_project_company_options(prime_change_orders_parser)
    _add_filter_options(prime_change_orders_parser)

    prime_change_order_parser = subcommands.add_parser(
        "prime-change-order", help="Get one prime change order"
    )
    _add_project_company_options(prime_change_order_parser)
    prime_change_order_parser.add_argument(
        "--id", "--prime-change-order-id", dest="prime_change_order_id", type=int, required=True
    )

    find_prime_change_order_parser = subcommands.add_parser(
        "find-prime-change-order", help="Find one prime change order"
    )
    _add_project_company_options(find_prime_change_order_parser)
    _add_name_number_query_options(find_prime_change_order_parser)

    commitment_change_orders_parser = subcommands.add_parser(
        "commitment-change-orders", help="List commitment change orders"
    )
    _add_project_company_options(commitment_change_orders_parser)

    change_order_packages_parser = subcommands.add_parser(
        "change-order-packages", help="List change order packages"
    )
    _add_project_company_options(change_order_packages_parser)

    direct_costs_parser = subcommands.add_parser("direct-costs", help="List direct costs")
    _add_project_company_options(direct_costs_parser)
    _add_filter_options(direct_costs_parser)

    direct_cost_parser = subcommands.add_parser("direct-cost", help="Get one direct cost")
    _add_project_company_options(direct_cost_parser)
    direct_cost_parser.add_argument(
        "--id", "--direct-cost-id", dest="direct_cost_id", type=int, required=True
    )

    find_direct_cost_parser = subcommands.add_parser(
        "find-direct-cost", help="Find one direct cost"
    )
    _add_project_company_options(find_direct_cost_parser)
    _add_name_number_query_options(find_direct_cost_parser)

    budget_views_parser = subcommands.add_parser("budget-views", help="List budget views")
    _add_project_company_options(budget_views_parser)

    budget_detail_columns_parser = subcommands.add_parser(
        "budget-detail-columns", help="List budget detail columns"
    )
    _add_project_company_options(budget_detail_columns_parser)
    budget_detail_columns_parser.add_argument(
        "--budget-view", "--budget-view-id", dest="budget_view_id", type=int, required=True
    )

    budget_details_parser = subcommands.add_parser("budget-details", help="List budget details")
    _add_project_company_options(budget_details_parser)
    budget_details_parser.add_argument(
        "--budget-view", "--budget-view-id", dest="budget_view_id", type=int, required=True
    )

    budget_summary_rows_parser = subcommands.add_parser(
        "budget-summary-rows", help="List budget summary rows"
    )
    _add_project_company_options(budget_summary_rows_parser)
    budget_summary_rows_parser.add_argument(
        "--budget-view", "--budget-view-id", dest="budget_view_id", type=int, required=True
    )

    cost_codes_parser = subcommands.add_parser("cost-codes", help="List company cost codes")
    _add_company_options(cost_codes_parser)

    wbs_codes_parser = subcommands.add_parser("wbs-codes", help="List project WBS codes")
    _add_project_company_options(wbs_codes_parser)

    commitments_parser = subcommands.add_parser("commitments", help="List commitments")
    _add_project_company_options(commitments_parser)

    commitment_parser = subcommands.add_parser("commitment", help="Get one commitment")
    _add_project_company_options(commitment_parser)
    commitment_parser.add_argument(
        "--id", "--commitment-id", dest="commitment_id", type=int, required=True
    )

    find_commitment_parser = subcommands.add_parser("find-commitment", help="Find one commitment")
    _add_project_company_options(find_commitment_parser)
    _add_name_number_query_options(find_commitment_parser)

    for command_name, help_text, id_dest in (
        ("prime-contract", "Get one prime contract", "prime_contract_id"),
        ("commitment-contract", "Get one commitment contract", "commitment_contract_id"),
        (
            "purchase-order-contract",
            "Get one purchase order contract",
            "purchase_order_contract_id",
        ),
        ("work-order-contract", "Get one work order contract", "work_order_contract_id"),
        ("subcontractor-invoice", "Get one subcontractor invoice", "subcontractor_invoice_id"),
        ("contract-payment", "Get one contract payment", "contract_payment_id"),
        ("billing-period", "Get one billing period", "billing_period_id"),
    ):
        item_parser = subcommands.add_parser(command_name, help=help_text)
        _add_project_company_options(item_parser)
        item_parser.add_argument("--id", dest=id_dest, type=int, required=True)

    for command_name, help_text in (
        ("prime-contracts", "List prime contracts"),
        ("commitment-contracts", "List commitment contracts"),
        ("purchase-order-contracts", "List purchase order contracts"),
        ("work-order-contracts", "List work order contracts"),
        ("subcontractor-invoices", "List subcontractor invoices"),
        ("contract-payments", "List contract payments"),
        ("billing-periods", "List billing periods"),
    ):
        list_parser = subcommands.add_parser(command_name, help=help_text)
        _add_project_company_options(list_parser)
        _add_filter_options(list_parser)

    for command_name, help_text in (
        ("find-prime-contract", "Find one prime contract"),
        ("find-commitment-contract", "Find one commitment contract"),
        ("find-purchase-order-contract", "Find one purchase order contract"),
        ("find-work-order-contract", "Find one work order contract"),
        ("find-subcontractor-invoice", "Find one subcontractor invoice"),
        ("find-contract-payment", "Find one contract payment"),
    ):
        find_parser = subcommands.add_parser(command_name, help=help_text)
        _add_project_company_options(find_parser)
        _add_name_number_query_options(find_parser)

    prime_contract_line_items_parser = subcommands.add_parser(
        "prime-contract-line-items", help="List prime contract line items"
    )
    _add_project_company_options(prime_contract_line_items_parser)
    prime_contract_line_items_parser.add_argument(
        "--prime-contract", "--prime-contract-id", dest="prime_contract_id", type=int, required=True
    )

    prime_contract_summary_parser = subcommands.add_parser(
        "prime-contract-summary", help="Get prime contract summary"
    )
    _add_project_company_options(prime_contract_summary_parser)
    prime_contract_summary_parser.add_argument(
        "--prime-contract", "--prime-contract-id", dest="prime_contract_id", type=int, required=True
    )

    owner_invoices_parser = subcommands.add_parser("owner-invoices", help="List owner invoices")
    _add_project_company_options(owner_invoices_parser)
    owner_invoices_parser.add_argument(
        "--prime-contract", "--prime-contract-id", dest="prime_contract_id", type=int, required=True
    )
    _add_filter_options(owner_invoices_parser)

    payment_applications_parser = subcommands.add_parser(
        "payment-applications", help="List payment applications"
    )
    _add_project_company_options(payment_applications_parser)
    payment_applications_parser.add_argument(
        "--prime-contract", "--prime-contract-id", dest="prime_contract_id", type=int, required=True
    )
    _add_filter_options(payment_applications_parser)

    owner_invoice_parser = subcommands.add_parser("owner-invoice", help="Get one owner invoice")
    _add_project_company_options(owner_invoice_parser)
    owner_invoice_parser.add_argument(
        "--prime-contract", "--prime-contract-id", dest="prime_contract_id", type=int, required=True
    )
    owner_invoice_parser.add_argument(
        "--id", "--owner-invoice-id", dest="owner_invoice_id", type=int, required=True
    )

    find_owner_invoice_parser = subcommands.add_parser(
        "find-owner-invoice", help="Find one owner invoice"
    )
    _add_project_company_options(find_owner_invoice_parser)
    find_owner_invoice_parser.add_argument(
        "--prime-contract", "--prime-contract-id", dest="prime_contract_id", type=int, required=True
    )
    _add_name_number_query_options(find_owner_invoice_parser)

    owner_invoice_line_items_parser = subcommands.add_parser(
        "owner-invoice-line-items", help="List owner invoice line items"
    )
    _add_project_company_options(owner_invoice_line_items_parser)
    owner_invoice_line_items_parser.add_argument(
        "--prime-contract", "--prime-contract-id", dest="prime_contract_id", type=int, required=True
    )
    owner_invoice_line_items_parser.add_argument(
        "--owner-invoice", "--owner-invoice-id", dest="owner_invoice_id", type=int, required=True
    )

    for command_name, help_text in (
        ("requisition-contract-items", "List requisition contract items"),
        ("requisition-contract-detail-items", "List requisition contract detail items"),
        ("requisition-change-order-items", "List requisition change order items"),
    ):
        requisition_parser = subcommands.add_parser(command_name, help=help_text)
        _add_project_company_options(requisition_parser)
        requisition_parser.add_argument(
            "--requisition", "--requisition-id", dest="requisition_id", type=int, required=True
        )

    cost_types_parser = subcommands.add_parser("cost-types", help="List company cost types")
    _add_company_options(cost_types_parser)

    tax_codes_parser = subcommands.add_parser("tax-codes", help="List company tax codes")
    _add_company_options(tax_codes_parser)

    for command_name, help_text in (
        ("project-schedule", "Get read-only project schedule metadata"),
        ("schedule-settings", "Get read-only project schedule settings"),
        ("schedule-type", "Get read-only project schedule type metadata"),
        ("schedule-integration", "Get read-only project schedule integration metadata"),
        ("schedule-import-status", "Get read-only project schedule import status"),
        ("schedule-resource-assignments", "List schedule resource assignments"),
        ("tasks", "List project tasks"),
        ("calendar-items", "List project calendar items"),
        ("coordination-issues", "List project coordination issues"),
        ("forms", "List project forms"),
        ("form-templates", "List project form templates"),
        ("action-plans", "List project action plans"),
    ):
        project_management_parser = subcommands.add_parser(command_name, help=help_text)
        _add_project_company_options(project_management_parser)
        _add_filter_options(project_management_parser)

    for command_name, help_text, id_dest in (
        ("schedule-resource-assignment", "Get one schedule resource assignment", "assignment_id"),
        ("task", "Get one project task", "task_id"),
        ("calendar-item", "Get one project calendar item", "calendar_item_id"),
        ("coordination-issue", "Get one project coordination issue", "coordination_issue_id"),
        ("form", "Get one project form", "form_id"),
        ("action-plan", "Get one project action plan", "action_plan_id"),
    ):
        project_management_item_parser = subcommands.add_parser(command_name, help=help_text)
        _add_project_company_options(project_management_item_parser)
        project_management_item_parser.add_argument("--id", dest=id_dest, type=int, required=True)

    for command_name, help_text in (
        ("find-task", "Find one task by number, title, or text"),
        ("find-calendar-item", "Find one calendar item by number, title, or text"),
        ("find-coordination-issue", "Find one coordination issue by number, title, or text"),
        ("find-form", "Find one form by number, title, or text"),
        ("find-action-plan", "Find one action plan by number, title, or text"),
    ):
        project_management_find_parser = subcommands.add_parser(command_name, help=help_text)
        _add_project_company_options(project_management_find_parser)
        _add_number_title_query_options(project_management_find_parser)

    task_requested_changes_parser = subcommands.add_parser(
        "task-requested-changes",
        help="List read-only requested changes for one task",
    )
    _add_project_company_options(task_requested_changes_parser)
    task_requested_changes_parser.add_argument(
        "--task",
        "--task-id",
        dest="task_id",
        type=int,
        required=True,
    )
    _add_filter_options(task_requested_changes_parser)

    coordination_issue_change_history_parser = subcommands.add_parser(
        "coordination-issue-change-history",
        help="List read-only change history for one coordination issue",
    )
    _add_project_company_options(coordination_issue_change_history_parser)
    coordination_issue_change_history_parser.add_argument(
        "--coordination-issue",
        "--coordination-issue-id",
        dest="coordination_issue_id",
        type=int,
        required=True,
    )
    _add_filter_options(coordination_issue_change_history_parser)

    coordination_issue_activity_feed_parser = subcommands.add_parser(
        "coordination-issue-activity-feed",
        help="List read-only activity feed entries for one coordination issue",
    )
    _add_project_company_options(coordination_issue_activity_feed_parser)
    coordination_issue_activity_feed_parser.add_argument(
        "--coordination-issue",
        "--coordination-issue-id",
        dest="coordination_issue_id",
        type=int,
        required=True,
    )
    _add_filter_options(coordination_issue_activity_feed_parser)

    coordination_issue_filter_options_parser = subcommands.add_parser(
        "coordination-issue-filter-options",
        help="List read-only coordination issue filter options",
    )
    _add_project_company_options(coordination_issue_filter_options_parser)
    coordination_issue_filter_options_parser.add_argument("--option-type", default=None)
    _add_filter_options(coordination_issue_filter_options_parser)

    action_plan_change_history_parser = subcommands.add_parser(
        "action-plan-change-history",
        help="List read-only change history events for one action plan",
    )
    _add_project_company_options(action_plan_change_history_parser)
    action_plan_change_history_parser.add_argument(
        "--action-plan",
        "--action-plan-id",
        dest="action_plan_id",
        type=int,
        required=True,
    )
    _add_filter_options(action_plan_change_history_parser)

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

    export_company_users_parser = subcommands.add_parser(
        "export-company-users",
        help="Export company directory users to CSV",
    )
    _add_company_options(export_company_users_parser)
    export_company_users_parser.add_argument(
        "--output",
        dest="output_path",
        type=Path,
        required=True,
        help="CSV output path",
    )

    export_project_users_parser = subcommands.add_parser(
        "export-project-users",
        help="Export project directory users to CSV",
    )
    _add_project_company_options(export_project_users_parser)
    export_project_users_parser.add_argument(
        "--output",
        dest="output_path",
        type=Path,
        required=True,
        help="CSV output path",
    )

    export_vendors_parser = subcommands.add_parser(
        "export-vendors",
        help="Export vendors to CSV",
    )
    _add_company_options(export_vendors_parser)
    export_vendors_parser.add_argument(
        "--output",
        dest="output_path",
        type=Path,
        required=True,
        help="CSV output path",
    )

    export_departments_parser = subcommands.add_parser(
        "export-departments",
        help="Export company departments to CSV",
    )
    _add_company_options(export_departments_parser)
    export_departments_parser.add_argument(
        "--output",
        dest="output_path",
        type=Path,
        required=True,
        help="CSV output path",
    )

    export_distribution_groups_parser = subcommands.add_parser(
        "export-distribution-groups",
        help="Export project distribution groups to CSV",
    )
    _add_project_company_options(export_distribution_groups_parser)
    export_distribution_groups_parser.add_argument(
        "--output",
        dest="output_path",
        type=Path,
        required=True,
        help="CSV output path",
    )

    export_locations_parser = subcommands.add_parser(
        "export-locations",
        help="Export project locations to CSV",
    )
    _add_project_company_options(export_locations_parser)
    export_locations_parser.add_argument(
        "--output",
        dest="output_path",
        type=Path,
        required=True,
        help="CSV output path",
    )

    for command_name, help_text, needs_budget_view in (
        ("export-change-events", "Export project change events to CSV", False),
        ("export-prime-change-orders", "Export project prime change orders to CSV", False),
        (
            "export-commitment-change-orders",
            "Export project commitment change orders to CSV",
            False,
        ),
        ("export-change-order-packages", "Export project change order packages to CSV", False),
        ("export-direct-costs", "Export project direct costs to CSV", False),
        ("export-budget-views", "Export project budget views to CSV", False),
        ("export-budget-details", "Export project budget details to CSV", True),
        ("export-budget-summary-rows", "Export project budget summary rows to CSV", True),
        ("export-commitments", "Export project commitments to CSV", False),
        ("export-prime-contracts", "Export project prime contracts to CSV", False),
        ("export-commitment-contracts", "Export project commitment contracts to CSV", False),
        (
            "export-purchase-order-contracts",
            "Export project purchase order contracts to CSV",
            False,
        ),
        ("export-work-order-contracts", "Export project work order contracts to CSV", False),
        ("export-subcontractor-invoices", "Export project subcontractor invoices to CSV", False),
        ("export-contract-payments", "Export project contract payments to CSV", False),
        ("export-billing-periods", "Export project billing periods to CSV", False),
        (
            "export-schedule-resource-assignments",
            "Export schedule resource assignments to CSV",
            False,
        ),
        ("export-tasks", "Export project tasks to CSV", False),
        ("export-calendar-items", "Export project calendar items to CSV", False),
        ("export-coordination-issues", "Export project coordination issues to CSV", False),
        (
            "export-coordination-issue-filter-options",
            "Export coordination issue filter options to CSV",
            False,
        ),
        ("export-forms", "Export project forms to CSV", False),
        ("export-form-templates", "Export project form templates to CSV", False),
        ("export-action-plans", "Export project action plans to CSV", False),
    ):
        export_parser = subcommands.add_parser(command_name, help=help_text)
        _add_project_company_options(export_parser)
        if needs_budget_view:
            export_parser.add_argument(
                "--budget-view",
                "--budget-view-id",
                dest="budget_view_id",
                type=int,
                required=True,
            )
        export_parser.add_argument(
            "--output",
            dest="output_path",
            type=Path,
            required=True,
            help="CSV output path",
        )

    export_task_requested_changes_parser = subcommands.add_parser(
        "export-task-requested-changes",
        help="Export task requested changes to CSV",
    )
    _add_project_company_options(export_task_requested_changes_parser)
    export_task_requested_changes_parser.add_argument(
        "--task",
        "--task-id",
        dest="task_id",
        type=int,
        required=True,
    )
    export_task_requested_changes_parser.add_argument(
        "--output",
        dest="output_path",
        type=Path,
        required=True,
        help="CSV output path",
    )

    for command_name, help_text in (
        (
            "export-coordination-issue-change-history",
            "Export coordination issue change history to CSV",
        ),
        (
            "export-coordination-issue-activity-feed",
            "Export coordination issue activity feed to CSV",
        ),
    ):
        export_coordination_issue_parser = subcommands.add_parser(command_name, help=help_text)
        _add_project_company_options(export_coordination_issue_parser)
        export_coordination_issue_parser.add_argument(
            "--coordination-issue",
            "--coordination-issue-id",
            dest="coordination_issue_id",
            type=int,
            required=True,
        )
        export_coordination_issue_parser.add_argument(
            "--output",
            dest="output_path",
            type=Path,
            required=True,
            help="CSV output path",
        )

    export_action_plan_change_history_parser = subcommands.add_parser(
        "export-action-plan-change-history",
        help="Export action plan change history events to CSV",
    )
    _add_project_company_options(export_action_plan_change_history_parser)
    export_action_plan_change_history_parser.add_argument(
        "--action-plan",
        "--action-plan-id",
        dest="action_plan_id",
        type=int,
        required=True,
    )
    export_action_plan_change_history_parser.add_argument(
        "--output",
        dest="output_path",
        type=Path,
        required=True,
        help="CSV output path",
    )

    for command_name, help_text in (
        ("export-prime-contract-line-items", "Export prime contract line items to CSV"),
        ("export-owner-invoices", "Export owner invoices to CSV"),
    ):
        export_parser = subcommands.add_parser(command_name, help=help_text)
        _add_project_company_options(export_parser)
        export_parser.add_argument(
            "--prime-contract",
            "--prime-contract-id",
            dest="prime_contract_id",
            type=int,
            required=True,
        )
        export_parser.add_argument("--output", dest="output_path", type=Path, required=True)

    export_owner_invoice_line_items_parser = subcommands.add_parser(
        "export-owner-invoice-line-items",
        help="Export owner invoice line items to CSV",
    )
    _add_project_company_options(export_owner_invoice_line_items_parser)
    export_owner_invoice_line_items_parser.add_argument(
        "--prime-contract",
        "--prime-contract-id",
        dest="prime_contract_id",
        type=int,
        required=True,
    )
    export_owner_invoice_line_items_parser.add_argument(
        "--owner-invoice",
        "--owner-invoice-id",
        dest="owner_invoice_id",
        type=int,
        required=True,
    )
    export_owner_invoice_line_items_parser.add_argument(
        "--output", dest="output_path", type=Path, required=True
    )

    for command_name, help_text in (
        ("export-requisition-contract-items", "Export requisition contract items to CSV"),
        (
            "export-requisition-contract-detail-items",
            "Export requisition contract detail items to CSV",
        ),
        ("export-requisition-change-order-items", "Export requisition change order items to CSV"),
    ):
        export_parser = subcommands.add_parser(command_name, help=help_text)
        _add_project_company_options(export_parser)
        export_parser.add_argument(
            "--requisition",
            "--requisition-id",
            dest="requisition_id",
            type=int,
            required=True,
        )
        export_parser.add_argument("--output", dest="output_path", type=Path, required=True)

    for command_name, help_text in (
        ("export-cost-types", "Export company cost types to CSV"),
        ("export-tax-codes", "Export company tax codes to CSV"),
    ):
        export_parser = subcommands.add_parser(command_name, help=help_text)
        _add_company_options(export_parser)
        export_parser.add_argument("--output", dest="output_path", type=Path, required=True)

    export_cost_codes_parser = subcommands.add_parser(
        "export-cost-codes",
        help="Export company cost codes to CSV",
    )
    _add_company_options(export_cost_codes_parser)
    export_cost_codes_parser.add_argument(
        "--output",
        dest="output_path",
        type=Path,
        required=True,
        help="CSV output path",
    )

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

    scheduled_export_parser = subcommands.add_parser(
        "scheduled-export",
        help="Validate and dry-run local scheduled export plans",
    )
    scheduled_export_subcommands = scheduled_export_parser.add_subparsers(
        dest="scheduled_export_command",
        required=True,
    )
    scheduled_export_sample_parser = scheduled_export_subcommands.add_parser(
        "sample-config",
        help="Print or write a safe scheduled export sample config",
    )
    scheduled_export_sample_parser.add_argument(
        "--auth-mode",
        choices=["authorization_code", "client_credentials"],
        default="client_credentials",
        help="Auth mode to show in the sample",
    )
    scheduled_export_sample_parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write the sample JSON config",
    )

    scheduled_export_validate_parser = scheduled_export_subcommands.add_parser(
        "validate",
        help="Validate a local scheduled export plan without Procore access",
    )
    scheduled_export_validate_parser.add_argument("plan_path", type=Path)
    scheduled_export_validate_parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Print structured JSON output",
    )

    scheduled_export_dry_run_parser = scheduled_export_subcommands.add_parser(
        "dry-run",
        help="Explain what a scheduled export plan would do without calling Procore",
    )
    scheduled_export_dry_run_parser.add_argument("plan_path", type=Path)
    scheduled_export_dry_run_parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Print structured JSON output",
    )
    scheduled_export_dry_run_parser.add_argument(
        "--write-manifest",
        type=Path,
        help="Optional local path to write the dry-run manifest JSON",
    )

    async_batch_parser = subcommands.add_parser(
        "async-batch",
        help="Validate and dry-run async multi-project batch plans",
    )
    async_batch_subcommands = async_batch_parser.add_subparsers(
        dest="async_batch_command",
        required=True,
    )
    async_batch_sample_parser = async_batch_subcommands.add_parser(
        "sample-config",
        help="Print or write a safe async batch sample config",
    )
    async_batch_sample_parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write the sample JSON config",
    )

    async_batch_validate_parser = async_batch_subcommands.add_parser(
        "validate",
        help="Validate an async batch plan without Procore access",
    )
    async_batch_validate_parser.add_argument("plan_path", type=Path)
    async_batch_validate_parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Print structured JSON output",
    )

    async_batch_dry_run_parser = async_batch_subcommands.add_parser(
        "dry-run",
        help="Explain what an async batch plan would do without calling Procore",
    )
    async_batch_dry_run_parser.add_argument("plan_path", type=Path)
    async_batch_dry_run_parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Print structured JSON output",
    )
    async_batch_dry_run_parser.add_argument(
        "--write-manifest",
        type=Path,
        help="Optional local path to write the dry-run manifest JSON",
    )

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


def _add_plugin_scaffold_options(
    parser: argparse.ArgumentParser,
    *,
    include_kind: bool = True,
) -> None:
    """Add safe local plugin scaffold options."""
    parser.add_argument("--name", required=True, help="Safe lowercase plugin metadata name")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--description", default=None)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--json", dest="json_output", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    if include_kind:
        parser.add_argument(
            "--kind",
            choices=[
                PluginTemplateKind.FULL_PACK.value,
                PluginTemplateKind.PLUGIN_MANIFEST.value,
                PluginTemplateKind.PLUGIN_CONFIG.value,
                PluginTemplateKind.EXTENSION_PACK.value,
                PluginTemplateKind.HOOK_MANIFEST.value,
                PluginTemplateKind.README.value,
                PluginTemplateKind.TESTS.value,
                PluginTemplateKind.DOCS.value,
            ],
            default=PluginTemplateKind.FULL_PACK.value,
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


def _add_company_options(parser: argparse.ArgumentParser) -> None:
    """Add shared company-scoped command options."""
    parser.add_argument("--company-id", "--company", dest="company_id", type=int, default=None)


def _add_number_title_query_options(parser: argparse.ArgumentParser) -> None:
    """Add shared resolver options for number/title/text lookup."""
    parser.add_argument("--number", default=None)
    parser.add_argument("--title", default=None)
    parser.add_argument("--query", default=None)


def _add_name_email_query_options(parser: argparse.ArgumentParser) -> None:
    """Add shared resolver options for name/email/text lookup."""
    parser.add_argument("--name", default=None)
    parser.add_argument("--email", default=None)
    parser.add_argument("--query", default=None)


def _add_name_number_query_options(parser: argparse.ArgumentParser) -> None:
    """Add shared resolver options for name/number/text lookup."""
    parser.add_argument("--name", default=None)
    parser.add_argument("--number", default=None)
    parser.add_argument("--query", default=None)


def _add_name_code_query_options(parser: argparse.ArgumentParser) -> None:
    """Add shared resolver options for name/code/text lookup."""
    parser.add_argument("--name", default=None)
    parser.add_argument("--code", default=None)
    parser.add_argument("--query", default=None)


def _add_name_query_options(parser: argparse.ArgumentParser) -> None:
    """Add shared resolver options for name/text lookup."""
    parser.add_argument("--name", default=None)
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
        if args.auth_command == "rotation-checklist":
            return build_auth_rotation_checklist(args.auth_mode)
        raise ValueError(f"Unsupported auth command: {args.auth_command}")

    if args.command == "token-store":
        if args.token_store_command in {"status", "inspect"}:
            return inspect_token_store(args.path)
        if args.token_store_command == "clear":
            return clear_token_store_cli(args.path, confirmed=args.yes)
        if args.token_store_command == "sample-paths":
            return token_store_sample_paths()
        raise ValueError(f"Unsupported token-store command: {args.token_store_command}")

    if args.command == "enterprise":
        if args.enterprise_command == "readiness-check":
            return evaluate_private_deployment_config(
                auth_mode=args.auth_mode,
                token_store_path=args.token_store_path,
                export_output_dir=args.output_dir,
                log_dir=args.log_dir,
                environment_name=args.environment_name,
                scheduled_export_plan_path=args.plan,
                dry_run_required=not args.allow_no_dry_run,
                server_to_server=not args.user_workflow,
            )
        if args.enterprise_command == "sample-layout":
            return sample_private_folder_layout(args.root)
        if args.enterprise_command == "runbook-summary":
            return build_production_runbook_summary(args.auth_mode)
        if args.enterprise_command == "deployment-pattern":
            return explain_private_deployment_pattern(args.pattern)
        raise ValueError(f"Unsupported enterprise command: {args.enterprise_command}")

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
                    export_mcp_resources_json(pretty=args.pretty, kind=args.kind),
                    args.output,
                )
            if args.agent_mcp_command == "prompts":
                return _write_optional_output(
                    export_mcp_prompts_json(pretty=args.pretty, kind=args.kind),
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

    if args.command == "mcp":
        if args.mcp_command == "manifest":
            return _write_optional_output(
                export_mcp_manifest_json(pretty=args.pretty),
                args.output,
            )
        if args.mcp_command == "resources":
            return _write_optional_output(
                export_mcp_resources_json(pretty=args.pretty, kind=args.kind),
                args.output,
            )
        if args.mcp_command == "resource":
            return read_mcp_resource(args.uri)
        if args.mcp_command == "prompts":
            return _write_optional_output(
                export_mcp_prompts_json(pretty=args.pretty, kind=args.kind),
                args.output,
            )
        if args.mcp_command == "prompt":
            return read_mcp_prompt(args.name)
        if args.mcp_command == "capabilities":
            return _write_optional_output(
                export_mcp_capabilities_json(pretty=args.pretty),
                args.output,
            )
        if args.mcp_command == "safety":
            return _write_optional_output(
                export_mcp_safety_json(pretty=args.pretty),
                args.output,
            )
        if args.mcp_command == "stdio-discovery":
            discovery_text = json.dumps(
                build_mcp_stdio_discovery(),
                indent=2 if args.pretty else None,
                sort_keys=True,
            )
            return _write_optional_output(discovery_text, args.output)
        raise ValueError(f"Unsupported MCP command: {args.mcp_command}")

    if args.command == "evals":
        if args.evals_command == "list":
            return list_builtin_eval_suites()
        if args.evals_command == "run":
            report = (
                run_golden_dataset_file(args.dataset_path)
                if args.dataset_path is not None
                else run_builtin_eval_suites(suite=args.suite)
            )
            if args.output is not None:
                if args.format == "json":
                    write_eval_report_json(report, args.output, pretty=True)
                else:
                    write_eval_report_markdown(report, args.output)
            return report
        if args.evals_command == "validate-dataset":
            dataset = load_golden_dataset_from_file(args.dataset_path)
            return validate_golden_dataset(dataset)
        if args.evals_command == "report":
            report = (
                run_golden_dataset_file(args.dataset_path)
                if args.dataset_path is not None
                else run_builtin_eval_suites(suite=args.suite)
            )
            if args.output is not None:
                if args.format == "json":
                    write_eval_report_json(report, args.output, pretty=True)
                else:
                    write_eval_report_markdown(report, args.output)
            return report
        if args.evals_command == "sample-dataset":
            return sample_golden_dataset()
        if args.evals_command == "sample-report":
            return sample_eval_report()
        if args.evals_command == "model-fixture":
            if args.evals_model_fixture_command == "sample":
                return sample_model_response_fixture()
            if args.evals_model_fixture_command == "validate":
                fixture = load_model_response_fixture_from_file(args.fixture_path)
                return validate_model_response_fixture(fixture)
            if args.evals_model_fixture_command == "score":
                fixture = load_model_response_fixture_from_file(args.fixture_path)
                return score_model_response_fixture(fixture)
            if args.evals_model_fixture_command == "policy":
                return model_response_fixture_policy_summary()
            raise ValueError(
                f"Unsupported eval model-fixture command: {args.evals_model_fixture_command}"
            )
        if args.evals_command == "baseline":
            if args.evals_baseline_command == "sample":
                return sample_eval_baseline()
            if args.evals_baseline_command == "create":
                report = run_builtin_eval_suites(suite=args.suite)
                baseline = build_eval_baseline(
                    report,
                    baseline_name=args.name,
                    notes=args.notes,
                )
                write_eval_baseline_json(baseline, args.output, pretty=True)
                return baseline
            if args.evals_baseline_command == "validate":
                return load_eval_baseline_from_file(args.baseline_path)
            raise ValueError(f"Unsupported eval baseline command: {args.evals_baseline_command}")
        if args.evals_command == "compare":
            return compare_current_to_baseline_file(
                args.baseline_path,
                suite=args.suite,
                policy=default_eval_threshold_policy(),
            )
        if args.evals_command == "regression-report":
            result = compare_current_to_baseline_file(
                args.baseline_path,
                suite=args.suite,
                policy=default_eval_threshold_policy(),
            )
            if args.output is not None:
                if args.format == "json":
                    write_regression_report_json(result, args.output, pretty=True)
                else:
                    write_regression_report_markdown(result, args.output)
            return result
        if args.evals_command == "history":
            if args.evals_history_command == "sample":
                return sample_eval_history_summary()
            if args.evals_history_command == "append":
                report = run_builtin_eval_suites(suite=args.suite)
                snapshot = build_eval_history_snapshot(report, label=args.label)
                append_eval_history_snapshot(args.output, snapshot)
                return snapshot
            if args.evals_history_command == "summary":
                snapshots = load_eval_history_file(args.history_path)
                return summarize_eval_history(snapshots)
            raise ValueError(f"Unsupported eval history command: {args.evals_history_command}")
        raise ValueError(f"Unsupported evals command: {args.evals_command}")

    if args.command == "plugins":
        registry = build_default_plugin_registry()
        if args.plugins_command == "list":
            return registry.list_plugins()
        if args.plugins_command == "show":
            return registry.get_plugin(args.name)
        if args.plugins_command == "manifest":
            return registry.export_plugin_registry_manifest()
        if args.plugins_command == "sample-manifest":
            return sample_plugin_manifest()
        if args.plugins_command == "validate":
            plugin_manifest = load_local_plugin_manifest_file(args.manifest_path)
            return validate_plugin_manifest(plugin_manifest)
        if args.plugins_command == "hooks":
            hook_registry = build_default_hook_registry()
            if args.hook_type:
                return hook_registry.find_hooks_by_type(args.hook_type)
            return hook_registry.list_hooks()
        if args.plugins_command == "hook-manifest":
            return build_default_hook_registry().export_hook_registry_manifest()
        if args.plugins_command == "sample-hook-manifest":
            return sample_hook_manifest()
        if args.plugins_command == "run-sample-validator":
            return build_default_hook_registry().run_validator_hook(
                "validate_required_fields",
                sample_hook_records(),
                options={"required_fields": ["id", "name"]},
            )
        if args.plugins_command == "run-sample-formatter":
            return build_default_hook_registry().run_formatter_hook(
                "format_records_as_summary",
                sample_hook_records(),
            )
        if args.plugins_command == "config":
            if args.plugins_config_command == "sample":
                return export_plugin_config_template()
            config = load_plugin_config_from_file(args.config_path)
            if args.plugins_config_command == "validate":
                return validate_plugin_config(config)
            if args.plugins_config_command == "summary":
                return config
            if args.plugins_config_command == "manifest":
                return merge_plugin_config_with_registry_metadata(
                    config,
                    registry.list_plugins(),
                )
            raise ValueError(f"Unsupported plugins config command: {args.plugins_config_command}")
        if args.plugins_command == "extension-pack":
            if args.plugins_extension_pack_command == "sample":
                return export_extension_pack_template()
            extension_pack = load_extension_pack_manifest_from_file(args.extension_pack_path)
            if args.plugins_extension_pack_command == "validate":
                return validate_extension_pack_manifest(extension_pack)
            if args.plugins_extension_pack_command == "summary":
                return extension_pack
            raise ValueError(
                "Unsupported plugins extension-pack command: "
                f"{args.plugins_extension_pack_command}"
            )
        if args.plugins_command == "scaffold":
            if args.plugins_scaffold_command == "sample-plan":
                return export_plugin_scaffold_sample_plan()
            if args.plugins_scaffold_command in {"dry-run", "create"}:
                return scaffold_plugin_pack(
                    args.name,
                    args.output_dir,
                    kind=args.kind,
                    description=args.description,
                    overwrite=args.overwrite,
                    dry_run=args.plugins_scaffold_command == "dry-run",
                )
            if args.plugins_scaffold_command == "extension-pack":
                return scaffold_extension_pack(
                    args.name,
                    args.output_dir,
                    overwrite=args.overwrite,
                    dry_run=False,
                )
            if args.plugins_scaffold_command == "config":
                return scaffold_plugin_config(
                    args.name,
                    args.output_dir,
                    overwrite=args.overwrite,
                    dry_run=False,
                )
            if args.plugins_scaffold_command == "hook-pack":
                return scaffold_hook_pack(
                    args.name,
                    args.output_dir,
                    overwrite=args.overwrite,
                    dry_run=False,
                )
            raise ValueError(
                f"Unsupported plugins scaffold command: {args.plugins_scaffold_command}"
            )
        raise ValueError(f"Unsupported plugins command: {args.plugins_command}")

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

    if args.command == "scheduled-export":
        if args.scheduled_export_command == "sample-config":
            sample_json = sample_scheduled_export_plan_json(auth_mode=args.auth_mode)
            if args.output is not None:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(sample_json, encoding="utf-8")
                return args.output
            return sample_json
        if args.scheduled_export_command == "validate":
            return validate_scheduled_export_plan(load_scheduled_export_plan(args.plan_path))
        if args.scheduled_export_command == "dry-run":
            if args.write_manifest is not None:
                return write_scheduled_export_manifest(args.plan_path, args.write_manifest)
            if args.json_output:
                return export_plan_to_manifest(args.plan_path)
            return explain_scheduled_export_plan(args.plan_path)
        raise ValueError(f"Unsupported scheduled-export command: {args.scheduled_export_command}")

    if args.command == "async-batch":
        if args.async_batch_command == "sample-config":
            sample_json = sample_async_batch_plan_json()
            if args.output is not None:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(sample_json, encoding="utf-8")
                return args.output
            return sample_json
        if args.async_batch_command == "validate":
            return build_async_batch_dry_run_manifest(load_async_batch_plan(args.plan_path))
        if args.async_batch_command == "dry-run":
            if args.write_manifest is not None:
                async_batch_manifest = build_async_batch_dry_run_manifest(args.plan_path)
                return write_async_batch_manifest(async_batch_manifest, args.write_manifest)
            if args.json_output:
                return build_async_batch_dry_run_manifest(args.plan_path)
            return explain_async_batch_plan(args.plan_path)
        raise ValueError(f"Unsupported async-batch command: {args.async_batch_command}")

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

    if args.command == "company-users":
        if args.inactive:
            return list_company_inactive_users(args.company_id)
        return list_company_users(args.company_id)

    if args.command == "company-user":
        return get_company_user(args.company_id, args.user_id)

    if args.command == "find-company-user":
        return find_company_user(
            args.company_id,
            name=args.name,
            email=args.email,
            query=args.query,
        )

    if args.command == "project-users":
        return list_project_users(
            args.company_id,
            args.project_id,
            active=False if args.inactive else None,
        )

    if args.command == "project-user":
        return get_project_user(args.company_id, args.project_id, args.user_id)

    if args.command == "find-project-user":
        return find_project_user(
            args.company_id,
            args.project_id,
            name=args.name,
            email=args.email,
            query=args.query,
        )

    if args.command == "vendors":
        if args.project_id is not None:
            return list_project_vendors(args.company_id, args.project_id)
        return list_vendors(args.company_id)

    if args.command == "vendor":
        return get_vendor(args.company_id, args.vendor_id)

    if args.command == "find-vendor":
        return find_vendor(
            args.company_id,
            name=args.name,
            number=args.number,
            query=args.query,
        )

    if args.command == "departments":
        return list_departments(args.company_id)

    if args.command == "department":
        return get_department(args.company_id, args.department_id)

    if args.command == "find-department":
        return find_department(
            args.company_id,
            name=args.name,
            code=args.code,
            query=args.query,
        )

    if args.command == "distribution-groups":
        return list_project_distribution_groups(args.company_id, args.project_id)

    if args.command == "distribution-group":
        return get_project_distribution_group(
            args.company_id,
            args.project_id,
            args.distribution_group_id,
        )

    if args.command == "find-distribution-group":
        return find_project_distribution_group(
            args.company_id,
            args.project_id,
            name=args.name,
            query=args.query,
        )

    if args.command == "locations":
        return list_locations(args.company_id, args.project_id)

    if args.command == "location":
        return get_location(args.company_id, args.project_id, args.location_id)

    if args.command == "find-location":
        return find_location(
            args.company_id,
            args.project_id,
            name=args.name,
            code=args.code,
            query=args.query,
        )

    if args.command == "change-events":
        return list_change_events(
            args.company_id,
            args.project_id,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
        )

    if args.command == "change-event":
        return get_change_event(args.company_id, args.project_id, args.change_event_id)

    if args.command == "find-change-event":
        return find_change_event(
            args.project_id,
            company_id=args.company_id,
            number=args.number,
            name=args.name,
            query=args.query,
        )

    if args.command == "change-event-statuses":
        return list_change_event_statuses(args.company_id, args.project_id)

    if args.command == "change-event-types":
        return list_change_event_types(args.company_id, args.project_id)

    if args.command == "change-event-settings":
        return get_change_event_settings(args.company_id, args.project_id)

    if args.command == "prime-change-orders":
        return list_prime_change_orders(
            args.company_id,
            args.project_id,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
        )

    if args.command == "prime-change-order":
        return get_prime_change_order(args.company_id, args.project_id, args.prime_change_order_id)

    if args.command == "find-prime-change-order":
        return find_prime_change_order(
            args.project_id,
            company_id=args.company_id,
            number=args.number,
            name=args.name,
            query=args.query,
        )

    if args.command == "commitment-change-orders":
        return list_commitment_change_orders(args.company_id, args.project_id)

    if args.command == "change-order-packages":
        return list_change_order_packages(args.company_id, args.project_id)

    if args.command == "direct-costs":
        return list_direct_costs(
            args.company_id,
            args.project_id,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
        )

    if args.command == "direct-cost":
        return get_direct_cost(args.company_id, args.project_id, args.direct_cost_id)

    if args.command == "find-direct-cost":
        return find_direct_cost(
            args.project_id,
            company_id=args.company_id,
            number=args.number,
            name=args.name,
            query=args.query,
        )

    if args.command == "budget-views":
        return list_budget_views(args.company_id, args.project_id)

    if args.command == "budget-detail-columns":
        return list_budget_detail_columns(args.company_id, args.project_id, args.budget_view_id)

    if args.command == "budget-details":
        return list_budget_details(args.company_id, args.project_id, args.budget_view_id)

    if args.command == "budget-summary-rows":
        return list_budget_view_summary_rows(args.company_id, args.project_id, args.budget_view_id)

    if args.command == "cost-codes":
        return list_cost_codes(args.company_id)

    if args.command == "wbs-codes":
        return list_wbs_codes(args.company_id, args.project_id)

    if args.command == "commitments":
        return list_commitments(args.company_id, args.project_id)

    if args.command == "commitment":
        return get_commitment(args.company_id, args.project_id, args.commitment_id)

    if args.command == "find-commitment":
        return find_commitment(
            args.project_id,
            company_id=args.company_id,
            number=args.number,
            name=args.name,
            query=args.query,
        )

    if args.command == "prime-contracts":
        return list_prime_contracts(args.company_id, args.project_id)

    if args.command == "prime-contract":
        return get_prime_contract(args.company_id, args.project_id, args.prime_contract_id)

    if args.command == "find-prime-contract":
        return find_prime_contract(
            args.project_id,
            company_id=args.company_id,
            number=args.number,
            name=args.name,
            query=args.query,
        )

    if args.command == "prime-contract-line-items":
        return list_prime_contract_line_items(
            args.company_id, args.project_id, args.prime_contract_id
        )

    if args.command == "prime-contract-summary":
        return get_prime_contract_summary(args.company_id, args.project_id, args.prime_contract_id)

    if args.command == "commitment-contracts":
        return list_commitment_contracts(args.company_id, args.project_id)

    if args.command == "commitment-contract":
        return get_commitment_contract(
            args.company_id,
            args.project_id,
            args.commitment_contract_id,
        )

    if args.command == "find-commitment-contract":
        return find_commitment_contract(
            args.project_id,
            company_id=args.company_id,
            number=args.number,
            name=args.name,
            query=args.query,
        )

    if args.command == "purchase-order-contracts":
        return list_purchase_order_contracts(args.company_id, args.project_id)

    if args.command == "purchase-order-contract":
        return get_purchase_order_contract(
            args.company_id,
            args.project_id,
            args.purchase_order_contract_id,
        )

    if args.command == "find-purchase-order-contract":
        return find_purchase_order_contract(
            args.project_id,
            company_id=args.company_id,
            number=args.number,
            name=args.name,
            query=args.query,
        )

    if args.command == "work-order-contracts":
        return list_work_order_contracts(args.company_id, args.project_id)

    if args.command == "work-order-contract":
        return get_work_order_contract(
            args.company_id, args.project_id, args.work_order_contract_id
        )

    if args.command == "find-work-order-contract":
        return find_work_order_contract(
            args.project_id,
            company_id=args.company_id,
            number=args.number,
            name=args.name,
            query=args.query,
        )

    if args.command in {"owner-invoices", "payment-applications"}:
        return list_owner_invoices(args.company_id, args.project_id, args.prime_contract_id)

    if args.command == "owner-invoice":
        return get_owner_invoice(
            args.company_id,
            args.project_id,
            args.prime_contract_id,
            args.owner_invoice_id,
        )

    if args.command == "find-owner-invoice":
        return find_owner_invoice(
            args.project_id,
            args.prime_contract_id,
            company_id=args.company_id,
            number=args.number,
            name=args.name,
            query=args.query,
        )

    if args.command == "owner-invoice-line-items":
        return list_owner_invoice_line_items(
            args.company_id,
            args.project_id,
            args.prime_contract_id,
            args.owner_invoice_id,
        )

    if args.command == "subcontractor-invoices":
        return list_subcontractor_invoices(args.company_id, args.project_id)

    if args.command == "subcontractor-invoice":
        return get_subcontractor_invoice(
            args.company_id,
            args.project_id,
            args.subcontractor_invoice_id,
        )

    if args.command == "find-subcontractor-invoice":
        return find_subcontractor_invoice(
            args.project_id,
            company_id=args.company_id,
            number=args.number,
            name=args.name,
            query=args.query,
        )

    if args.command == "requisition-contract-items":
        return list_requisition_contract_items(
            args.company_id, args.project_id, args.requisition_id
        )

    if args.command == "requisition-contract-detail-items":
        return list_requisition_contract_detail_items(
            args.company_id, args.project_id, args.requisition_id
        )

    if args.command == "requisition-change-order-items":
        return list_requisition_change_order_items(
            args.company_id, args.project_id, args.requisition_id
        )

    if args.command == "contract-payments":
        return list_contract_payments(args.company_id, args.project_id)

    if args.command == "contract-payment":
        return get_contract_payment(args.company_id, args.project_id, args.contract_payment_id)

    if args.command == "find-contract-payment":
        return find_contract_payment(
            args.project_id,
            company_id=args.company_id,
            number=args.number,
            name=args.name,
            query=args.query,
        )

    if args.command == "billing-periods":
        return list_billing_periods(args.company_id, args.project_id)

    if args.command == "billing-period":
        return get_billing_period(args.company_id, args.project_id, args.billing_period_id)

    if args.command == "cost-types":
        return list_cost_types(args.company_id)

    if args.command == "tax-codes":
        return list_tax_codes(args.company_id)

    if args.command == "project-schedule":
        return get_project_schedule(args.company_id, args.project_id)

    if args.command == "schedule-settings":
        return get_schedule_settings(args.company_id, args.project_id)

    if args.command == "schedule-type":
        return get_schedule_type(args.company_id, args.project_id)

    if args.command == "schedule-integration":
        return get_schedule_integration(args.company_id, args.project_id)

    if args.command == "schedule-import-status":
        return get_schedule_import_status(args.company_id, args.project_id)

    if args.command == "schedule-resource-assignments":
        return list_schedule_resource_assignments(
            args.company_id,
            args.project_id,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
        )

    if args.command == "schedule-resource-assignment":
        return get_schedule_resource_assignment(
            args.company_id, args.project_id, args.assignment_id
        )

    if args.command == "tasks":
        return list_tasks(
            args.company_id,
            args.project_id,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
        )

    if args.command == "task":
        return get_task(args.company_id, args.project_id, args.task_id)

    if args.command == "find-task":
        return find_task(
            args.project_id,
            company_id=args.company_id,
            number=args.number,
            name=args.title,
            query=args.query,
        )

    if args.command == "task-requested-changes":
        return list_task_requested_changes(
            args.company_id,
            args.project_id,
            args.task_id,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
        )

    if args.command == "calendar-items":
        return list_calendar_items(
            args.company_id,
            args.project_id,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
        )

    if args.command == "calendar-item":
        return get_calendar_item(args.company_id, args.project_id, args.calendar_item_id)

    if args.command == "find-calendar-item":
        return find_calendar_item(
            args.project_id,
            company_id=args.company_id,
            number=args.number,
            name=args.title,
            query=args.query,
        )

    if args.command == "coordination-issues":
        return list_coordination_issues(
            args.company_id,
            args.project_id,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
        )

    if args.command == "coordination-issue":
        return get_coordination_issue(args.company_id, args.project_id, args.coordination_issue_id)

    if args.command == "find-coordination-issue":
        return find_coordination_issue(
            args.project_id,
            company_id=args.company_id,
            number=args.number,
            name=args.title,
            query=args.query,
        )

    if args.command == "coordination-issue-change-history":
        return list_coordination_issue_change_history(
            args.company_id,
            args.project_id,
            args.coordination_issue_id,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
        )

    if args.command == "coordination-issue-activity-feed":
        return list_coordination_issue_activity_feed(
            args.company_id,
            args.project_id,
            args.coordination_issue_id,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
        )

    if args.command == "coordination-issue-filter-options":
        return list_coordination_issue_filter_options(
            args.company_id,
            args.project_id,
            option_type=args.option_type,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
        )

    if args.command == "forms":
        return list_forms(
            args.company_id,
            args.project_id,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
        )

    if args.command == "form":
        return get_form(args.company_id, args.project_id, args.form_id)

    if args.command == "find-form":
        return find_form(
            args.project_id,
            company_id=args.company_id,
            number=args.number,
            name=args.title,
            query=args.query,
        )

    if args.command == "form-templates":
        return list_form_templates(
            args.company_id,
            args.project_id,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
        )

    if args.command == "action-plans":
        return list_action_plans(
            args.company_id,
            args.project_id,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
        )

    if args.command == "action-plan":
        return get_action_plan(args.company_id, args.project_id, args.action_plan_id)

    if args.command == "find-action-plan":
        return find_action_plan(
            args.project_id,
            company_id=args.company_id,
            number=args.number,
            name=args.title,
            query=args.query,
        )

    if args.command == "action-plan-change-history":
        return list_action_plan_change_history_events(
            args.company_id,
            args.project_id,
            args.action_plan_id,
            status=args.status,
            updated_after=args.updated_after,
            updated_before=args.updated_before,
            created_after=args.created_after,
            created_before=args.created_before,
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

    if args.command == "export-company-users":
        return export_company_users_to_csv(args.company_id, args.output_path)

    if args.command == "export-project-users":
        return export_project_users_to_csv(args.company_id, args.project_id, args.output_path)

    if args.command == "export-vendors":
        return export_vendors_to_csv(args.company_id, args.output_path)

    if args.command == "export-departments":
        return export_departments_to_csv(args.company_id, args.output_path)

    if args.command == "export-distribution-groups":
        return export_distribution_groups_to_csv(
            args.company_id,
            args.project_id,
            args.output_path,
        )

    if args.command == "export-locations":
        return export_locations_to_csv(args.company_id, args.project_id, args.output_path)

    if args.command == "export-change-events":
        return export_change_events_to_csv(args.company_id, args.project_id, args.output_path)

    if args.command == "export-prime-change-orders":
        return export_prime_change_orders_to_csv(args.company_id, args.project_id, args.output_path)

    if args.command == "export-commitment-change-orders":
        return export_commitment_change_orders_to_csv(
            args.company_id,
            args.project_id,
            args.output_path,
        )

    if args.command == "export-change-order-packages":
        return export_change_order_packages_to_csv(
            args.company_id, args.project_id, args.output_path
        )

    if args.command == "export-direct-costs":
        return export_direct_costs_to_csv(args.company_id, args.project_id, args.output_path)

    if args.command == "export-budget-views":
        return export_budget_views_to_csv(args.company_id, args.project_id, args.output_path)

    if args.command == "export-budget-details":
        return export_budget_details_to_csv(
            args.company_id,
            args.project_id,
            args.budget_view_id,
            args.output_path,
        )

    if args.command == "export-budget-summary-rows":
        return export_budget_summary_rows_to_csv(
            args.company_id,
            args.project_id,
            args.budget_view_id,
            args.output_path,
        )

    if args.command == "export-cost-codes":
        return export_cost_codes_to_csv(args.company_id, args.output_path)

    if args.command == "export-commitments":
        return export_commitments_to_csv(args.company_id, args.project_id, args.output_path)

    if args.command == "export-prime-contracts":
        return export_prime_contracts_to_csv(args.company_id, args.project_id, args.output_path)

    if args.command == "export-prime-contract-line-items":
        return export_prime_contract_line_items_to_csv(
            args.company_id,
            args.project_id,
            args.prime_contract_id,
            args.output_path,
        )

    if args.command == "export-commitment-contracts":
        return export_commitment_contracts_to_csv(
            args.company_id,
            args.project_id,
            args.output_path,
        )

    if args.command == "export-purchase-order-contracts":
        return export_purchase_order_contracts_to_csv(
            args.company_id,
            args.project_id,
            args.output_path,
        )

    if args.command == "export-work-order-contracts":
        return export_work_order_contracts_to_csv(
            args.company_id,
            args.project_id,
            args.output_path,
        )

    if args.command == "export-owner-invoices":
        return export_owner_invoices_to_csv(
            args.company_id,
            args.project_id,
            args.prime_contract_id,
            args.output_path,
        )

    if args.command == "export-owner-invoice-line-items":
        return export_owner_invoice_line_items_to_csv(
            args.company_id,
            args.project_id,
            args.prime_contract_id,
            args.owner_invoice_id,
            args.output_path,
        )

    if args.command == "export-subcontractor-invoices":
        return export_subcontractor_invoices_to_csv(
            args.company_id,
            args.project_id,
            args.output_path,
        )

    if args.command == "export-requisition-contract-items":
        return export_requisition_contract_items_to_csv(
            args.company_id,
            args.project_id,
            args.requisition_id,
            args.output_path,
        )

    if args.command == "export-requisition-contract-detail-items":
        return export_requisition_contract_detail_items_to_csv(
            args.company_id,
            args.project_id,
            args.requisition_id,
            args.output_path,
        )

    if args.command == "export-requisition-change-order-items":
        return export_requisition_change_order_items_to_csv(
            args.company_id,
            args.project_id,
            args.requisition_id,
            args.output_path,
        )

    if args.command == "export-contract-payments":
        return export_contract_payments_to_csv(args.company_id, args.project_id, args.output_path)

    if args.command == "export-billing-periods":
        return export_billing_periods_to_csv(args.company_id, args.project_id, args.output_path)

    if args.command == "export-cost-types":
        return export_cost_types_to_csv(args.company_id, args.output_path)

    if args.command == "export-tax-codes":
        return export_tax_codes_to_csv(args.company_id, args.output_path)

    if args.command == "export-schedule-resource-assignments":
        return export_schedule_resource_assignments_to_csv(
            args.company_id,
            args.project_id,
            args.output_path,
        )

    if args.command == "export-tasks":
        return export_tasks_to_csv(args.company_id, args.project_id, args.output_path)

    if args.command == "export-task-requested-changes":
        return export_task_requested_changes_to_csv(
            args.company_id,
            args.project_id,
            args.task_id,
            args.output_path,
        )

    if args.command == "export-calendar-items":
        return export_calendar_items_to_csv(args.company_id, args.project_id, args.output_path)

    if args.command == "export-coordination-issues":
        return export_coordination_issues_to_csv(args.company_id, args.project_id, args.output_path)

    if args.command == "export-coordination-issue-change-history":
        return export_coordination_issue_change_history_to_csv(
            args.company_id,
            args.project_id,
            args.coordination_issue_id,
            args.output_path,
        )

    if args.command == "export-coordination-issue-activity-feed":
        return export_coordination_issue_activity_feed_to_csv(
            args.company_id,
            args.project_id,
            args.coordination_issue_id,
            args.output_path,
        )

    if args.command == "export-coordination-issue-filter-options":
        return export_coordination_issue_filter_options_to_csv(
            args.company_id,
            args.project_id,
            args.output_path,
        )

    if args.command == "export-forms":
        return export_forms_to_csv(args.company_id, args.project_id, args.output_path)

    if args.command == "export-form-templates":
        return export_form_templates_to_csv(args.company_id, args.project_id, args.output_path)

    if args.command == "export-action-plans":
        return export_action_plans_to_csv(args.company_id, args.project_id, args.output_path)

    if args.command == "export-action-plan-change-history":
        return export_action_plan_change_history_to_csv(
            args.company_id,
            args.project_id,
            args.action_plan_id,
            args.output_path,
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


def build_default_plugin_registry() -> PluginRegistry:
    """Build a registry containing safe built-in plugin manifests."""
    discovery = discover_plugins()
    registry = PluginRegistry()
    for manifest in discovery.discovered:
        registry.register_plugin_manifest(manifest, source=discovery.source)
    return registry


def build_default_hook_registry() -> PluginHookRegistry:
    """Build a registry containing safe built-in local plugin hooks."""
    return builtin_hook_registry()


def sample_plugin_manifest() -> PluginManifest:
    """Return a placeholder plugin manifest for local experimentation."""
    return PluginManifest(
        name="example_exporter_plugin",
        version="1.0.0",
        description="Placeholder metadata for a future local exporter plugin.",
        author="Your Name",
        homepage="https://example.com/pyprocore-plugin",
        capabilities=[PluginCapability.EXPORTER, PluginCapability.FORMATTER],
        requires_pyprocore=">=2.2.0",
        entry_points={"exporter": "example_package.exporters"},
        tags=["example", "metadata-only"],
        enabled_by_default=False,
        supports_sync=True,
        supports_async=False,
        supports_agent_metadata=False,
        supports_cli=True,
        notes=[
            "Phase 11A validates this metadata only.",
            "No plugin code is installed, imported, or executed.",
        ],
    )


def sample_hook_manifest() -> PluginManifest:
    """Return a placeholder plugin manifest with hook metadata."""
    hook_metadata = [
        PluginHookMetadata(
            hook_name="example_quality_validator",
            plugin_name="example_hook_plugin",
            hook_type=PluginHookType.VALIDATOR,
            description="Example metadata for a local validator hook.",
            input_kind="records",
            output_kind="validation_report",
            notes=[
                "Metadata only. This does not register or execute a callable.",
                "Trusted application code must explicitly register hook callables in-process.",
            ],
        ),
        PluginHookMetadata(
            hook_name="example_summary_formatter",
            plugin_name="example_hook_plugin",
            hook_type=PluginHookType.FORMATTER,
            description="Example metadata for a local formatter hook.",
            input_kind="records",
            output_kind="text",
        ),
    ]
    return PluginManifest(
        name="example_hook_plugin",
        version="1.0.0",
        description="Placeholder metadata for safe local extension hooks.",
        author="Your Name",
        capabilities=[PluginCapability.VALIDATOR, PluginCapability.FORMATTER],
        requires_pyprocore=">=2.2.0",
        tags=["example", "hooks", "metadata-only"],
        supports_sync=True,
        supports_cli=True,
        hooks=hook_metadata,
        notes=[
            "Phase 11B hook metadata is descriptive only.",
            "No remote loading, installation, imports, or Procore calls are performed.",
        ],
    )


def sample_hook_records() -> list[dict[str, object]]:
    """Return deterministic local sample records for safe built-in hook demos."""
    return [
        {"id": 1, "name": "Sample RFI", "status": "open"},
        {"id": 2, "name": "Sample Submittal", "status": "closed"},
    ]


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


def build_auth_rotation_checklist(auth_mode: str | None = None) -> AuthRotationChecklistResult:
    """Build a local-only credential rotation checklist."""
    if auth_mode is None:
        try:
            auth_mode = get_settings().auth_mode.value
        except ConfigurationError:
            auth_mode = "authorization_code"
    return AuthRotationChecklistResult(
        auth_mode=auth_mode,
        summary=explain_credential_rotation(auth_mode),
        checklist=build_credential_rotation_checklist(auth_mode),
        token_clearance=explain_token_clearance(auth_mode),
        environment_separation=explain_sandbox_production_separation(),
    )


def clear_token_store_cli(path: Path | None, *, confirmed: bool) -> TokenStoreClearResult:
    """Clear a token store from CLI input after explicit confirmation."""
    store = TokenStore(path)
    token_path = store.path
    if not confirmed:
        answer = input(
            "This will delete only the token-store file at "
            f"{token_path}. Type CLEAR to continue: "
        )
        if answer.strip() != "CLEAR":
            return TokenStoreClearResult(
                cleared=False,
                path=str(token_path),
                message="Token store was not cleared.",
            )
    store.clear()
    return TokenStoreClearResult(
        cleared=True,
        path=str(token_path),
        message="Token store cleared. Reauthenticate before running authenticated commands.",
    )


def token_store_sample_paths() -> str:
    """Return safe token-store path examples."""
    return "\n".join(
        [
            "Safe token-store path examples:",
            "- macOS/Linux: ~/.config/pyprocore/token_store.json",
            "- CI runtime: $RUNNER_TEMP/pyprocore/token_store.json",
            "- Windows: %APPDATA%\\pyprocore\\token_store.json",
            "",
            "Keep token stores outside the repository and never commit them.",
            "Set PROCORE_TOKEN_STORE_PATH to use a private location.",
            "Use PROCORE_TOKEN_STORE_BACKEND=file for persistent local storage.",
            "Use PROCORE_TOKEN_STORE_BACKEND=memory only for tests/examples.",
        ]
    )


def format_token_store_diagnostic(result: TokenStoreDiagnostic) -> str:
    """Format token-store diagnostics without exposing token values."""
    lines = [
        "PyProcore Token Store",
        f"Backend: {result.backend_type}",
        f"Description: {result.description}",
        f"Path: {result.path or 'not applicable'}",
        f"Exists: {'Yes' if result.exists else 'No'}",
        f"Readable: {'Yes' if result.readable else 'No'}",
        f"Contains token: {'Yes' if result.contains_token else 'No'}",
        f"Access token: {'Present' if result.access_token_present else 'Missing'}",
        f"Refresh token: {'Present' if result.refresh_token_present else 'Missing'}",
        f"Auth mode: {result.auth_mode or 'Unknown'}",
        f"Token status: {result.token_status}",
    ]
    if result.warnings:
        lines.append("Warnings:")
        lines.extend(f"- {warning}" for warning in result.warnings)
    if result.errors:
        lines.append("Errors:")
        lines.extend(f"- {error}" for error in result.errors)
    return "\n".join(lines)


def format_auth_rotation_checklist(result: AuthRotationChecklistResult) -> str:
    """Format credential rotation guidance for humans."""
    lines = [
        "PyProcore Credential Rotation Checklist",
        f"Auth mode: {result.auth_mode}",
        "",
        result.summary,
        "",
        "Checklist:",
    ]
    lines.extend(f"- {item}" for item in result.checklist)
    lines.extend(
        [
            "",
            "Token clearance:",
            result.token_clearance,
            "",
            "Sandbox/production separation:",
            result.environment_separation,
            "",
            "No Procore API calls were made.",
        ]
    )
    return "\n".join(lines)


def format_enterprise_readiness_report(result: EnterpriseReadinessReport) -> str:
    """Format private deployment readiness findings for humans."""
    lines = [
        "PyProcore Enterprise Readiness Check",
        f"Environment: {result.environment_name or 'not provided'}",
        f"Auth mode: {result.auth_mode}",
        f"Token store: {result.token_store_path or 'not provided'}",
        f"Output dir: {result.export_output_dir or 'not provided'}",
        f"Log dir: {result.log_dir or 'not provided'}",
        f"Plan: {result.scheduled_export_plan_path or 'not provided'}",
        f"Dry-run required: {result.dry_run_required}",
        "",
        "Findings:",
    ]
    lines.extend(
        f"- {finding.severity.upper()} {finding.code}: {finding.message}"
        for finding in result.findings
    )
    if result.warnings:
        lines.append("")
        lines.append("Suggested fixes:")
        for finding in result.warnings:
            if finding.suggested_action:
                lines.append(f"- {finding.suggested_action}")
    lines.append("")
    lines.append("No Procore API calls were made.")
    lines.append("Tool execution remains disabled; MCP remains discovery-only.")
    return "\n".join(lines)


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


def format_plugins(plugins: list[PluginManifest]) -> str:
    """Return a human-readable plugin manifest list."""
    if not plugins:
        return "No plugin manifests are registered."
    lines = [f"Registered plugin manifests: {len(plugins)}"]
    lines.extend(
        f"- {plugin.name} {plugin.version}: {', '.join(item.value for item in plugin.capabilities)}"
        for plugin in plugins
    )
    lines.append("Mode: metadata only; no plugin code is installed, imported, or executed.")
    return "\n".join(lines)


def format_plugin(plugin: PluginManifest) -> str:
    """Return a human-readable plugin manifest summary."""
    lines = [
        f"{plugin.name} {plugin.version}",
        f"Description: {plugin.description}",
        f"Safety: {plugin.safety_level.value}",
        f"Capabilities: {', '.join(item.value for item in plugin.capabilities)}",
        f"Requires PyProcore: {plugin.requires_pyprocore or 'not specified'}",
        f"Supports sync: {plugin.supports_sync}",
        f"Supports async: {plugin.supports_async}",
        f"Supports agent metadata: {plugin.supports_agent_metadata}",
        f"Supports CLI metadata: {plugin.supports_cli}",
        "Mode: metadata only; no plugin code is installed, imported, or executed.",
    ]
    if plugin.homepage:
        lines.insert(3, f"Homepage: {plugin.homepage}")
    if plugin.notes:
        lines.append("Notes:")
        lines.extend(f"- {note}" for note in plugin.notes)
    if plugin.hooks:
        lines.append("Hook metadata:")
        lines.extend(
            f"- {hook.hook_name} ({hook.hook_type.value}): {hook.description}"
            for hook in plugin.hooks
        )
        lines.append("Hook metadata does not execute code.")
    return "\n".join(lines)


def format_plugin_registry_manifest(manifest: PluginRegistryManifest) -> str:
    """Return a human-readable plugin registry manifest summary."""
    return "\n".join(
        [
            "PyProcore plugin registry manifest.",
            f"Schema version: {manifest.schema_version}",
            f"Plugins: {manifest.plugin_count}",
            f"Mode: {manifest.mode}",
            "No plugin code is installed, imported, or executed.",
        ]
    )


def format_plugin_validation(result: PluginValidationResult) -> str:
    """Return a human-readable plugin validation result."""
    lines = [
        "Plugin manifest validation complete.",
        f"Valid: {result.valid}",
        "Mode: metadata validation only; no plugin code was executed.",
    ]
    if result.errors:
        lines.append("Errors:")
        lines.extend(f"- {error}" for error in result.errors)
    if result.warnings:
        lines.append("Warnings:")
        lines.extend(f"- {warning}" for warning in result.warnings)
    if result.manifest is not None:
        lines.append(f"Plugin: {result.manifest.name} {result.manifest.version}")
    return "\n".join(lines)


def format_plugin_config(config: PluginConfig) -> str:
    """Return a human-readable plugin config summary."""
    lines = [
        "PyProcore plugin configuration.",
        f"Config version: {config.config_version}",
        f"Safety policy: {config.safety_policy}",
        f"Enabled plugins: {len(config.enabled_plugins)}",
        f"Disabled plugins: {len(config.disabled_plugins)}",
        f"Hook preferences: {len(config.hook_preferences)}",
        f"Extension packs: {len(config.extension_packs)}",
        "Mode: metadata only; no plugin code is loaded, imported, or executed.",
    ]
    if config.enabled_capabilities:
        lines.append(
            "Enabled capabilities: "
            + ", ".join(capability.value for capability in config.enabled_capabilities)
        )
    if config.notes:
        lines.append("Notes:")
        lines.extend(f"- {note}" for note in config.notes)
    return "\n".join(lines)


def format_plugin_config_validation(result: PluginConfigValidationResult) -> str:
    """Return a human-readable plugin config validation result."""
    lines = [
        "Plugin config validation complete.",
        f"Valid: {result.valid}",
        "Mode: JSON metadata validation only; no plugin code was executed.",
    ]
    if result.errors:
        lines.append("Errors:")
        lines.extend(f"- {error}" for error in result.errors)
    if result.warnings:
        lines.append("Warnings:")
        lines.extend(f"- {warning}" for warning in result.warnings)
    return "\n".join(lines)


def format_plugin_config_manifest(summary: PluginConfigSummary) -> str:
    """Return a human-readable configured plugin metadata summary."""
    lines = [
        "Configured plugin metadata summary.",
        f"Config version: {summary.config_version}",
        f"Matched plugins: {len(summary.matched_plugins)}",
        f"Unmatched names: {len(summary.unmatched_plugins)}",
        f"Hook preferences: {len(summary.hook_preferences)}",
        f"Mode: {summary.mode}",
    ]
    if summary.matched_plugins:
        lines.append("Matched plugins:")
        lines.extend(f"- {name}" for name in summary.matched_plugins)
    if summary.unmatched_plugins:
        lines.append("Unmatched names:")
        lines.extend(f"- {name}" for name in summary.unmatched_plugins)
    return "\n".join(lines)


def format_extension_pack(extension_pack: PluginExtensionPack) -> str:
    """Return a human-readable extension-pack summary."""
    lines = [
        "PyProcore extension-pack manifest.",
        f"Name: {extension_pack.name}",
        f"Version: {extension_pack.version}",
        f"Description: {extension_pack.description}",
        f"Safety: {extension_pack.safety_level.value}",
        f"Included plugins: {len(extension_pack.included_plugins)}",
        f"Included hooks: {len(extension_pack.included_hooks)}",
        "Mode: metadata only; no plugin code is loaded, registered, or executed.",
    ]
    if extension_pack.capabilities:
        lines.append(
            "Capabilities: "
            + ", ".join(capability.value for capability in extension_pack.capabilities)
        )
    if extension_pack.notes:
        lines.append("Notes:")
        lines.extend(f"- {note}" for note in extension_pack.notes)
    return "\n".join(lines)


def format_extension_pack_validation(result: PluginExtensionPackValidationResult) -> str:
    """Return a human-readable extension-pack validation result."""
    lines = [
        "Extension-pack validation complete.",
        f"Valid: {result.valid}",
        "Mode: JSON metadata validation only; no plugin code was executed.",
    ]
    if result.errors:
        lines.append("Errors:")
        lines.extend(f"- {error}" for error in result.errors)
    if result.warnings:
        lines.append("Warnings:")
        lines.extend(f"- {warning}" for warning in result.warnings)
    return "\n".join(lines)


def format_plugin_scaffold_plan(plan: PluginScaffoldPlan) -> str:
    """Return a human-readable plugin scaffold plan."""
    lines = [
        "PyProcore plugin scaffold plan.",
        f"Name: {plan.request.name}",
        f"Kind: {plan.request.kind.value}",
        f"Output: {plan.request.output_dir}",
        f"Files planned: {len(plan.files)}",
        "Mode: dry-run only; no files were written or executed.",
    ]
    if plan.files:
        lines.append("Files:")
        lines.extend(f"- {file.path}" for file in plan.files)
    if plan.findings:
        lines.append("Findings:")
        lines.extend(
            f"- {finding.severity.upper()}: {finding.message}" for finding in plan.findings
        )
    return "\n".join(lines)


def format_plugin_scaffold_result(result: PluginScaffoldResult) -> str:
    """Return a human-readable plugin scaffold write result."""
    mode = "dry-run" if result.dry_run else "create"
    lines = [
        "PyProcore plugin scaffold result.",
        f"Name: {result.name}",
        f"Output: {result.output_dir}",
        f"Mode: {mode}; generated files are templates only.",
        f"Files planned: {result.planned_count}",
        f"Files written: {result.written_count}",
        f"Files skipped: {result.skipped_count}",
        f"Overwrite: {result.overwrite}",
        "No generated files were loaded, imported, installed, or executed.",
    ]
    if result.files:
        lines.append("Files:")
        lines.extend(f"- {file.status}: {file.path}" for file in result.files)
    if result.findings:
        lines.append("Findings:")
        lines.extend(
            f"- {finding.severity.upper()}: {finding.message}" for finding in result.findings
        )
    return "\n".join(lines)


def format_plugin_hooks(hooks: list[PluginHookMetadata]) -> str:
    """Return a human-readable plugin hook metadata list."""
    if not hooks:
        return "No plugin hooks are registered."
    lines = [f"Registered plugin hooks: {len(hooks)}"]
    lines.extend(
        f"- {hook.hook_name} ({hook.hook_type.value}): {hook.description}" for hook in hooks
    )
    lines.append(
        "Mode: explicit local hooks only; no plugin code is discovered, imported, or installed."
    )
    return "\n".join(lines)


def format_plugin_hook_manifest(manifest: PluginHookRegistryManifest) -> str:
    """Return a human-readable plugin hook registry manifest summary."""
    return "\n".join(
        [
            "PyProcore plugin hook registry manifest.",
            f"Schema version: {manifest.schema_version}",
            f"Hooks: {manifest.hook_count}",
            f"Mode: {manifest.mode}",
            (
                "Hook metadata is safe to inspect; callables run only after "
                "explicit local registration."
            ),
        ]
    )


def format_plugin_hook_result(result: PluginHookResult) -> str:
    """Return a human-readable plugin hook run result."""
    lines = [
        "Plugin hook run complete.",
        f"Hook: {result.hook_name}",
        f"Plugin: {result.plugin_name}",
        f"Type: {result.hook_type.value}",
        f"Success: {result.success}",
        "Mode: built-in deterministic sample only; no Procore or external calls were made.",
    ]
    if result.errors:
        lines.append("Errors:")
        lines.extend(f"- {error}" for error in result.errors)
    if result.warnings:
        lines.append("Warnings:")
        lines.extend(f"- {warning}" for warning in result.warnings)
    if result.output is not None:
        lines.append("Output:")
        lines.append(json.dumps(to_serializable(result.output), indent=2, default=str))
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


def format_eval_suites(suites: list[EvalSuite]) -> str:
    """Return a human-readable list of built-in golden eval suites."""
    lines = [f"Built-in golden eval suites: {len(suites)}"]
    lines.extend(f"- {suite.name}: {suite.description}" for suite in suites)
    lines.append(
        "Mode: local deterministic fixtures only; no Procore, model, plugin, MCP, "
        "or tool execution."
    )
    return "\n".join(lines)


def format_eval_findings(findings: list[EvalFinding]) -> str:
    """Return a human-readable dataset validation summary."""
    failed = [finding for finding in findings if finding.severity.value == "failure"]
    lines = [
        "Golden dataset validation.",
        f"Findings: {len(findings)}",
        f"Failures: {len(failed)}",
    ]
    lines.extend(
        f"- {finding.severity.value}: {finding.case_id or 'dataset'}: {finding.message}"
        for finding in findings
    )
    lines.append("Mode: local JSON validation only; no live calls were made.")
    return "\n".join(lines)


def format_eval_report(report: EvalReport) -> str:
    """Return a human-readable deterministic eval report."""
    return eval_report_to_markdown(report).rstrip()


def eval_report_exit_code(report: EvalReport) -> int:
    """Return the CLI exit code for a deterministic eval report."""
    return 0 if report.passed else 1


def format_eval_baseline(baseline: EvalBaseline) -> str:
    """Return a human-readable deterministic eval baseline summary."""
    return baseline_to_summary(baseline)


def format_eval_regression_result(result: EvalRegressionResult) -> str:
    """Return a human-readable deterministic regression summary."""
    return summarize_eval_regressions(result)


def eval_regression_exit_code(result: EvalRegressionResult) -> int:
    """Return the CLI exit code for a deterministic regression result."""
    return 0 if result.passed else 1


def format_eval_history_snapshot(snapshot: EvalHistorySnapshot) -> str:
    """Return a human-readable eval history append summary."""
    return "\n".join(
        [
            "PyProcore eval history snapshot appended.",
            f"Label: {snapshot.label or ''}",
            f"Status: {snapshot.status.value}",
            f"Suites: {snapshot.total_suites}",
            f"Cases: {snapshot.passed_cases}/{snapshot.total_cases}",
            f"Score: {snapshot.score}/{snapshot.max_score}",
            "Mode: local deterministic history only; no live calls were made.",
        ]
    )


def format_eval_history_summary(summary: EvalHistorySummary) -> str:
    """Return a human-readable eval history summary."""
    return build_eval_history_markdown(summary).rstrip()


def format_model_response_eval_result(result: ModelResponseEvalResult) -> str:
    """Return a human-readable offline model-response fixture eval summary."""
    lines = [
        "PyProcore offline model-response fixture eval.",
        f"Fixture: {result.fixture_name}",
        f"Workflow: {result.workflow_name}",
        f"Status: {result.status.value}",
        f"Score: {result.score}/{result.max_score}",
        "",
        "Findings:",
    ]
    lines.extend(
        f"- {finding.severity.value}: {finding.check}: {finding.message}"
        for finding in result.findings
    )
    lines.append("")
    lines.append(
        "Mode: local deterministic fixture only; no model, Procore, plugin, MCP, or tool calls."
    )
    return "\n".join(lines)


def model_response_fixture_policy_summary() -> dict[str, object]:
    """Return offline model-response fixture policy notes for the CLI."""
    return {
        "mode": "local_deterministic",
        "external_model_calls": False,
        "live_procore_calls": False,
        "tool_execution": False,
        "plugin_execution": False,
        "mcp_execution": False,
        "checks": [
            "required sections",
            "required and forbidden phrases",
            "citation/source labels",
            "grounding statements",
            "approval/write-action language",
            "fake confidence",
            "limitation disclosures",
            "secret-like values",
            "external model claims",
            "live API call claims",
        ],
    }


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


def format_scheduled_export_validation(result: ScheduledExportValidationReport) -> str:
    """Return a human-readable scheduled export validation summary."""
    lines = [
        "Scheduled export plan validation complete.",
        f"Plan: {result.plan_name}",
        f"Valid: {result.is_valid}",
        f"Errors: {len(result.errors)}",
        f"Warnings: {len(result.warnings)}",
    ]
    if result.findings:
        lines.append("")
        lines.append("Findings:")
        lines.extend(
            f"- {finding.severity.upper()}: {finding.message}" for finding in result.findings
        )
    return "\n".join(lines)


def format_scheduled_export_manifest(result: ScheduledExportManifest) -> str:
    """Return a human-readable scheduled export dry-run summary."""
    lines = [
        "Scheduled export dry run complete.",
        f"Plan: {result.plan_name}",
        f"Auth mode: {result.auth_mode}",
        f"Company: {result.company_id or 'missing'}",
        f"Projects: {', '.join(str(item) for item in result.project_ids) or 'none'}",
        f"Resources: {', '.join(result.resources) or 'none'}",
        f"Output format: {result.output_format}",
        f"Output folder: {result.output_dir}",
        f"Planned files: {len(result.files)}",
        "Mode: local dry-run only; no Procore API calls were made.",
    ]
    if result.findings:
        lines.append("")
        lines.append("Findings:")
        lines.extend(
            f"- {finding.severity.upper()}: {finding.message}" for finding in result.findings
        )
    return "\n".join(lines)


def format_async_batch_manifest(result: AsyncBatchManifest) -> str:
    """Return a human-readable async batch dry-run summary."""
    valid = not any(finding.severity == "error" for finding in result.findings)
    lines = [
        "Async batch dry run complete.",
        f"Plan: {result.plan_name}",
        f"Valid: {valid}",
        f"Company: {result.company_id}",
        f"Projects: {', '.join(str(item) for item in result.project_ids) or 'none'}",
        f"Resources: {', '.join(result.resources) or 'none'}",
        f"Output format: {result.output_format}",
        f"Output folder: {result.output_dir}",
        f"Max concurrency: {result.max_concurrency}",
        f"Planned project/resource files: {len(result.results)}",
        "Mode: local dry-run only; no Procore API calls were made.",
    ]
    if result.findings:
        lines.append("")
        lines.append("Findings:")
        lines.extend(
            f"- {finding.severity.upper()}: {finding.message}" for finding in result.findings
        )
    return "\n".join(lines)


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

    if isinstance(result, AuthRotationChecklistResult):
        if args.json_output:
            print(json.dumps(to_serializable(result), indent=2, default=str))
        else:
            print(format_auth_rotation_checklist(result))
        return

    if isinstance(result, TokenStoreDiagnostic):
        if args.json_output:
            print(json.dumps(to_serializable(result), indent=2, default=str))
        else:
            print(format_token_store_diagnostic(result))
        raise SystemExit(0 if not result.errors else 1)

    if isinstance(result, TokenStoreClearResult):
        if args.json_output:
            print(json.dumps(to_serializable(result), indent=2, default=str))
        else:
            print(result.message)
            print(f"Path: {result.path}")
        return

    if isinstance(result, str) and args.command == "token-store":
        print(result)
        return

    if isinstance(result, EnterpriseReadinessReport):
        if args.json_output:
            print(json.dumps(to_serializable(result), indent=2, default=str))
        else:
            print(format_enterprise_readiness_report(result))
        raise SystemExit(0 if result.passed else 1)

    if args.command == "enterprise":
        if isinstance(result, list):
            print("PyProcore Production Runbook Summary")
            for item in result:
                print(f"- {item}")
            print("No Procore API calls were made.")
        else:
            print(result)
        return

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

    if args.command == "mcp":
        if isinstance(result, Path):
            if args.json_output:
                print(json.dumps({"output_path": str(result)}, indent=2))
            else:
                print(f"MCP metadata written to: {result}")
            return
        if isinstance(result, str):
            print(result)
            return
        print(json.dumps(to_serializable(result), indent=2, default=str))
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

    if args.command == "evals":
        if args.evals_command == "list" and isinstance(result, list):
            if args.json_output or getattr(args, "pretty", False):
                print(json.dumps(to_serializable(result), indent=2, default=str))
            else:
                print(format_eval_suites(result))
            return
        if args.evals_command == "validate-dataset" and isinstance(result, list):
            if args.json_output or getattr(args, "pretty", False):
                print(json.dumps(to_serializable(result), indent=2, default=str))
            else:
                print(format_eval_findings(result))
            raise SystemExit(0 if not any(f.severity.value == "failure" for f in result) else 1)
        if isinstance(result, GoldenDataset):
            print(golden_dataset_to_json(result, pretty=True))
            return
        if isinstance(result, ModelResponseFixture):
            print(model_response_fixture_to_json(result, pretty=True))
            return
        if isinstance(result, ModelResponseEvalResult):
            if args.json_output or getattr(args, "pretty", False):
                print(json.dumps(to_serializable(result), indent=2, default=str))
            else:
                print(format_model_response_eval_result(result))
            raise SystemExit(0 if result.passed else 1)
        if isinstance(result, EvalReport):
            if args.evals_command in {"run", "report"} and args.output is not None:
                print(f"Golden eval report written to: {args.output}")
            if args.json_output or getattr(args, "format", None) == "json":
                print(eval_report_to_json(result, pretty=True))
            else:
                print(format_eval_report(result))
            raise SystemExit(eval_report_exit_code(result))
        if isinstance(result, EvalBaseline):
            if (
                args.evals_command == "baseline"
                and getattr(args, "evals_baseline_command", None) == "create"
            ):
                print(f"Golden eval baseline written to: {args.output}")
            if args.json_output or getattr(args, "pretty", False):
                print(eval_baseline_to_json(result, pretty=True))
            else:
                print(format_eval_baseline(result))
            return
        if isinstance(result, EvalRegressionResult):
            if args.evals_command == "regression-report" and args.output is not None:
                print(f"Golden eval regression report written to: {args.output}")
            if args.json_output or getattr(args, "format", None) == "json":
                print(build_regression_report_json(result, pretty=True))
            elif getattr(args, "format", None) == "markdown":
                print(build_regression_report_markdown(result).rstrip())
            else:
                print(format_eval_regression_result(result))
            raise SystemExit(eval_regression_exit_code(result))
        if isinstance(result, EvalHistorySnapshot):
            if args.json_output or getattr(args, "pretty", False):
                print(json.dumps(to_serializable(result), indent=2, default=str))
            else:
                print(format_eval_history_snapshot(result))
            return
        if isinstance(result, EvalHistorySummary):
            if args.json_output or getattr(args, "format", None) == "json":
                print(eval_history_to_json(result.snapshots, pretty=True))
            else:
                print(format_eval_history_summary(result))
            return

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

    if args.command == "plugins":
        if isinstance(result, list):
            if args.json_output or getattr(args, "pretty", False):
                print(json.dumps(to_serializable(result), indent=2, default=str))
            elif result and isinstance(result[0], PluginHookMetadata):
                print(format_plugin_hooks(result))
            elif not result and args.plugins_command == "hooks":
                print(format_plugin_hooks(result))
            else:
                print(format_plugins(result))
            return
        if isinstance(result, PluginManifest):
            if args.json_output or getattr(args, "pretty", False):
                print(json.dumps(to_serializable(result), indent=2, default=str))
            else:
                print(format_plugin(result))
            return
        if isinstance(result, PluginRegistryManifest):
            if args.json_output or getattr(args, "pretty", False):
                print(json.dumps(to_serializable(result), indent=2, default=str))
            else:
                print(format_plugin_registry_manifest(result))
            return
        if isinstance(result, PluginHookRegistryManifest):
            if args.json_output or getattr(args, "pretty", False):
                print(json.dumps(to_serializable(result), indent=2, default=str))
            else:
                print(format_plugin_hook_manifest(result))
            return
        if isinstance(result, PluginValidationResult):
            if args.json_output or getattr(args, "pretty", False):
                print(json.dumps(to_serializable(result), indent=2, default=str))
            else:
                print(format_plugin_validation(result))
            raise SystemExit(0 if result.valid else 1)
        if isinstance(result, PluginConfig):
            if args.json_output or getattr(args, "pretty", False):
                print(json.dumps(to_serializable(result), indent=2, default=str))
            else:
                print(format_plugin_config(result))
            return
        if isinstance(result, PluginConfigValidationResult):
            if args.json_output or getattr(args, "pretty", False):
                print(json.dumps(to_serializable(result), indent=2, default=str))
            else:
                print(format_plugin_config_validation(result))
            raise SystemExit(0 if result.valid else 1)
        if isinstance(result, PluginConfigSummary):
            if args.json_output or getattr(args, "pretty", False):
                print(json.dumps(to_serializable(result), indent=2, default=str))
            else:
                print(format_plugin_config_manifest(result))
            return
        if isinstance(result, PluginExtensionPack):
            if args.json_output or getattr(args, "pretty", False):
                print(json.dumps(to_serializable(result), indent=2, default=str))
            else:
                print(format_extension_pack(result))
            return
        if isinstance(result, PluginExtensionPackValidationResult):
            if args.json_output or getattr(args, "pretty", False):
                print(json.dumps(to_serializable(result), indent=2, default=str))
            else:
                print(format_extension_pack_validation(result))
            raise SystemExit(0 if result.valid else 1)
        if isinstance(result, PluginScaffoldPlan):
            if args.json_output or getattr(args, "pretty", False):
                print(json.dumps(to_serializable(result), indent=2, default=str))
            else:
                print(format_plugin_scaffold_plan(result))
            raise SystemExit(
                0 if not any(finding.severity == "error" for finding in result.findings) else 1
            )
        if isinstance(result, PluginScaffoldResult):
            if args.json_output or getattr(args, "pretty", False):
                print(json.dumps(to_serializable(result), indent=2, default=str))
            else:
                print(format_plugin_scaffold_result(result))
            raise SystemExit(
                0 if not any(finding.severity == "error" for finding in result.findings) else 1
            )
        if isinstance(result, PluginHookResult):
            if args.json_output or getattr(args, "pretty", False):
                print(json.dumps(to_serializable(result), indent=2, default=str))
            else:
                print(format_plugin_hook_result(result))
            raise SystemExit(0 if result.success else 1)

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

    if isinstance(result, ScheduledExportValidationReport):
        if args.json_output:
            print(json.dumps(to_serializable(result), indent=2, default=str))
        else:
            print(format_scheduled_export_validation(result))
        raise SystemExit(0 if result.is_valid else 1)

    if isinstance(result, ScheduledExportManifest):
        if args.json_output:
            print(json.dumps(to_serializable(result), indent=2, default=str))
        else:
            print(format_scheduled_export_manifest(result))
        return

    if isinstance(result, Path) and args.command == "scheduled-export":
        if getattr(args, "json_output", False):
            print(json.dumps({"output_path": str(result)}, indent=2))
        else:
            print(f"Scheduled export file written to: {result}")
        return

    if isinstance(result, str) and args.command == "scheduled-export":
        print(result, end="" if result.endswith("\n") else "\n")
        return

    if isinstance(result, AsyncBatchManifest):
        if args.json_output:
            print(json.dumps(to_serializable(result), indent=2, default=str))
        else:
            print(format_async_batch_manifest(result))
        raise SystemExit(
            0 if not any(finding.severity == "error" for finding in result.findings) else 1
        )

    if isinstance(result, Path) and args.command == "async-batch":
        if getattr(args, "json_output", False):
            print(json.dumps({"output_path": str(result)}, indent=2))
        else:
            print(f"Async batch file written to: {result}")
        return

    if isinstance(result, str) and args.command == "async-batch":
        print(result, end="" if result.endswith("\n") else "\n")
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
        "export-budget-details",
        "export-budget-summary-rows",
        "export-budget-views",
        "export-calendar-items",
        "export-billing-periods",
        "export-change-events",
        "export-change-order-packages",
        "export-company-users",
        "export-commitment-change-orders",
        "export-commitment-contracts",
        "export-commitments",
        "export-correspondences",
        "export-contract-payments",
        "export-coordination-issue-activity-feed",
        "export-coordination-issue-change-history",
        "export-coordination-issue-filter-options",
        "export-coordination-issues",
        "export-cost-codes",
        "export-cost-types",
        "export-departments",
        "export-direct-costs",
        "export-distribution-groups",
        "export-form-templates",
        "export-forms",
        "export-incidents",
        "export-inspections",
        "export-locations",
        "export-meetings",
        "export-observations",
        "export-owner-invoice-line-items",
        "export-owner-invoices",
        "export-project-users",
        "export-prime-change-orders",
        "export-prime-contract-line-items",
        "export-prime-contracts",
        "export-purchase-order-contracts",
        "export-punch-items",
        "export-requisition-change-order-items",
        "export-requisition-contract-detail-items",
        "export-requisition-contract-items",
        "export-rfis",
        "export-schedule-resource-assignments",
        "export-subcontractor-invoices",
        "export-submittals",
        "export-tax-codes",
        "export-task-requested-changes",
        "export-tasks",
        "export-action-plan-change-history",
        "export-action-plans",
        "export-vendors",
        "export-work-order-contracts",
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
