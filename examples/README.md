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
export WORKFLOW_RUN_OUTPUT_DIR=exports/workflow-run
export WORKFLOW_DRY_RUN=1
export PROCORE_AUTH_MODE=authorization_code
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
`110_agent_registry_phase8g.py`.

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
- Keep secrets out of code, screenshots, logs, and issue reports.
