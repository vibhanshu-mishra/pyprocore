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

### Phase 9 — Async Client

Planned features:

- Async Procore client
- Async pagination
- Async exports
- Async downloads
- Batch fetch helpers
- Concurrency limits
- Large-project performance improvements

### Phase 10 — Plugin Architecture

Planned features:

- Plugin registration
- Custom tool registration
- Custom exporters
- Custom package builders
- Custom workflow steps
- Third-party integration hooks
- Organization-specific extensions

### Phase 11 — AI Workflow Examples

Planned examples:

- RFI review assistant
- Submittal review assistant
- Drawing/specification comparison assistant
- Project context search assistant
- Vector DB examples
- Engineering assistant examples
- Document Q&A package
- Field issue summarizer

PyProcore will remain model-agnostic.

### Phase 12 — Golden Datasets and Agent Evals

Planned features:

- Golden datasets
- Expected-output fixtures
- Agent evaluation scenarios
- Model comparison examples
- Tool-selection accuracy checks
- Safety evals
- Regression tests

### Phase 13 — Private Deployment Patterns

Planned features:

- Local-only deployment guide
- Private server deployment guide
- Docker Compose examples
- Internal network deployment
- Token-store strategy
- Secrets management guide
- Audit-log storage guide

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
