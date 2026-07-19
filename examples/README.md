# PyProcore Examples

These examples are small, runnable scripts that show common PyProcore tasks.
They are meant for learning, testing your setup, and copying into your own
automation projects.

## Prerequisites

Before running the examples:

1. Install PyProcore.

   ```bash
   pip3 install pyprocore
   ```

2. Configure your `.env` file with Procore OAuth and API settings.

3. Complete OAuth once so PyProcore has a usable token store.

The examples require valid Procore credentials and access to the company,
project, RFI, or submittal you are trying to read.

Examples `01` through `52` cover core SDK, workflow automation, and AI-ready
export functionality. Examples `53` through `63` cover the `v2.2.0` Phase 7
Agent Layer. Those agent examples are local metadata, schema, replay, MCP
discovery, or eval examples and do not require Procore credentials or execute
tools unless an individual example explicitly says otherwise.

Examples `64` through `69` cover unreleased Phase 8A read-only Observations,
Punch Items, Generic Tool correspondence, and agent registry metadata examples.
Examples `70` through `73` cover unreleased Phase 8B client credentials auth
patterns for Procore Data Connection Apps.
Examples `74` through `79` cover unreleased Phase 8C read-only Meetings,
Inspections, Incidents, and agent registry metadata examples.
Examples `80` through `87` cover unreleased Phase 8D read-only Directory users,
Vendors, Departments, Distribution Groups, Locations, and agent registry
metadata examples.
Examples `88` through `95` cover unreleased Phase 8E financial and
change-management read coverage.
Examples `96` through `102` cover unreleased Phase 8F contracts, invoices,
payments, and billing read coverage.
Examples `103` through `110` cover unreleased Phase 8G schedules, tasks,
calendar items, coordination issues, forms, action plans, and agent registry
metadata examples.
Examples `111` through `114` cover unreleased Phase 9A scheduled Client
Credentials patterns, enterprise diagnostics, token-store safety, and local
permission explanations. They make no live calls.
Examples `115` through `120` cover unreleased Phase 9B scheduled export plan
validation, dry-run manifests, Data Connection App deployment patterns,
multi-project planning, and private deployment reminders. They make no live
calls.
Examples `121` through `125` cover unreleased Phase 9C token-store backends,
safe diagnostics, credential rotation checklists, safe clearance, and
sandbox/production separation. They make no live calls.
Examples `126` through `130` cover unreleased Phase 9D private deployment
readiness checks, folder layouts, production runbook summaries, deployment
pattern comparisons, and enterprise safety boundaries. They make no live calls.
Examples `131` through `140` cover unreleased Phase 12 model-agnostic AI
workflow patterns, prompt packages, vector export manifests, engineering
context bundles, field issue summaries, change-risk reviews, and safety
checklists. They make no live Procore calls and no external AI/model calls.
Examples `141` through `146` cover unreleased Phase 10A async client patterns,
mock async transport, async pagination, and async safety notes. They use local
mock responses and make no live Procore calls.
Examples `147` through `152` cover unreleased Phase 10B async export and
download patterns, local manifests, and concurrency limits. They use local mock
responses, temporary folders, and make no live Procore calls.
Examples `153` through `160` cover unreleased Phase 10C async batch planning,
dry-runs, multi-project exports, partial failures, concurrency, and simple
resume patterns. They use mock clients or local dry-runs and make no live
Procore calls.
Examples `161` through `168` cover unreleased Phase 10D async field,
operations, correspondence, and directory coverage. They use local mock
responses or local dry-runs and make no live Procore calls.
Examples `169` through `176` cover unreleased Phase 10E async financial,
contract, billing, and project-management read coverage. They use local mock
responses or local dry-runs and make no live Procore calls.
Examples `177` through `184` cover unreleased Phase 11A plugin architecture
metadata, registry, validation, CLI patterns, and safety boundaries. They do
not install plugins, execute plugin code, call Procore, or call external
AI/model APIs.
Examples `185` through `192` cover unreleased Phase 11B safe local plugin
extension hooks. They use explicit in-process registration or built-in
deterministic hooks only and do not install plugins, fetch remote registries,
call Procore, call external AI/model APIs, or enable agent/MCP execution.
Examples `193` through `200` cover unreleased Phase 11C plugin configuration
and local extension-pack manifests. They read JSON metadata only and do not
install plugins, fetch remote resources, load plugin code, execute hooks, call
Procore, call external AI/model APIs, or enable agent/MCP execution.
Examples `201` through `208` cover unreleased Phase 11D plugin developer
scaffolding. They render local templates or write to temporary folders only and
do not install plugins, fetch remote resources, load generated code, execute
hooks, call Procore, call external AI/model APIs, or enable agent/MCP
execution.
Examples `209` through `218` cover unreleased Phase 13A local deterministic
golden datasets and eval reports. They validate local artifacts only and do not
call Procore, call external AI/model APIs, execute plugins, fetch remote
datasets, or enable tool/MCP execution.

