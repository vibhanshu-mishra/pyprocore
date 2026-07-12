# Project Status

## Current Versions

- Published stable release: `2.1.0`
- Prepared next release: `2.2.0`
- `2.2.0` has not been published to PyPI yet.

## Released In 2.1.0

PyProcore `2.1.0` is the current stable PyPI release. It includes expanded
Procore API coverage, AI-ready local exports, workflow automation foundations,
documentation, security hardening, release tooling, and package metadata.

## Prepared For 2.2.0

PyProcore `2.2.0` is prepared to include the completed Phase 7 Agent API
infrastructure:

- Agent Tool Registry
- Local Agent API Server
- OpenAPI / JSON Schema Export
- Agent Run Logs + Replay
- Discovery-only MCP Adapter
- Agent Evaluation Harness

## Safety Status

- Tool execution remains disabled.
- The MCP adapter remains discovery-only.
- Agent metadata, schema export, MCP discovery, replay, and eval commands do not
  call live Procore APIs.
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

## Next Recommended Steps

1. Run the documentation truth audit.
2. Run release-candidate validation for `2.2.0`.
3. Publish to TestPyPI only after local checks pass.
4. Verify a clean TestPyPI install.
5. Publish to PyPI only after final manual confirmation.
6. Create the `v2.2.0` Git tag and GitHub release.
7. Perform post-release documentation cleanup.
