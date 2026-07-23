# API Coverage

PyProcore focuses on read-oriented SDK and automation workflows. The table below
summarizes current coverage without overclaiming live verification in every
Procore environment.

| Area | Status | Read/List/Get/Download Support | Notes |
| --- | --- | --- | --- |
| Companies | Supported | List | Used to discover companies available to the token. |
| Projects | Supported | List, get | Project listing is company-scoped. |
| Project Tools | Unreleased Phase 16A | List, get, find | Read-only project tool metadata. No tool execution or configuration mutation. |
| RFIs | Supported | List, get, download attachments | Attachments are read from RFI questions when Procore includes signed URLs. |
| Submittals | Supported | List, get, download attachments | Attachments are downloaded from Procore-provided URLs. |
| Documents | Supported | List folders, list files, get, download, sync | Uses Procore folder/file endpoints behind user-friendly service names. |
| Drawings | Supported | List areas, list drawings, get, find, download when URL is present | Drawings are organized by drawing areas. Download depends on Procore payload URLs. |
| Specifications | Supported | List sets, list sections, get revisions, download revisions | V2 endpoints are used where appropriate. |
| Photos | Supported | List albums, list photos, get, find, download | SDK names map to Procore image category/image API terms. |
| Daily Logs | Supported | Counts, headers, type-specific listing, date summaries | Read-only helpers for common log workflows. |
| Observations | Phase 8A | List, get, find, CSV/JSONL export | Read-only helpers use project context and typed flexible models. |
| Punch Items | Phase 8A | List, get, find, CSV/JSONL export | Read-only helpers use project context and typed flexible models. |
| Generic Tools / Correspondence | Phase 8A | List Generic Tools, list/get/find correspondence items, CSV/JSONL export | Correspondence-like items are modeled through Procore Generic Tools. |
| Meetings | Phase 8C | List, get, find, CSV/JSONL export | Read-only helpers use project context and typed flexible models. |
| Inspections | Phase 8C | List, get, find, CSV/JSONL export | Modeled through checklist-style read endpoints where Procore exposes inspection data. |
| Incidents | Phase 8C | List, get, find, incident configuration, CSV/JSONL export | Read-only helpers include project incident configuration metadata. |
| Directory Users | Phase 8D | List company/project users, get, find, CSV/JSONL export | Read-only company and project directory helpers. |
| Vendors | Phase 8D | List, get, find, CSV/JSONL export | Uses conservative company context and optional project filtering. |
| Departments | Phase 8D | List, get, find, CSV/JSONL export | Company-scoped read-only department helpers. |
| Distribution Groups | Phase 8D | List, get, find, CSV/JSONL export | Project-scoped distribution group helpers. |
| Locations | Phase 8D | List, get, find, CSV/JSONL export | Project-scoped location helpers. |
| Change Events | Phase 8E | List, get, find, statuses, types, settings, CSV/JSONL export | Read-only change-management helpers. No comments, writes, approvals, or status changes. |
| Prime Change Orders | Phase 8E | List, get, find, CSV/JSONL export | Read-only helpers only. No create/update/delete or approval behavior. |
| Commitment Change Orders | Phase 8E | List, get, CSV/JSONL export | Read-only helpers only. |
| Change Order Packages | Phase 8E | List, get, CSV/JSONL export | Read-only helpers only. |
| Direct Costs | Phase 8E | List, get, find, CSV/JSONL export | Read-only helpers only. No direct cost writes. |
| Budget Views and Details | Phase 8E | List views, columns, detail rows, summary rows, CSV/JSONL export | Read-only budget reporting helpers. No budget modification or forecast writes. |
| Cost Codes / WBS Codes | Phase 8E | List company cost codes, standard cost codes, project WBS codes, CSV/JSONL export | Read-only coding helpers. No WBS or cost code writes. |
| Commitments | Phase 8E | List, get, find, CSV/JSONL export | Read-only commitment helpers. No commitment, invoice, line-item, or compliance-document writes. |
| Prime Contracts | Phase 8F | List, get, find, line items, summary, CSV/JSONL export | Read-only contract helpers. No contract writes, SOV updates, PDF generation, approvals, or status changes. |
| Commitment / Purchase Order / Work Order Contracts | Phase 8F | List, get, find, CSV/JSONL export | Read-only contract helpers only. |
| Owner Invoices / Payment Applications | Phase 8F | List, get, find, line items, CSV/JSONL export | Read-only invoice helpers. No submission, approval, rejection, status change, or line-item mutation behavior. |
| Subcontractor Invoices / Requisitions | Phase 8F | List, get, find, requisition item lists, CSV/JSONL export | Read-only invoice helpers. No invoice submission, approval, rejection, package creation, or PDF compiler behavior. |
| Contract Payments | Phase 8F | List, get, find, CSV/JSONL export | Read-only payment helpers. No payment submission, approval, status change, or mutation behavior. |
| Billing Periods / Cost Types / Tax Codes | Phase 8F | List/get billing periods, list cost types, list tax codes, CSV/JSONL export | Read-only reference helpers only. |
| Schedule | Phase 8G | Get schedule metadata, settings, type, integration, import status; list/get resource assignments; CSV/JSONL export for assignments | Read-only helpers only. No schedule uploads or import creation. |
| Tasks | Phase 8G | List, get, find, requested changes, CSV/JSONL export | Read-only helpers only. No task or requested-change mutations. |
| Calendar Items | Phase 8G | List, get, find, CSV/JSONL export | Read-only project calendar item helpers. |
| Coordination Issues | Phase 8G | List, get, find, change history, activity feed, filter options, CSV/JSONL export | Read-only helpers only. No coordination issue mutations, associations, or status transitions. |
| Forms | Phase 8G | List, get, find, templates, CSV/JSONL export | Read-only helpers only. No form creation, edits, submissions, or response mutations. |
| Action Plans | Phase 8G | List, get, find, change history events, CSV/JSONL export | Read-only helpers only. No completion, signature, request/response, closeout, approval, or status mutation behavior. |
| Attachments/downloads | Supported | Streaming downloads, skip existing files, overwrite option | Downloads are local file operations only. |
| Workflows | Supported | CSV, JSONL, folder sync, project context, AI-ready packages | Workflows create local files and do not mutate Procore data. |
| Webhooks | Local helpers | Validate, redact, save, list, dry-run dispatch | No hosted webhook server is included. |
| Agent registry | Metadata only | Manifest, tool list, tool lookup | No tool execution, server, credentials, or live Procore calls. |
| OAS Catalog | Unreleased Phase 17A | Local endpoint summaries, safety reports, coverage reports | Metadata-only inspection of user-provided local OAS JSON files. No remote fetch, generated executable tools, Procore calls, MCP execution, or write actions. |