Agent examples do not require Procore credentials or execute tools.

## Environment Variables

IDs and lookup values can be supplied through environment variables:

```bash
export PROCORE_COMPANY_ID=your_company_id
export PROCORE_PROJECT_ID=your_project_id
export PROCORE_PROJECT_NAME="Project name"
export PROCORE_PROJECT_NUMBER="Project number"
export PROCORE_RFI_ID=your_rfi_id
export PROCORE_RFI_NUMBER=your_rfi_number
export PROCORE_RFI_STATUS=open
export PROCORE_SEARCH_TERM="door hardware"
export PROCORE_SUBMITTAL_ID=your_submittal_id
export PROCORE_SUBMITTAL_NUMBER=your_submittal_number
export PROCORE_SUBMITTAL_STATUS=pending
export PROCORE_DOCUMENT_ID=your_document_id
export PROCORE_DOCUMENT_FOLDER_ID=your_document_folder_id
export PROCORE_DRAWING_ID=your_drawing_id
export PROCORE_DRAWING_AREA_ID=your_drawing_area_id
export PROCORE_DRAWING_DISCIPLINE_ID=your_drawing_discipline_id
export PROCORE_PHOTO_ALBUM_ID=your_photo_album_id
export PROCORE_PHOTO_ID=your_photo_id
export PROCORE_PHOTO_LIMIT=5
export PROCORE_LOG_DATE=2026-07-10
export PROCORE_DAILY_LOG_TYPE=manpower
export PROCORE_DAILY_LOG_TYPES=manpower,notes,delay
export PROCORE_OBSERVATION_ID=your_observation_id
export PROCORE_PUNCH_ITEM_ID=your_punch_item_id
export PROCORE_GENERIC_TOOL_ID=your_generic_tool_id
export PROCORE_MEETING_ID=your_meeting_id
export PROCORE_INSPECTION_ID=your_inspection_id
export PROCORE_INCIDENT_ID=your_incident_id
export PROCORE_SPECIFICATION_SET_ID=your_specification_set_id
export PROCORE_SPECIFICATION_SECTION_ID=your_specification_section_id
export PROCORE_SPECIFICATION_REVISION_ID=your_specification_revision_id
export PROCORE_OUTPUT_DIR=downloads/examples
export PROCORE_DRY_RUN=1
export PROCORE_STATUS=open
export PACKAGE_DIR=path/to/local/package
export AI_EXPORT_OUTPUT_DIR=path/to/local/package/ai-export
export AI_PROMPT_PACK_OUTPUT_DIR=path/to/local/package/ai-prompt-pack
export AI_REVIEW_TYPE=general
export AGENT_EVAL_RESULTS_PATH=example-output/agent-evals/agent-eval-results.json
export WORKFLOW_PLAN_PATH=examples/workflow_plans/project_context_and_ai_export.json
export SCHEDULED_EXPORT_PLAN=examples/configs/scheduled_export_client_credentials.json
export WORKFLOW_RUN_OUTPUT_DIR=exports/workflow-run
export WORKFLOW_DRY_RUN=1
export PROCORE_AUTH_MODE=authorization_code
export PROCORE_TOKEN_STORE_BACKEND=file
export PROCORE_TOKEN_STORE_PATH=~/.config/pyprocore/token_store.json
export PYPROCORE_PRIVATE_ROOT=/opt/pyprocore
export PYPROCORE_AI_WORKFLOW_OUTPUT=examples/generated/ai-workflow-sample
export PYPROCORE_RUN_LIVE_EXAMPLE=0
```

Use placeholder values while learning. Do not commit real IDs, tokens, secrets,
or `.env` files.

## Running Examples

From the repository root:

```bash
python3 examples/01_list_companies.py
python3 examples/02_list_projects.py
python3 examples/05_get_rfi.py
python3 examples/13_client_interface.py
python3 examples/14_export_rfis_to_csv.py
python3 examples/18_incremental_sync.py
python3 examples/20_list_documents.py
python3 examples/23_list_drawings.py
python3 examples/26_list_specification_sections.py
python3 examples/31_list_photos.py
python3 examples/35_get_daily_log_counts.py
python3 examples/40_build_project_context_package.py
python3 examples/42_build_enhanced_rfi_package.py
python3 examples/44_build_enhanced_submittal_package.py
python3 examples/46_build_ai_review_export.py
python3 examples/47_build_ai_prompt_pack.py
python3 examples/48_run_workflow_plan.py
python3 examples/49_validate_workflow_plan.py
python3 examples/62_run_agent_evals.py
python3 examples/64_list_observations.py
python3 examples/66_list_punch_items.py
python3 examples/68_list_correspondences.py
python3 examples/70_configure_client_credentials.py
python3 examples/73_auth_modes_overview.py
python3 examples/74_list_meetings.py
python3 examples/76_list_inspections.py
python3 examples/78_list_incidents.py
python3 examples/116_validate_scheduled_export_plan.py
python3 examples/117_scheduled_export_dry_run.py
python3 examples/121_token_store_backends.py
python3 examples/122_token_store_diagnostics.py
python3 examples/123_credential_rotation_checklist.py
python3 examples/131_rfi_review_assistant_package.py
python3 examples/135_vector_db_export_pattern.py
python3 examples/139_ai_workflow_safety_checklist.py
python3 examples/161_async_observations_and_punch_items.py
python3 examples/164_async_directory_resources.py
python3 examples/168_phase10d_async_coverage_summary.py
```

