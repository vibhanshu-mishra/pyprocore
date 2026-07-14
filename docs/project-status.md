# Project Status

## Current Versions

- Current stable release: `2.2.0`
- Previous stable release: `2.1.0`
- `v2.2.0` is published on PyPI and released on GitHub.
- Current unreleased branch work: Phase 8A and Phase 8C read-only API coverage,
  plus Phase 8B client-credentials auth support for Data Connection Apps.

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

## Safety Status

- Tool execution remains disabled.
- The MCP adapter remains discovery-only.
- Agent metadata, schema export, MCP discovery, replay, and eval commands do not
  call live Procore APIs.
- Agent evals are local and deterministic.
- PyProcore does not call external AI/model APIs.
- Live SDK workflows still require valid Procore credentials and permissions.
- Client credentials support does not enable Procore tool execution.
- Phase 8C service helpers are read-only.

## Known Limitations

- PyProcore is read-oriented and does not provide broad create/update/delete
  coverage.
- Hosted webhook ingestion is not included; webhook helpers are local utilities.
- Scheduled GitHub Actions examples require a deliberate OAuth token-store
  strategy before live use.
- Some download helpers depend on Procore returning direct download URLs.
- Live project-level behavior can vary by company, project, OAuth app
  installation, user permissions, enabled tools, and sandbox vs production
  configuration.

## Future Roadmap

- Guarded tool execution and human approval gates
- Write-action safety model
- Real MCP execution after explicit safety design
- Additional read-only Procore coverage beyond Phase 8C
- Async client and plugin architecture
- Vector DB examples and engineering assistant examples
- Golden datasets and model evals
- Private deployment patterns and richer MCP integration
