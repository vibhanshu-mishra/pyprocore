# Project Status

## Current Versions

- Current stable release: `2.2.0`
- Previous stable release: `2.1.0`
- `v2.2.0` is published on PyPI and released on GitHub.
- Current unreleased branch work: Phase 8A, Phase 8C, Phase 8D, Phase 8E, Phase 8F, and Phase 8G read-only
  API coverage, plus Phase 8B client-credentials auth support for Data
  Connection Apps, Phase 9A enterprise auth hardening and permission
  diagnostics, Phase 9B scheduled export planning and deployment patterns,
  Phase 9C token-store backend and credential rotation hardening, and Phase 9D
  private deployment/runbook guidance, plus Phase 12 model-agnostic AI workflow
  examples. The package remains `2.2.0`; this branch work is unpublished.

## Current Stable Release: 2.2.0

PyProcore `2.2.0` includes the Phase 7 Agent Layer:

- Agent Tool Registry
- Local Agent API Server
- OpenAPI / JSON Schema Export
- Agent Run Logs + Replay
- Discovery-only MCP Adapter
- Agent Evaluation Harness

The `2.2.0` release has been published to PyPI, verified from a clean install,
tagged as `v2.2.0`, and released on GitHub.

## Previous Stable Release: 2.1.0

PyProcore `2.1.0` delivered expanded API coverage, AI-ready local exports,
workflow automation foundations, documentation, security hardening, release
tooling, and package metadata.

## Current Unreleased Branch Work

Phase 9A hardens the two existing auth strategies, token-store resilience,
config/doctor output, and local-only permission explanations. It does not call
Procore or external model APIs, enable agent execution, or change discovery-only
MCP behavior.

Phase 9B adds local scheduled export plan models, validation helpers, dry-run
manifests, safe sample configs, examples, scripts, and enterprise Data
Connection App deployment guidance. It does not call Procore, run exports,
create scheduled jobs, call external model APIs, enable agent execution, or
change discovery-only MCP behavior.

Phase 9C adds file and memory token-store backend architecture, safe token-store
diagnostics, credential rotation checklists, and sandbox/production separation
guidance. It does not call Procore, add cloud secret-manager integrations, call
external model APIs, enable agent execution, or change discovery-only MCP
behavior.

Phase 9D adds private deployment patterns, production runbooks, enterprise
readiness checks, safe templates, examples, and local scripts. It completes the
Phase 9 enterprise hardening work on main as unreleased branch work.

Phase 12 adds model-agnostic AI workflow examples, local prompt/checklist
helpers, vector export manifests, templates, examples, and safety checks. It
does not call Procore, call external AI/model APIs, add AI framework
dependencies, enable agent execution, or change discovery-only MCP behavior.

Phase 8A adds read-only SDK coverage for Observations, Punch Items, Generic
Tools, and Generic Tool correspondence items. It includes service helpers,
typed flexible models, search helpers, local CSV/JSONL exports, CLI commands,
agent registry metadata, docs, examples, and mocked tests. It does not add
create/update/delete actions and does not enable agent tool execution.

Phase 8B adds `PROCORE_AUTH_MODE=client_credentials` support for Procore Data
Connection Apps. Authorization-code OAuth remains the default. Client
credentials mode does not require `PROCORE_REDIRECT_URI`, and refresh tokens are
not required for stored client credentials tokens.

Phase 8C adds read-only SDK coverage for Meetings, checklist-backed
Inspections, Incidents, and project incident configuration metadata. It includes
service helpers, typed flexible models, search helpers, local CSV/JSONL exports,
CLI commands, agent registry metadata, docs, examples, and mocked tests. It does
not add create/update/delete actions and does not enable agent tool execution.

Phase 8D adds read-only SDK coverage for company/project users, Vendors,
Departments, project Distribution Groups, and project Locations. It includes
service helpers, typed flexible models, search helpers, local CSV/JSONL exports,
CLI commands, agent registry metadata, docs, examples, and mocked tests. It does
not add create/update/delete actions and does not enable agent tool execution.

Phase 8E adds read-only SDK coverage for financial and change-management
resources such as Change Events, Prime Change Orders, Commitment Change Orders,
Change Order Packages, Direct Costs, Budget Views/Details, Cost Codes, WBS
Codes, and Commitments. It does not add financial writes, approvals, status
changes, budget modifications, invoices, payment mutations, or commitment
creation.

Phase 8F adds read-only SDK coverage for contracts, invoices, payments, and
billing resources. It does not add contract, invoice, payment, approval,
submission, status-change, PDF-generation, SOV, or line-item mutation behavior.

Phase 8G adds read-only SDK coverage for project-management extras: Schedule
metadata/settings/type/integration/import status, Schedule Resource
Assignments, Tasks, Task Requested Changes, Calendar Items, Coordination
Issues, Forms, Form Templates, Action Plans, and Action Plan Change History
Events. It does not add schedule uploads/import creation, task writes,
coordination issue mutations, form submissions, action plan completions,
approvals, status changes, or project-management mutations.

## Safety Status

- Tool execution remains disabled.
- The MCP adapter remains discovery-only.
- Agent metadata, schema export, MCP discovery, replay, and eval commands do not
  call live Procore APIs.
- Agent evals are local and deterministic.
- PyProcore does not call external AI/model APIs.
- Live SDK workflows still require valid Procore credentials and permissions.
- Client credentials support does not enable Procore tool execution.
- Phase 8C, Phase 8D, Phase 8E, Phase 8F, and Phase 8G service helpers are read-only.
- Phase 9B scheduled export validation and dry-runs are local planning tools only.
- Phase 12 AI workflow examples are local-only and model-agnostic.

## Known Limitations

- PyProcore is read-oriented and does not provide broad create/update/delete
  coverage.
- Hosted webhook ingestion is not included; webhook helpers are local utilities.
- Scheduled GitHub Actions examples require a deliberate OAuth token-store
  strategy before live use.
- Enterprise scheduled exports need private token-store and output-storage
  handling before production scheduling.
- Some download helpers depend on Procore returning direct download URLs.
- Live project-level behavior can vary by company, project, OAuth app
  installation, user permissions, enabled tools, and sandbox vs production
  configuration.

## Future Roadmap

- Guarded tool execution and human approval gates
- Write-action safety model
- Real MCP execution after explicit safety design
- Additional read-only Procore coverage beyond Phase 8G
- Async client and plugin architecture
- Golden datasets and model evals
- Richer MCP integration