Documents use Procore's Project Folders and Files endpoints internally. Before a
release or sandbox rollout, inspect the live payload shape with:

```bash
PROCORE_PROJECT_ID=352338 make smoke-documents
```

Drawings support is first-class for list/get/find/download helpers. Procore
organizes drawings by drawing areas, so `PROCORE_DRAWING_AREA_ID` is useful when
you want to fetch or download one drawing directly. Before relying on downloads
in a new sandbox, inspect the live payload shape with:

```bash
PROCORE_PROJECT_ID=352338 make smoke-drawings
```

Specifications use Procore's company/project-scoped V2 endpoints. Before
building automation around a new project, inspect the live payload shape with:

```bash
PROCORE_PROJECT_ID=352338 make smoke-specifications
```

Photos use Procore's Images API. Procore calls photo albums "image categories"
and photos "images" in the REST API. Inspect live payloads with:

```bash
PROCORE_PROJECT_ID=352338 make smoke-photos
```

Daily Logs are organized by log type. You can list counts, headers, or a
specific type such as manpower, notes, or delay. Inspect live payloads with:

```bash
PROCORE_PROJECT_ID=352338 make smoke-daily-logs
```

Each script prints helpful messages when required environment variables are
missing.

Agent-layer examples do not require `.env`, OAuth tokens, company IDs, project
IDs, or live Procore access unless an example explicitly says otherwise. They do
not execute Procore tools, and the MCP adapter remains discovery-only.

## Keeping Examples Valid

Developers can check example syntax without running live Procore calls:

```bash
make examples-check
```

## Example Index

The current example set runs from `01_list_companies.py` through
`168_phase10d_async_coverage_summary.py`.

