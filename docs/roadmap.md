# Roadmap

This roadmap is directional and may change based on user needs, Procore API
coverage priorities, and safety review.

## Released

### v2.2.0

- Phase 7 Agent Layer
- Agent Tool Registry
- Local Agent API Server
- OpenAPI / JSON Schema Export
- Agent Run Logs + Replay
- Discovery-only MCP Adapter
- Local deterministic Agent Evaluation Harness

Safety status for `v2.2.0`:

- Tool execution remains disabled.
- The MCP adapter is discovery-only.
- Metadata, schema, replay, MCP, and eval commands do not call live Procore APIs.
- No external AI/model APIs are called by the Phase 7 layer.

### v2.1.0

- Expanded API coverage across documents, drawings, specifications, photos, and Daily Logs
- Workflow automation foundations
- AI-ready local exports and project context packages
- Enhanced RFI and submittal review packages
- Local workflow plans, scheduled examples, webhook helpers, Docker templates, and CI examples
- Documentation site, recipes, examples, security docs, contributor docs, and release tooling

## Unreleased Branch Work

### Phase 15A — Richer MCP Discovery, Resources, And Prompt Templates

Implemented in the current branch and not yet published:

- Typed MCP resource, prompt, server, capability, tool-summary, and safety models
- Local MCP resource discovery for agent, eval, plugin, async, AI workflow,
  safety, and docs metadata
- Local MCP prompt templates for construction review and planning workflows
- Top-level `procore-sdk mcp` discovery commands
- Stdio-friendly discovery payloads
- Placeholder-only examples 249–258

Focus: discovery metadata only. No MCP execution, Procore tool execution,
plugin execution, live Procore calls, external AI/model calls, remote resource
fetching, uploads, or write actions are enabled.

### Phase 9A — Enterprise Authentication Hardening

- Backward-compatible Authorization Code and Client Credentials strategy handling
- Safe config, token-store, renewal, 401/403, permission, app-connection, and environment diagnostics
- No Procore/model calls or agent/MCP execution

### Phase 9B — Scheduled Export and Data Connection App Deployment Patterns

Implemented in the current branch and not yet published:

- Local scheduled export plan model
- Local plan validation for auth mode, company/project scope, resources, output format, output path, and broad-export warnings
- Dry-run manifests that describe planned files without calling Procore
- Safe sample configs with placeholder IDs only
- CLI commands for `scheduled-export sample-config`, `scheduled-export validate`, and `scheduled-export dry-run`
- Enterprise deployment guidance for `.env`, token stores, sandbox/production separation, credential rotation, private outputs, and permission review

Focus: local planning only. No scheduled jobs are installed, no exports are
run, no live Procore calls are made, no external AI/model APIs are called, and
agent/MCP execution remains disabled.

### Phase 9C — Token Store Backends and Credential Rotation Guidance

Implemented in the current branch and not yet published:

- Token-store backend interface with file and memory backends
- Safer file token-store writes, clears, diagnostics, and permission warnings
- CLI commands for token-store status, inspect, clear, and sample paths
- Credential rotation checklist helpers for Authorization Code and Client Credentials
- Public docs and examples for sandbox/production separation and private token stores

Focus: local token-store safety and enterprise readiness only. No cloud
secret-manager integrations are implemented, no live Procore calls are made, no
external AI/model APIs are called, and agent/MCP execution remains disabled.

### Phase 9D — Private Deployment Patterns and Production Runbooks

Implemented in the current branch and not yet published:

- Private deployment guide for local-only, private-server, cron, and Docker runner patterns
- Production runbook for setup, dry-runs, first production runs, monitoring, 401/403 troubleshooting, rotation, incident response, rollback, upgrades, and decommissioning
- Enterprise readiness checklist models and local CLI helpers
- Placeholder-only deployment templates and examples 126–130
- Safe local scripts for readiness checks, folder layout planning, and runbook summaries

Focus: private deployment guidance only. PyProcore does not host
infrastructure, does not install schedules, does not call live Procore APIs or
external AI/model APIs, and agent/MCP execution remains disabled.

### Phase 12 — AI Workflow Examples