## Agent Tool Registry

The agent registry describes existing read-only and local-file-output PyProcore
operations for future assistant integrations. It is intentionally metadata-only:
it does not execute SDK functions, mutate Procore data, read credentials, or
start a server.

See [Agent API](agent-api.md) for the CLI and Python usage.

Phase 15A, Phase 15B, and Phase 15C MCP resources, prompts, kind filters,
capability summaries, contract validation, snapshots, compatibility reports,
and fixtures add no new Procore endpoint coverage. They are local metadata
only and do not call Procore.

## Unreleased Phase 16A Endpoint Notes

Phase 16A adds read-only SDK coverage for Project Tools metadata:

- Project Tools: `/rest/v1.0/projects/{project_id}/tools`.
- Project Tool: `/rest/v1.0/projects/{project_id}/tools/{tool_id}`.

The helpers support optional read filters such as `active`, `mobile`, and
`configurable` through the existing query-parameter pattern. They do not
execute tools, configure tools, enable/disable tools, upload data, or mutate
Procore.

Daily Logs already includes clear read-only helpers for counts, headers,
manpower, notes, daily construction report, delay, delivery, call, accident,
dumpster, visitor, productivity, and plan revision logs. Weather, equipment,
additional waste variants, transmittals, project emails, and workforce/resource
request coverage remain deferred until safe, unambiguous GET/list endpoint
shapes are documented and modeled.

