# Project Status

## Current Versions

- Current stable release: `2.2.0`
- Previous stable release: `2.1.0`
- `v2.2.0` is published on PyPI and released on GitHub.

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

## Safety Status

- Tool execution remains disabled.
- The MCP adapter remains discovery-only.
- Agent metadata, schema export, MCP discovery, replay, and eval commands do not
  call live Procore APIs.
- Agent evals are local and deterministic.
- PyProcore does not call external AI/model APIs.
- Live SDK workflows still require valid Procore credentials and permissions.

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
- Expanded Procore coverage for Observations and Correspondence
- Async client and plugin architecture
- Vector DB examples and engineering assistant examples
- Golden datasets and model evals
- Private deployment patterns and richer MCP integration
