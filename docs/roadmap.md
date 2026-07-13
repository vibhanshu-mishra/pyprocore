# Roadmap

This roadmap is directional and may change based on user needs and Procore API
coverage priorities.

## Released in 2.1.0

Status: Published to PyPI and released on GitHub.

PyProcore `2.1.0` delivered the production SDK, expanded API coverage,
AI-ready local exports, automation foundation, documentation site, security
hardening, package metadata, and release-readiness tooling.

Released capabilities include:

- OAuth authorization-code flow, token refresh, retries, pagination, and structured logging
- Companies, projects, RFIs, submittals, documents, drawings, specifications, photos, and Daily Logs
- Typed models, object-oriented client helpers, and human-friendly resolvers
- Attachment and file downloads where Procore returns usable URLs
- CSV, JSONL, local sync, project context, enhanced RFI, enhanced submittal, and AI review export workflows
- Workflow plan runner, scheduled automation examples, local webhook helpers, Docker templates, and CI dry-run examples
- README, MkDocs documentation, recipes, examples, security docs, contributor docs, and release tooling

## Prepared for 2.2.0

Status: Prepared for release, not yet published.

PyProcore `2.2.0` is prepared to release the completed Phase 7 agent-layer
infrastructure:

- Phase 7A: Agent Tool Registry
- Phase 7B: Local Agent API discovery server
- Phase 7C: OpenAPI and JSON Schema exports
- Phase 7D: Agent run logs and replay
- Phase 7E: Discovery-only MCP adapter
- Phase 7F: Local deterministic agent evaluation harness

Safety guarantees for the prepared `2.2.0` release:

- Tool execution remains disabled.
- The MCP adapter is discovery-only.
- Metadata, schema, replay, and eval commands do not call live Procore APIs.
- No external AI/model APIs are called.
- Agent evals are local and deterministic.

## Future

Future work should stay safety-first and additive:

- Guarded tool execution design
- Human approval gates
- Write-action safety model
- Real MCP execution only after explicit safety design
- Golden datasets and model evals
- Private deployment patterns
- Richer MCP integration
- Possible `2.3.0` or later planning

Live Procore project-level behavior remains environment-specific and can vary
by company, project, OAuth app installation, user permissions, enabled tools,
and sandbox vs production configuration.