| File | Demonstrates |
| ---- | ------------ |
| `01_list_companies.py` | List companies available to the authenticated user |
| `02_list_projects.py` | List projects for `PROCORE_COMPANY_ID` |
| `03_find_project.py` | Find a project by name or number |
| `04_list_rfis.py` | List RFIs for `PROCORE_PROJECT_ID`, optionally filtered by `PROCORE_RFI_STATUS` |
| `05_get_rfi.py` | Fetch one RFI by ID |
| `06_download_rfi_attachments.py` | Download attachments from one RFI |
| `07_list_submittals.py` | List submittals for a project, optionally filtered by `PROCORE_SUBMITTAL_STATUS` |
| `08_get_submittal.py` | Fetch one submittal by ID |
| `09_download_submittal_attachments.py` | Download attachments from one submittal |
| `10_build_rfi_package.py` | Build an automation package for one RFI |
| `11_build_submittal_package.py` | Build an automation package for one submittal |
| `12_export_typed_model_json.py` | Export a typed model as JSON |
| `13_client_interface.py` | Use the object-oriented `Procore` client interface |
| `14_export_rfis_to_csv.py` | Export project RFIs to a CSV file |
| `15_export_submittals_to_csv.py` | Export project submittals to a CSV file |
| `16_sync_rfis_to_folder.py` | Sync project RFIs into local folders |
| `17_sync_submittals_to_folder.py` | Sync project submittals into local folders |
| `18_incremental_sync.py` | Run an incremental RFI sync with local state |
| `19_sync_project_to_folder.py` | Sync RFIs and submittals into one project folder |
| `20_list_documents.py` | List documents for a project or document folder |
| `21_download_document.py` | Download one document by ID |
| `22_sync_documents_to_folder.py` | Sync project documents into local folders |
| `23_list_drawings.py` | List drawings for a project, optionally filtered by drawing area or discipline |
| `24_download_drawing.py` | Download one drawing by ID and optional drawing area when Procore provides a direct URL |
| `25_list_specification_sets.py` | List specification sets for a project |
| `26_list_specification_sections.py` | List specification sections for a project, optionally filtered by set, area, or division |
| `27_get_specification_section.py` | Fetch one specification section by ID using the verified list endpoint |
| `28_list_specification_revisions.py` | List specification section revisions for a project or section |
| `29_download_specification_revision.py` | Download one specification section revision PDF |
| `30_list_photo_albums.py` | List photo albums, which Procore calls image categories |
| `31_list_photos.py` | List photos for a project or album |
| `32_get_photo.py` | Fetch one photo by ID |
| `33_download_photo.py` | Download one photo when Procore returns a full-size URL |
| `34_download_photo_album.py` | Download photos from one album with an optional limit |
| `35_get_daily_log_counts.py` | Get Daily Log counts for a project |
| `36_list_daily_log_headers.py` | List Daily Log headers for a project or date |
| `37_list_manpower_logs.py` | List manpower Daily Log entries |
| `38_list_daily_logs_by_type.py` | List Daily Log entries by type |
| `39_list_daily_logs_for_date.py` | List multiple Daily Log types for one date |
| `40_build_project_context_package.py` | Build an AI-ready project context package |
| `41_build_lightweight_project_context.py` | Build a smaller project context package with selected sections |
| `42_build_enhanced_rfi_package.py` | Build an enhanced AI-ready RFI review package with related context |
| `43_build_rfi_ai_review_context.py` | Build focused AI review files for one RFI |
| `44_build_enhanced_submittal_package.py` | Build an enhanced AI-ready submittal review package with related context |
| `45_build_submittal_ai_review_context.py` | Build focused AI review files for one submittal |
| `46_build_ai_review_export.py` | Build a local AI review export from an existing package folder |
| `47_build_ai_prompt_pack.py` | Build a local AI prompt pack from an existing package folder |
| `48_run_workflow_plan.py` | Dry-run or run a local workflow plan JSON file |
| `49_validate_workflow_plan.py` | Validate a local workflow plan without calling Procore |
| `50_validate_webhook_event.py` | Validate and normalize a local webhook JSON payload |
| `51_save_webhook_event.py` | Save a redacted webhook payload and normalized event locally |
| `52_dispatch_webhook_to_workflow_plan.py` | Dry-run a workflow plan from a local webhook event |
| `53_agent_tool_registry.py` | List local agent tool registry metadata without Procore credentials |
| `54_agent_manifest_export.py` | Export the local agent manifest JSON without calling Procore |
| `55_agent_api_server.py` | Print safe commands for starting the local agent API discovery server |
| `56_export_agent_openapi.py` | Export the local Agent API OpenAPI document without Procore credentials |
| `57_inspect_agent_schemas.py` | Inspect local agent JSON Schema metadata without calling Procore |
| `58_agent_run_logs.py` | Print safe commands for opt-in local Agent API run logging |
| `59_replay_agent_run.py` | Print safe commands for replaying local Agent API run logs |
| `60_export_agent_mcp.py` | Export discovery-only MCP metadata without Procore credentials |
| `61_mcp_discovery_only.py` | Show the disabled MCP tool-call response without executing tools |
| `62_run_agent_evals.py` | Run local deterministic agent evals without Procore or AI credentials |
| `63_inspect_agent_eval_results.py` | Inspect a saved local agent eval JSON report |
| `64_list_observations.py` | List read-only observation items for a project |
| `65_export_observations.py` | Export observation items to a local CSV file |
| `66_list_punch_items.py` | List read-only punch items for a project |
| `67_export_punch_items.py` | Export punch items to a local CSV file |
| `68_list_correspondences.py` | List Generic Tools or correspondence items for a Generic Tool |
| `69_agent_registry_phase8a.py` | Inspect Phase 8A agent metadata without executing tools |
| `70_configure_client_credentials.py` | Print a safe `.env` template for Data Connection App auth |
| `71_client_credentials_token.py` | Show the client credentials token command, with explicit opt-in for a live token request |
| `72_client_credentials_export_pattern.py` | Print a safe scheduled export pattern for client credentials setups |
| `73_auth_modes_overview.py` | Compare authorization-code and client-credentials auth modes |
| `74_list_meetings.py` | List read-only meetings for a project |
| `75_export_meetings.py` | Export meetings to a local CSV file |
| `76_list_inspections.py` | List read-only checklist-backed inspections for a project |
| `77_export_inspections.py` | Export inspections to a local CSV file |
| `78_list_incidents.py` | List read-only incidents for a project |
| `79_agent_registry_phase8c.py` | Inspect Phase 8C agent metadata without executing tools |
| `80_list_company_users.py` | List read-only company directory users |
| `81_export_company_users.py` | Export company directory users to a local CSV file |
| `82_list_project_users.py` | List read-only project directory users |
| `83_list_vendors.py` | List read-only vendors |
| `84_list_departments.py` | List read-only company departments |
| `85_list_distribution_groups.py` | List read-only project distribution groups |
| `86_list_locations.py` | List read-only project locations |
| `87_agent_registry_phase8d.py` | Inspect Phase 8D agent metadata without executing tools |
| `88_list_change_events.py` | List read-only project change events |
| `89_export_change_events.py` | Export change events to a local CSV file |
| `90_list_prime_change_orders.py` | List read-only prime change orders |
| `91_list_direct_costs.py` | List read-only direct costs |
| `92_list_budget_views.py` | List read-only budget views |
| `93_export_budget_details.py` | Export budget detail rows to a local CSV file |
| `94_list_cost_codes.py` | List read-only company cost codes |
| `95_agent_registry_phase8e.py` | Inspect Phase 8E agent metadata without executing tools |
| `96_list_prime_contracts.py` | List read-only prime contracts |
| `97_export_prime_contracts.py` | Export prime contracts to a local CSV file |
| `98_list_owner_invoices.py` | List read-only owner invoices/payment applications |
| `99_list_subcontractor_invoices.py` | List read-only subcontractor invoices/requisitions |
| `100_list_contract_payments.py` | List read-only contract payments |
| `101_list_billing_periods.py` | List read-only billing periods |
| `102_agent_registry_phase8f.py` | Inspect Phase 8F agent metadata without executing tools |
| `103_get_project_schedule.py` | Get read-only project schedule metadata |
| `104_list_tasks.py` | List read-only project tasks |
| `105_export_tasks.py` | Export project tasks to a local CSV file |
| `106_list_calendar_items.py` | List read-only project calendar items |
| `107_list_coordination_issues.py` | List read-only project coordination issues |
| `108_list_forms.py` | List read-only project forms |
| `109_list_action_plans.py` | List read-only project action plans |
| `110_agent_registry_phase8g.py` | Inspect Phase 8G agent metadata without executing tools |
| `111_client_credentials_scheduled_export_pattern.py` | Print a safe unattended Data Connection App export plan |
| `112_enterprise_auth_diagnostics.py` | Explain app connection and environment setup locally |
| `113_token_store_safety.py` | Inspect token-store metadata without printing tokens |
| `114_permission_diagnostics.py` | Interpret example 401/403 data without a network call |
| `115_scheduled_export_plan.py` | Build a local scheduled export plan object without Procore access |
| `116_validate_scheduled_export_plan.py` | Validate a scheduled export plan JSON file locally |
| `117_scheduled_export_dry_run.py` | Preview a scheduled export dry-run manifest without live calls |
| `118_data_connection_app_export_pattern.py` | Print a Data Connection App scheduled export deployment pattern |
| `119_multi_project_export_pattern.py` | Preview planned files for a placeholder multi-project export |
| `120_private_deployment_pattern.py` | Print private deployment reminders for scheduled exports |
| `121_token_store_backends.py` | Show file and memory token-store backend patterns locally |
| `122_token_store_diagnostics.py` | Inspect token-store safety without printing token values |
| `123_credential_rotation_checklist.py` | Print local-only credential rotation guidance |
| `124_safe_token_clearance.py` | Demonstrate token-store clear behavior with a temporary file |
| `125_sandbox_production_separation.py` | Explain separate sandbox and production token stores |
| `126_enterprise_readiness_check.py` | Run a local enterprise readiness check without Procore access |
| `127_private_deployment_layout.py` | Print a private deployment folder layout |
| `128_production_runbook_summary.py` | Print a production runbook summary |
| `129_deployment_pattern_comparison.py` | Compare private deployment patterns locally |
| `130_phase9_enterprise_summary.py` | Summarize Phase 9 enterprise hardening boundaries |
| `131_rfi_review_assistant_package.py` | Build a local RFI review assistant prompt package |
| `132_submittal_review_assistant_package.py` | Build a local submittal review assistant prompt package |
| `133_project_context_qa_package.py` | Prepare a project context Q&A prompt package |
| `134_drawing_spec_comparison_package.py` | Prepare a drawing/spec comparison prompt package |
| `135_vector_db_export_pattern.py` | Build a local vector export manifest without vector dependencies |
| `136_engineering_assistant_context_bundle.py` | Prepare an engineering assistant context bundle |
| `137_field_issue_summarizer_package.py` | Prepare a field issue summary prompt package |
| `138_change_risk_review_package.py` | Prepare a change-risk review prompt package |
| `139_ai_workflow_safety_checklist.py` | Print the Phase 12 AI workflow safety checklist |
| `140_phase12_ai_workflows_summary.py` | Summarize Phase 12 AI workflow patterns |
| `141_async_client_quickstart.py` | Run a local-only AsyncProcore quickstart with mock data |
| `142_async_list_projects.py` | Demonstrate async project listing with mock data |
| `143_async_rfis_and_submittals.py` | Demonstrate async RFI and submittal reads with mock data |
| `144_async_documents_drawings_specs.py` | Demonstrate async document, drawing, and specification reads |
| `145_async_pagination_pattern.py` | Demonstrate async pagination with mock responses |
| `146_async_client_safety_notes.py` | Print Phase 10A async client safety boundaries |
| `147_async_export_projects.py` | Export projects asynchronously to JSONL with mock data |
| `148_async_export_rfis.py` | Export RFIs asynchronously to CSV with mock data |
| `149_async_export_documents.py` | Export document metadata asynchronously with mock data |
| `150_async_download_manifest_pattern.py` | Demonstrate async download manifests with mock file responses |
| `151_async_concurrency_limits.py` | Show async download concurrency limits with a mock transport |
| `152_async_export_safety_notes.py` | Print Phase 10B async export and download safety notes |
| `153_async_batch_plan.py` | Build and validate a local async batch plan |
| `154_async_multi_project_rfi_export.py` | Export multi-project RFI mock data asynchronously |
| `155_async_multi_project_submittal_export.py` | Export multi-project submittal mock data asynchronously |
| `156_async_batch_dry_run.py` | Preview an async batch dry-run from a sample config |
| `157_async_batch_partial_failures.py` | Demonstrate partial failure capture with mock async data |
| `158_async_batch_concurrency.py` | Demonstrate async batch concurrency limits |
| `159_async_batch_manifest_resume_pattern.py` | Show simple manifest-based resume/skip planning |
| `160_phase10c_async_batch_summary.py` | Summarize Phase 10C async batch safety boundaries |
| `161_async_observations_and_punch_items.py` | Demonstrate async observations and punch items with mock data |
| `162_async_photos_and_daily_logs.py` | Demonstrate async photos and Daily Logs with mock data |
| `163_async_meetings_inspections_incidents.py` | Demonstrate async meetings, inspections, incidents, and incident configuration |
| `164_async_directory_resources.py` | Demonstrate async directory resources with mock data |
| `165_async_export_field_resources.py` | Export field resources asynchronously to local files with mock data |
| `166_async_batch_field_resources.py` | Build a local async batch dry-run for field resources |
| `167_async_correspondence_pattern.py` | Demonstrate the async Generic Tool correspondence pattern |
| `168_phase10d_async_coverage_summary.py` | Summarize Phase 10D async coverage safety boundaries |
| `169_async_financial_read_coverage.py` | Demonstrate async financial read coverage with mock data |
| `170_async_contract_invoice_read_coverage.py` | Demonstrate async contract and invoice reads with mock data |
| `171_async_project_management_read_coverage.py` | Demonstrate async project-management reads with mock data |
| `172_async_export_financial_resources.py` | Export mock financial resources asynchronously to a temporary file |
| `173_async_batch_financial_contract_resources.py` | Build a dry-run async batch for financial and contract resources |
| `174_async_project_management_exports.py` | Export mock project-management resources asynchronously |
| `175_async_financial_safety_boundaries.py` | Print Phase 10E financial safety boundaries |
| `176_phase10e_async_coverage_summary.py` | Summarize Phase 10E async coverage safety boundaries |
| `177_plugin_manifest_quickstart.py` | Create and validate a metadata-only plugin manifest |
| `178_plugin_registry_list_and_show.py` | List and show safe built-in plugin manifests |
| `179_plugin_validation.py` | Validate safe and unsafe plugin manifest dictionaries |
| `180_plugin_capability_discovery.py` | Find plugin manifests by capability |
| `181_plugin_cli_patterns.py` | Print safe plugin CLI command patterns |
| `182_plugin_safety_boundaries.py` | Summarize Phase 11A plugin safety boundaries |
| `183_plugin_export_manifest.py` | Export the plugin registry manifest to a temporary file |
| `184_phase11a_plugin_architecture_summary.py` | Summarize Phase 11A plugin architecture foundation |
| `185_plugin_hook_quickstart.py` | Register and run a trusted local hook callable |
| `186_validator_hook_example.py` | Run the built-in required-fields validator hook |
| `187_formatter_hook_example.py` | Run the built-in record summary formatter hook |
| `188_record_transformer_hook_example.py` | Run the built-in select-fields transformer hook |
| `189_builtin_hook_registry.py` | List built-in safe local hook metadata |
| `190_hook_manifest_export.py` | Export the hook registry manifest as JSON |
| `191_plugin_hook_safety_boundaries.py` | Summarize Phase 11B hook safety boundaries |
| `192_phase11b_plugin_hooks_summary.py` | Summarize Phase 11B safe local hook support |
| `193_plugin_config_quickstart.py` | Create and validate a safe plugin config template |
| `194_plugin_config_validation.py` | Validate a local JSON plugin config file |
| `195_plugin_config_summary.py` | Summarize config preferences against built-in metadata |
| `196_extension_pack_manifest.py` | Create a safe extension-pack manifest template |
| `197_extension_pack_validation.py` | Validate a local JSON extension-pack manifest |
| `198_plugin_config_hook_preferences.py` | Inspect hook preferences without executing hooks |
| `199_plugin_config_safety_boundaries.py` | Summarize Phase 11C config safety boundaries |
| `200_phase11c_plugin_config_summary.py` | Summarize Phase 11C plugin config support |
| `201_plugin_scaffold_quickstart.py` | Preview a safe local plugin scaffold plan |
| `202_plugin_scaffold_dry_run.py` | Run a scaffold dry-run without writing files |
| `203_plugin_scaffold_create.py` | Create a full scaffold in a temporary directory |
| `204_extension_pack_scaffold.py` | Create an extension-pack scaffold |
| `205_hook_pack_scaffold.py` | Create hook metadata scaffold files |
| `206_plugin_scaffold_overwrite_safety.py` | Demonstrate skip and overwrite behavior |
| `207_plugin_scaffold_path_safety.py` | Demonstrate path traversal rejection |
| `208_phase11d_plugin_scaffolding_summary.py` | Summarize Phase 11D scaffold safety boundaries |
| `209_golden_dataset_quickstart.py` | Create and validate a safe golden dataset locally |
| `210_eval_runner_basic.py` | Run all built-in deterministic golden eval suites |
| `211_eval_export_rows.py` | Evaluate placeholder export row shape and counts |
| `212_eval_agent_manifest.py` | Evaluate agent manifest safety metadata |
| `213_eval_ai_workflow_package.py` | Evaluate local AI workflow package metadata |
| `214_eval_async_batch_plan.py` | Evaluate a placeholder async batch plan |
| `215_eval_plugin_metadata.py` | Evaluate plugin manifest and config metadata |
| `216_eval_report_generation.py` | Write local JSON and Markdown eval reports to a temporary folder |
| `217_eval_safety_boundaries.py` | Demonstrate deterministic safety-boundary checks |
| `218_phase13a_eval_summary.py` | Summarize Phase 13A golden eval capabilities and limits |