## Unreleased Phase 17A OAS Catalog Notes

Phase 17A adds a local OAS-backed endpoint catalog for coverage intelligence.
Users provide a local OpenAPI/OAS JSON file; PyProcore parses endpoint metadata,
summarizes methods and resource areas, classifies likely read-only endpoints,
flags risky/write candidates, and compares areas to known PyProcore read
coverage.

This catalog layer is reporting-only. It does not download OAS files, fetch
remote registries, generate executable clients, register executable tools, call
Procore, enable MCP execution, enable Procore tool execution, or enable create,
update, delete, upload, approve, submit, payment, import, send, or other write
actions.

## Phase 8A Endpoint Notes

Phase 8A adds read-only SDK coverage for Observations, Punch Items, and Generic
Tools / correspondence-like items. The implementation follows conservative
endpoint helpers and mocked unit tests only:

- Observations: `/rest/v1.0/observations/items` with `project_id` as query context.
- Punch Items: `/rest/v1.0/punch_items` with `project_id` as query context.
- Generic Tools: `/rest/v1.0/generic_tools` with `project_id` as query context.
- Generic Tool Items: `/rest/v1.0/generic_tools/{generic_tool_id}/generic_tool_items`.

These helpers do not create, update, delete, or mutate Procore data. If a live
Procore environment returns a different payload shape or permission response,
open an issue with sanitized endpoint details and no tokens or secrets.

## Phase 8C Endpoint Notes

Phase 8C adds read-only SDK coverage for Meetings, checklist-backed
Inspections, and Incidents. The implementation follows conservative endpoint
helpers and mocked unit tests only:

- Meetings: `/rest/v1.0/meetings` with `project_id` as query context.
- Inspections: `/rest/v1.0/checklists` with `project_id` as query context.
- Incidents: `/rest/v1.0/incidents` with `project_id` as query context.
- Incident configuration: `/rest/v1.0/projects/{project_id}/incident_configuration`.

These helpers do not create, update, delete, or mutate Procore data. Inspection
terminology can vary between Procore API surfaces; PyProcore uses flexible typed
models so users can serialize the original response data while working with
common fields.

## Phase 8D Endpoint Notes

Phase 8D adds read-only SDK coverage for Directory users, Vendors, Departments,
Distribution Groups, and Locations. The implementation follows conservative
endpoint helpers and mocked unit tests only:

- Company users: `/rest/v1.0/companies/{company_id}/users`.
- Project users: `/rest/v1.0/projects/{project_id}/users`.
- Vendors: `/rest/v1.0/vendors` with company context.
- Departments: `/rest/v1.0/companies/{company_id}/departments`.
- Distribution Groups: `/rest/v1.0/projects/{project_id}/distribution_groups`.
- Locations: `/rest/v1.0/projects/{project_id}/locations`.

These helpers do not create, update, delete, or mutate Procore data. They include
flexible typed models, search helpers, CSV/JSONL exports, CLI commands, examples,
and agent registry metadata for discovery only.

## Phase 8E Endpoint Notes

Phase 8E adds read-oriented SDK coverage for financial and change-management
resources. The implementation intentionally exposes list/get/find and local
CSV/JSONL export helpers only.

These helpers do not create, update, delete, approve, change statuses, modify
budgets or forecasts, create commitments, create invoices, mutate payments, or
write compliance documents. Agent registry entries are metadata only, Procore
tool execution remains disabled, MCP remains discovery-only, and no external
AI/model APIs are called.