Implemented in the current branch and not yet published:

- Model-agnostic local AI workflow guide
- Prompt/checklist helpers for RFI review, submittal review, project Q&A,
  drawing/spec comparison, engineering context, field issue summaries, and
  change-risk review
- Local vector export manifest and text chunking helpers without vector
  database dependencies
- Placeholder-only examples 131–140
- Placeholder-only AI workflow templates
- Local safety check scripts

Focus: examples and local package preparation only. PyProcore does not call
external AI/model APIs, does not add required AI framework dependencies, does
not call live Procore APIs, does not perform Procore writes, and agent/MCP
execution remains disabled.

### Phase 10A — Async Client Foundation

Implemented in the current branch and not yet published:

- `AsyncProcore` read-oriented client
- Async transport abstraction with local `MockAsyncTransport`
- Optional real async HTTP transport through `pyprocore[async]`
- Async request parsing, retry, 401 refresh, error mapping, and pagination
- Initial async coverage for companies, projects, RFIs, submittals, documents,
  drawings, and specification sections
- Placeholder-only examples 141–146

Focus: async read foundation only. The sync client remains supported, no
Procore write actions are added, no live Procore calls are made by tests or
examples, no external AI/model APIs are called, and agent/MCP execution remains
disabled.

### Phase 10B — Async Exports And File Download Patterns

Implemented in the current branch and not yet published:

- Async CSV and JSONL export helpers for the initial async resource set
- Local async download helpers for records with direct download URLs
- `AsyncExportResult`, `AsyncExportManifest`, `AsyncDownloadResult`, and
  `AsyncDownloadManifest`
- Conservative semaphore-based `max_concurrency` controls
- Partial-failure capture with continue-on-error behavior
- Placeholder-only examples 147–152

Focus: read-only local export and download patterns. The sync client and sync
exports remain supported, no uploads or Procore mutations are added, no live
Procore calls are made by tests or examples, no external AI/model APIs are
called, and agent/MCP execution remains disabled.

### Phase 10C — Async Multi-Project Operations And Batch Helpers

Implemented in the current branch and not yet published:

- `AsyncBatchPlan`, `AsyncBatchManifest`, per-project results, per-resource results, and findings
- Local async batch validation and dry-run manifests
- Async multi-project CSV/JSONL exports for RFIs, submittals, documents, drawings, and specification sections
- In-memory async collection helpers for the same resource set
- Conservative `max_concurrency` controls
- Partial-failure capture with continue-on-error or fail-fast behavior
- Simple manifest resume/skip pattern for completed project/resource pairs
- Local-only CLI commands for `async-batch sample-config`, `async-batch validate`, and `async-batch dry-run`
- Placeholder-only examples 153–160 and safe sample configs

Focus: read-only async batch operations. The sync client and existing async
10A/10B APIs remain supported, no upload or Procore mutation actions are added,
no live Procore calls are made by tests or examples, no external AI/model APIs
are called, and agent/MCP execution remains disabled.

### Phase 10D — Async Field, Operations, And Directory Coverage

Implemented in the current branch and not yet published:

- Async read coverage for photo albums, photos, and Daily Logs
- Async read and find helpers for observations and punch items
- Async read and find helpers for Generic Tool correspondence
- Async read and find helpers for meetings, inspections, and incidents
- Async incident configuration read helper
- Async directory helpers for company users, project users, vendors,
  departments, distribution groups, and locations
- Local async CSV/JSONL export helpers for the new resource families
- Async batch support for observations, punch items, meetings, inspections,
  incidents, locations, project users, and vendors
- Placeholder/mock examples 161–168

Focus: read-only async coverage expansion. The sync client and existing async
APIs remain supported, no Procore mutations are added, no live Procore calls are
made by tests or examples, no external AI/model APIs are called, and agent/MCP
execution remains disabled.

### Phase 10E — Async Financial, Contract, And Project Management Coverage

Implemented in the current branch and not yet published:

- Async read and find helpers for selected financial and change-management resources
- Async read helpers for contracts, owner invoices, subcontractor invoices,
  contract payments, billing periods, cost types, and tax codes