Sample golden datasets live in `examples/golden_datasets/`:

| File | Demonstrates |
| ---- | ------------ |
| `golden_export_rows_basic.json` | Placeholder export row checks |
| `golden_agent_manifest_basic.json` | Agent manifest safety metadata checks |
| `golden_ai_workflow_package_basic.json` | Local AI workflow package checks |
| `golden_async_batch_plan_basic.json` | Async batch plan checks |
| `golden_plugin_manifest_basic.json` | Metadata-only plugin manifest checks |
| `golden_plugin_config_basic.json` | Metadata-only plugin config checks |
| `golden_safety_boundaries_basic.json` | Local deterministic safety-boundary checks |

Sample scheduled export configs live in `examples/configs/`:

| File | Demonstrates |
| ---- | ------------ |
| `scheduled_export_client_credentials.json` | Placeholder Data Connection App scheduled export plan |
| `scheduled_export_authorization_code.json` | Placeholder user-owned local scheduled export plan |
| `scheduled_export_multi_project.json` | Placeholder multi-project export planning config |
| `async_batch_multi_project.json` | Placeholder async multi-project export plan |
| `async_batch_dry_run.json` | Local-only async batch dry-run validation plan |
| `async_batch_enterprise_export.json` | Placeholder enterprise async batch export pattern |
| `plugin_config_minimal.json` | Minimal metadata-only plugin config |
| `plugin_config_hooks.json` | Hook preference metadata config |
| `plugin_config_enterprise.json` | Enterprise-style plugin metadata preferences |
| `plugin_extension_pack_sample.json` | Starter extension-pack manifest metadata |
| `plugin_extension_pack_ai_workflows.json` | AI workflow extension-pack metadata |

