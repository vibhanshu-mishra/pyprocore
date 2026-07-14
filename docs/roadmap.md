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

## Future

### Phase 8B+ — Expanded Procore API Coverage

Planned modules:

- Meetings
- Inspections
- Incidents
- Directory
- Locations
- Commitments
- Change Events
- Change Orders
- Budget/financial read coverage where appropriate

Focus: read-oriented coverage first.

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