- Async read helpers for schedule metadata, tasks, calendar items,
  coordination issues, forms, form templates, and action plans
- Local async CSV/JSONL export helpers for selected Phase 10E resource families
- Async batch support for selected financial, contract, billing, and
  project-management resources
- Placeholder/mock examples 169–176

Focus: read-only async coverage expansion for business-sensitive resource
families. No approvals, submissions, status changes, payment actions, budget
edits, contract edits, schedule imports, form submissions, action-plan
completions, Procore mutations, external AI/model calls, agent execution, or
MCP execution are added.

### Phase 11A — Plugin Architecture Foundation

Implemented in the current branch and not yet published:

- Metadata-only plugin manifest models
- Safe local plugin registry
- Local manifest validation
- Built-in example manifests for future exporter, workflow, validator, report,
  agent metadata, and MCP metadata extension categories
- CLI commands for `plugins list`, `plugins show`, `plugins manifest`,
  `plugins sample-manifest`, and `plugins validate`
- Placeholder/local examples 177–184

Focus: plugin architecture foundation only. No plugin installation, remote
registry fetching, arbitrary plugin imports, plugin code execution, Procore
mutations, live Procore calls, external AI/model calls, agent execution, or MCP
execution are added.

### Phase 11B — Safe Local Plugin Extension Hooks

Implemented in the current branch and not yet published:

- Typed hook metadata, contexts, results, and registry manifests
- Explicit in-process registration for trusted local hook callables
- Built-in deterministic local hooks for validators, formatters, transformers,
  JSONL payloads, and quality reports
- CLI commands for `plugins hooks`, `plugins hook-manifest`,
  `plugins sample-hook-manifest`, and built-in sample hook demos
- Placeholder/local examples 185–192

Focus: safe local extension hooks only. No plugin installation, remote registry
fetching, arbitrary plugin imports, manifest-driven execution, Procore
mutations, live Procore calls, external AI/model calls, agent execution, or MCP
execution are added.

### Phase 11C — Plugin Configuration and Local Extension Packs

Implemented in the current branch and not yet published:

- JSON-only plugin configuration models
- Hook preference and capability preference metadata
- Local extension-pack manifest models
- Safe config and extension-pack validation helpers
- Metadata filtering for registered plugin manifests
- CLI commands for `plugins config sample`, `plugins config validate`,
  `plugins config summary`, `plugins config manifest`,
  `plugins extension-pack sample`, `plugins extension-pack validate`, and
  `plugins extension-pack summary`
- Placeholder/local examples 193–200 and sample JSON config files

Focus: plugin configuration metadata only. No plugin installation, remote
registry fetching, arbitrary plugin imports, config-driven execution,
extension-pack execution, Procore mutations, live Procore calls, external
AI/model calls, agent execution, or MCP execution are added.

### Phase 11D — Plugin Developer Templates and Pack Scaffolding

Implemented in the current branch and not yet published:

- Local scaffold request, plan, file, finding, and result models
- Static template rendering for plugin manifests, plugin configs, hook
  manifests, extension-pack manifests, README files, docs, examples, and tests
- Dry-run planning that writes no files
- Create mode that writes only under the selected output directory
- Path traversal and remote-looking path rejection
- Existing-file skip behavior by default, with explicit overwrite support
- CLI commands for `plugins scaffold sample-plan`, `plugins scaffold dry-run`,
  `plugins scaffold create`, `plugins scaffold extension-pack`,
  `plugins scaffold config`, and `plugins scaffold hook-pack`
- Placeholder/local examples 201–208 and sample scaffold metadata files

Focus: safe local template scaffolding only. No plugin installation, remote
fetching, arbitrary plugin loading, dynamic imports, config-driven execution,
extension-pack execution, generated-code execution, Procore mutations, live
Procore calls, external AI/model calls, agent execution, or MCP execution are
added.

### Phase 13A — Golden Dataset Foundation and Deterministic Eval Harness

Implemented in the current branch and not yet published:

- Typed local golden dataset models for deterministic eval cases.
- Deterministic scoring helpers for exact matches, required/forbidden keys,
  text checks, JSON serializability, redaction, row counts, manifest integrity,
  and safety boundaries.