Sample plugin scaffolds live in `examples/plugin_scaffolds/`:

| File | Demonstrates |
| ---- | ------------ |
| `basic_plugin_manifest.json` | Placeholder metadata-only plugin manifest |
| `basic_plugin_config.json` | Placeholder plugin configuration metadata |
| `basic_extension_pack.json` | Placeholder extension-pack metadata |
| `basic_hook_manifest.json` | Placeholder hook metadata |

Sample workflow plans live in `examples/workflow_plans/`:

| File | Demonstrates |
| ---- | ------------ |
| `project_context_and_ai_export.json` | Build project context, then export it for AI review |
| `rfi_review_package.json` | Build an enhanced RFI package, then a prompt pack |
| `lightweight_sync.json` | Sync RFIs and submittals without attachment downloads |
| `nightly_project_context.json` | Nightly project context package plan |
| `weekly_ai_export.json` | Weekly AI review export from an existing local package |
| `rfi_submittal_sync.json` | Incremental RFI and submittal sync plan |
| `lightweight_daily_logs_export.json` | Daily Logs-focused project context export |

Scheduled automation templates live in `examples/scheduled/` and
`examples/github-actions/`:

| File | Demonstrates |
| ---- | ------------ |
| `run_workflow_plan.sh` | macOS/Linux shell runner for cron or Terminal |
| `run_workflow_plan.command` | macOS double-click friendly runner |
| `run_workflow_plan.ps1` | Windows PowerShell runner |
| `com.pyprocore.nightly-project-context.plist` | macOS launchd template |
| `pyprocore-scheduled-workflow.yml` | GitHub Actions scheduled workflow template |
| `pyprocore-docker-workflow.yml` | GitHub Actions Docker dry-run workflow template |