## Phase 8F Endpoint Notes

Phase 8F adds read-oriented SDK coverage for contracts, owner invoices/payment
applications, subcontractor invoices/requisitions, contract payments, billing
periods, cost types, and tax codes. The implementation intentionally exposes
list/get/find and local CSV/JSONL export helpers only.

These helpers do not create, update, delete, submit, approve, reject, change
statuses, generate PDFs, update SOV values, mutate line items, or submit
payments. Agent registry entries are metadata only, Procore tool execution
remains disabled, MCP remains discovery-only, and no external AI/model APIs are
called.

## Phase 8G Endpoint Notes

Phase 8G adds read-oriented SDK coverage for remaining project-management extras:
Schedule, Tasks, Calendar Items, Coordination Issues, Forms, and Action Plans.
The implementation intentionally exposes safe GET/list/find and local CSV/JSONL
export helpers only.

These helpers do not create, update, delete, upload schedules, create schedule
imports, mutate tasks, mutate requested changes, mutate coordination issues,
submit forms, complete action plans, add signatures, approve, close out, change
statuses, or perform other project-management writes. Agent registry entries are
metadata only, Procore tool execution remains disabled, MCP remains
discovery-only, and no external AI/model APIs are called.

Transmittals and Project Emails are left as future coverage until clear
read/list endpoint shapes are confirmed for this SDK.

## Phase 9B Planning Notes

Phase 9B does not add new Procore endpoint coverage. It adds local scheduled
export plan validation and dry-run manifests for enterprise Data Connection App
deployment patterns. These helpers do not construct a Procore client, do not
read tokens, do not call live Procore APIs, and do not run exports.

## Phase 9C Token-Store Notes

Phase 9C does not add new Procore endpoint coverage. It adds local token-store
backend diagnostics, file/memory token-store architecture, and credential
rotation guidance. These helpers do not construct a Procore client, do not print
token values, do not call live Procore APIs, and do not enable agent/MCP
execution.

## Phase 9D Private Deployment Notes

Phase 9D does not add new Procore endpoint coverage. It adds local private
deployment guidance, production runbooks, readiness checks, templates, examples,
and scripts. No live Procore calls, hosted infrastructure, automatic scheduling,
external AI/model calls, tool execution, or MCP execution are added.

## Phase 12 AI Workflow Notes

Phase 12 does not add new Procore endpoint coverage. It adds model-agnostic
local AI workflow examples, prompt/checklist helpers, vector export manifest
helpers, templates, and safety checks. These helpers operate on local text,
local dictionaries, or placeholder data only. They do not call Procore, call
external AI/model APIs, require AI framework dependencies, perform Procore
writes, enable agent tool execution, or enable MCP execution.

## Phase 10A Through 10E Async Coverage Notes

Phase 10A adds an async client foundation for read-oriented
workflows. Initial async coverage includes companies, projects, RFIs,
submittals, documents, drawing areas/drawings, and specification sections.

Phase 10B adds async CSV/JSONL export helpers, local download
patterns, manifests, and conservative concurrency controls for that initial
async read set. Download helpers work only when Procore payloads include direct
download URLs.

Phase 10C adds async multi-project batch helpers over the same
read-oriented async resource set. Batch exports and collection helpers support
RFIs, submittals, documents, drawings, specification sections, observations,
punch items, meetings, inspections, incidents, locations, project users, and
vendors. Local validation and dry-runs do not call Procore.

Phase 10D adds async read coverage for photo albums/photos, Daily
Logs, observations, punch items, Generic Tools/correspondence, meetings,
inspections, incidents, incident configuration, and directory resources. It also
adds local async export helpers for those resource families.

Phase 10E adds async read coverage for selected financial,
change-management, contract, billing, and project-management resources. It
includes async helpers for change events, change orders, direct costs, budget
views/details, cost codes, WBS codes, commitments, contracts, invoices,
payments, billing periods, schedule metadata, tasks, calendar items,
coordination issues, forms, form templates, and action plans.