- Built-in placeholder datasets for export rows, agent manifests, AI workflow
  packages, async batch plans, plugin manifests, plugin configs, and safety
  boundaries.
- Local eval runner, JSON/Markdown report builders, CLI commands, docs, and
  examples 209–218.

Focus: local artifact checks only. No live Procore calls, external AI/model
calls, plugin execution, MCP execution, remote dataset fetching, dataset
upload, arbitrary code loading, Procore tool execution, or Procore writes are
added.

### Phase 13B — Workflow-Specific Golden Eval Suites

Implemented in the current branch and not yet published:

- RFI workflow evals for export rows, package context, and grounded prompt
  packages.
- Submittal workflow evals for export rows, review package context, and
  human-review prompt boundaries.
- Async export and async batch evals for row shape, manifest integrity,
  dry-run flags, partial failures, and output path boundaries.
- AI workflow package evals for local prompt packages, context manifests,
  safety checklists, and vector-export metadata.
- Plugin metadata/config evals for metadata-only manifests, allowed
  capabilities, hook metadata, config preferences, and extension packs.
- Safety-boundary evals for disabled tool/MCP/plugin/model/remote dataset
  execution.
- Examples 219–228 and sample workflow golden dataset files.

Focus: deterministic local workflow fixtures only. No live Procore calls,
external AI/model calls, plugin execution, MCP execution, remote dataset
fetching, dataset upload, arbitrary code loading, Procore tool execution, or
Procore writes are added.

### Phase 13C — Eval Reports, Baselines, And Regression Tracking

Implemented in the current branch and not yet published:

- Local JSON eval baseline models and helpers.
- Deterministic comparison of current eval reports to baseline files.
- Regression findings for missing suites/cases, pass-to-fail changes, warnings,
  score drops, max score changes, and new suites/cases.
- Default and strict local threshold policies.
- JSON and Markdown regression report builders.
- Optional append-only local history snapshots and summaries.
- CLI commands for `evals baseline`, `evals compare`,
  `evals regression-report`, and `evals history`.
- Examples 229–238 and sample local baseline/report/history files.

Focus: deterministic local baseline comparison only. No live Procore calls,
external AI/model calls, plugin execution, MCP execution, remote dataset or
baseline fetching, remote report upload, arbitrary code loading, Procore tool
execution, or Procore writes are added.

### Phase 13D — Offline Model Response Fixture Evals

Implemented in the current branch and not yet published:

- Typed offline model-response fixture models and validation helpers.
- Deterministic scoring for required sections, citations/source labels,
  grounding statements, hallucination risk, prohibited approval/write-action
  language, fake confidence, limitations, secret-like text, and live/model-call
  claims.
- Built-in fixture suites for RFI review, submittal review, project context
  Q&A, drawing/spec comparison, engineering assistant, field issue summary,
  change-risk review, and safety boundaries.
- Local JSON fixture files under `examples/model_response_fixtures/`.
- CLI commands for `evals model-fixture sample`, `validate`, `score`, and
  `policy`.
- Examples 239–248.

Focus: saved local model-response fixtures only. No live Procore calls,
external AI/model calls, model-as-judge scoring, plugin execution, MCP
execution, remote fixture fetching, remote report upload, arbitrary code
loading, Procore tool execution, or Procore writes are added.

### Phase 8A — Expanded Procore API Coverage

Implemented in the current branch and not yet published:

- Observation item read helpers
- Punch item read helpers
- Generic Tool metadata helpers
- Generic Tool correspondence item read helpers
- Search/resolver helpers for observations, punch items, and correspondence
- CSV/JSONL local exports
- CLI commands
- Agent registry metadata for discovery only
- Examples and docs

Focus: read-oriented coverage only. No create/update/delete/write actions are
included.

### Phase 8B — Client Credentials Auth

Implemented in the current branch and not yet published:

- `PROCORE_AUTH_MODE=authorization_code|client_credentials`
- Authorization-code OAuth remains the default.
- Data Connection App / client credentials token requests
- Client credentials token storage without requiring refresh tokens
- Doctor/auth-status diagnostics that understand auth mode
- CLI helper: `procore-sdk auth client-credentials-token`
- Beginner-friendly examples and docs

