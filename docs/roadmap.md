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

## Future

Future work should stay safety-first and additive:

- Guarded execution and approval gates
- Expanded Procore coverage: Observations and Correspondence
- Developer platform: async client and plugin architecture
- AI workflow examples: vector DB examples and engineering assistant examples
- Evaluation: golden datasets and model evals
- Deployment: private deployment patterns and richer MCP integration

Live Procore project-level behavior remains environment-specific and can vary
by company, project, OAuth app installation, user permissions, enabled tools,
and sandbox vs production configuration.