Docker examples live in `examples/docker/`:

| File | Demonstrates |
| ---- | ------------ |
| `README.md` | Docker usage notes and dry-run examples |
| `workflow-runner.docker-compose.yml` | Docker Compose workflow-plan dry-run template |
| `run-workflow-in-docker.sh` | macOS/Linux Docker workflow-plan dry-run helper |
| `run-workflow-in-docker.ps1` | Windows PowerShell Docker workflow-plan dry-run helper |

AI workflow templates live in `examples/ai_workflows/`:

| File | Demonstrates |
| ---- | ------------ |
| `rfi_review_prompt_template.md` | Placeholder RFI review assistant prompt |
| `submittal_review_prompt_template.md` | Placeholder submittal review assistant prompt |
| `project_context_qa_prompt_template.md` | Placeholder project context Q&A prompt |
| `drawing_spec_comparison_prompt_template.md` | Placeholder drawing/spec comparison prompt |
| `engineering_assistant_prompt_template.md` | Placeholder engineering assistant context prompt |
| `field_issue_summary_prompt_template.md` | Placeholder field issue summary prompt |
| `change_risk_review_prompt_template.md` | Placeholder change-risk review prompt |
| `vector_export_manifest_sample.json` | Placeholder vector export manifest |

Sample webhook payloads live in `examples/webhooks/`:

| File | Demonstrates |
| ---- | ------------ |
| `rfi_created_event.json` | Simple top-level RFI created event shape |
| `submittal_updated_event.json` | Nested `data.resource` submittal update event shape |
| `generic_project_event.json` | Generic project event shape with nested metadata |

## Safety Notes

- These scripts make live Procore API calls when you run them.
- Examples `46` and `47` are local-file-only and do not call Procore.
- Example `49` validates local files only. Example `48` defaults to dry-run.
- Examples `50`, `51`, and `52` use local webhook JSON files only. Example `52` dispatches in dry-run mode.
- Scheduled templates should be dry-run tested before use.
- Docker templates are optional and should be dry-run tested before live use.
- Unit tests do not run these scripts against Procore.
- Example `71` does not request a token unless `PYPROCORE_RUN_LIVE_EXAMPLE=1`.
- Examples `115` through `120` are local planning/deployment examples and do
  not call Procore.
- Examples `131` through `140` are local AI workflow examples. They do not call
  Procore, external AI/model APIs, vector databases, MCP execution, or Procore
  tool execution.
- Examples `141` through `146` are local async client examples. They use
  `MockAsyncTransport`, do not call Procore, do not require credentials, and do
  not add write actions.
- Examples `147` through `152` are local async export/download examples. They
  write only to temporary folders, use mock transports, do not call Procore, do
  not upload files, and do not add mutation actions.
- Examples `153` through `160` are local async batch examples. They use
  placeholder IDs, mock clients, or dry-run manifests, do not call Procore, do
  not upload files, and keep agent/MCP execution disabled.
- Examples `161` through `176` are local async expansion examples. They use
  mock transports or dry-run manifests, do not call Procore, do not modify
  financial/contract/project-management data, and keep agent/MCP execution
  disabled.
- Examples `177` through `184` are local plugin metadata examples. They do not
  install plugins, fetch remote registries, import arbitrary plugin modules,
  execute plugin code, call Procore, call external AI/model APIs, or enable
  agent/MCP execution.
- Examples `185` through `192` are local plugin hook examples. They do not
  install plugins, fetch remote registries, import arbitrary plugin modules,
  execute manifest metadata, call Procore, call external AI/model APIs, or
  enable agent/MCP execution.
- Examples `193` through `200` are local plugin config and extension-pack
  examples. They read JSON metadata only, do not install plugins, do not fetch
  remote resources, do not load arbitrary plugin code, do not execute hooks,
  do not call Procore, and keep agent/MCP execution disabled.
- Examples `201` through `208` are local plugin scaffold examples. They create
  templates only, do not install plugins, do not fetch remote resources, do not
  load generated code, do not execute hooks, do not call Procore, and keep
  agent/MCP execution disabled.
- Examples `209` through `218` are local deterministic golden eval examples.
  They do not call Procore, call external AI/model APIs, execute plugins, fetch
  remote datasets, upload reports, load arbitrary code, or enable tool/MCP
  execution.
- Keep secrets out of code, screenshots, logs, and issue reports.