Focus: authentication support only. This does not enable Procore tool execution
or add write APIs.

### Phase 8C — Expanded Procore API Coverage

Implemented in the current branch and not yet published:

- Meetings
- Inspections
- Incidents

Focus: read-oriented coverage only. No create/update/delete/write actions are
included.

### Phase 8D — Expanded Procore API Coverage

Implemented in the current branch and not yet published:

- Company directory users
- Project directory users
- Vendors
- Departments
- Project distribution groups
- Project locations
- Search/resolver helpers
- CSV/JSONL local exports
- CLI commands
- Agent registry metadata for discovery only
- Examples and docs

Focus: read-oriented coverage only. No create/update/delete/write actions are
included.

### Phase 8E — Financial and Change Management Read Coverage

Implemented in the current branch and not yet published:

- Change Events
- Prime Change Orders
- Commitment Change Orders
- Change Order Packages
- Direct Costs
- Budget Views, Detail Columns, Details, and Summary Rows
- Cost Codes and WBS Codes
- Commitments
- CSV/JSONL local exports
- CLI commands
- Agent registry metadata for discovery only
- Examples and docs

Focus: read-oriented coverage only. No financial writes, approvals, status
changes, budget modifications, invoices, payment mutations, or commitment
creation are included.

### Phase 8F — Contracts, Invoices, Payments Read Coverage

Implemented in the current branch and not yet published:

- Prime Contracts, line items, and summaries
- Commitment Contracts, Purchase Order Contracts, and Work Order Contracts
- Owner Invoices / Payment Applications and line items
- Subcontractor Invoices / Requisitions and read-only requisition item lists
- Contract Payments
- Billing Periods, Cost Types, and Tax Codes
- CSV/JSONL local exports
- CLI commands
- Agent registry metadata for discovery only
- Examples and docs

Focus: read-oriented coverage only. No contract, invoice, payment, approval,
submission, status-change, PDF-generation, SOV, or line-item mutation behavior
is included.

### Phase 8G — Project Management Extras Read Coverage

Implemented in the current branch and not yet published:

- Schedule metadata, settings, type, integration, import status, and resource assignments
- Tasks and task requested changes
- Calendar items
- Coordination issues, change history, activity feed, and filter options
- Forms and form templates
- Action plans and change history events
- CSV/JSONL local exports
- CLI commands
- Agent registry metadata for discovery only
- Examples and docs

Focus: read-oriented coverage only. No schedule uploads/import creation, task
writes, requested-change mutations, coordination issue mutations, form
submissions, action plan completions, approvals, status changes, or
project-management mutations are included.

## Future

### Future Read Coverage

Planned modules when endpoint shapes are safe and clear:

- Transmittals
- Project Emails
- Additional read-only Procore resources

### Future Async Work

Planned features:

- Async attachment extraction helpers across more Procore payload shapes
- Large-project performance improvements

### Future Trusted Plugin Loading

Planned features:

- Signed or otherwise trusted plugin loading research
- Custom tool metadata registration
- Remote registry evaluation with strict review gates
- Custom package builders
- Custom workflow steps
- Third-party integration hooks
- Organization-specific extensions

### Phase 13 — Golden Datasets and Agent Evals

Planned features:

- Golden datasets
- Expected-output fixtures
- Agent evaluation scenarios
- Model comparison examples
- Tool-selection accuracy checks
- Safety evals
- Regression tests

### Phase 14 — Guarded Execution Foundation

Planned features:

- Guarded tool execution design
- Human approval gates
- Write-action safety model
- Read-only execution allowlist
- Risk levels
- Dry-run-first execution
- Execution audit logs

This phase should happen only after the SDK has broader read coverage and stronger evaluation infrastructure.

### Phase 15 — Richer MCP Integration

Planned features:

- Deeper MCP integration
- Real MCP execution only after explicit safety design
- Approval-aware MCP tool calls
- Execution logs
- Deployment guidance

Live Procore project-level behavior remains environment-specific and can vary
by company, project, OAuth app installation, user permissions, enabled tools,
and sandbox vs production configuration.