The async layer is additive. It does not remove or rewrite the sync client, does
not add write/upload endpoints, approvals, submissions, status changes, payment
actions, budget edits, contract edits, schedule imports, form submissions, or
action-plan completions, does not enable agent or MCP execution, and uses
mocked/local tests instead of live Procore calls.

## Phase 11A Plugin Architecture Notes

Phase 11A does not add new Procore endpoint coverage. It adds a metadata-only
plugin architecture foundation for future extension packs, custom workflows,
exporters, validators, reports, integration adapters, agent metadata, and MCP
metadata. Plugin manifests are validated locally and do not install plugins,
fetch remote registries, import arbitrary modules, execute plugin code, call
Procore, call external AI/model APIs, or enable agent/MCP execution.

## Phase 11B Plugin Hook Notes

Phase 11B does not add new Procore endpoint coverage. It adds safe local
extension hook interfaces for explicitly registered trusted in-process
validators, exporters, formatters, reports, workflow helpers, and record
transformers. Hook metadata remains descriptive until application code
explicitly registers a callable. No remote plugin installs, plugin fetching,
arbitrary imports, Procore writes, live API calls, external AI/model calls,
agent execution, or MCP execution are added.

## Phase 11C Plugin Config Notes

Phase 11C does not add new Procore endpoint coverage. It adds JSON-only plugin
configuration models, local extension-pack manifests, safe validation, and
metadata filtering for registered plugin manifests and hook preferences.
Configuration files and extension-pack manifests are descriptive metadata only:
they do not install plugins, fetch remote resources, import modules, register
callables, execute hooks, call Procore, call external AI/model APIs, add write
actions, or enable agent/MCP execution.

## Phase 11D Plugin Scaffold Notes

Phase 11D does not add new Procore endpoint coverage. It adds local developer
scaffolding for plugin manifests, plugin configs, hook metadata,
extension-pack manifests, README files, docs, examples, and test templates.
Scaffolding creates static files only and does not call Procore, install
plugins, fetch remote resources, load generated code, execute hooks, add write
actions, or enable agent/MCP execution.

## Phase 13 Golden Eval Notes

Phase 13A, Phase 13B, Phase 13C, and Phase 13D do not add new Procore endpoint coverage.
They add local golden dataset schemas, deterministic scoring helpers, built-in
placeholder datasets, workflow-specific eval suites, baselines, regression
reports, history snapshots, offline model-response fixture evals, examples,
and CLI commands for checking local artifacts.

Golden evals inspect local JSON-like structures only. They do not call Procore,
call external AI/model APIs, use model-as-judge scoring, execute tools, execute
plugins, fetch remote datasets, fetch remote baselines, upload reports, add
write actions, or enable MCP execution.

## Live Verification Notes

Procore access varies by environment, company, project, app connection, and user
permissions. A command can be implemented correctly and still receive a 403 or
404 if the OAuth app is not connected to the company, the project belongs to a
different environment, a tool is disabled, or the user lacks permission.

Use the smoke helper scripts only when you intentionally want to inspect live
payload behavior in your own sandbox or production environment.

Manual smoke helpers are not part of the normal test suite. They require valid
Procore credentials, a project the OAuth user can access, and the correct
sandbox or production API base:

```bash
PROCORE_PROJECT_ID=352338 make smoke-documents
PROCORE_PROJECT_ID=352338 make smoke-drawings
PROCORE_PROJECT_ID=352338 make smoke-specifications
PROCORE_PROJECT_ID=352338 make smoke-photos
PROCORE_PROJECT_ID=352338 make smoke-daily-logs
```

If one of these returns a 403, authentication may still be valid. Confirm the
company/project pairing, app connection, user permissions, enabled Procore tool,
and sandbox vs production environment.
