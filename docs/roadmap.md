# Roadmap

This roadmap is directional and may change based on user needs, Procore API
coverage priorities, and safety review.

## Released

### v2.3.0

- Phase 8A-8G expanded read-oriented Procore API coverage for observations,
  punch items, correspondence, client credentials auth, meetings, inspections,
  incidents, directory, financial, contract, billing, schedule, task, form, and
  action-plan resources.
  Included slices: Phase 8A, Phase 8B, Phase 8C, Phase 8D, Phase 8E, Phase 8F,
  and Phase 8G.
- Phase 9A-9D enterprise authentication, token-store, scheduled export,
  private deployment, and production runbook hardening.
- Phase 10A-10E async client foundation, async exports/downloads, async batch
  helpers, and expanded async read coverage.
- Phase 11A-11D metadata-only plugin manifest support, explicit in-process
  registration for local hooks, JSON-only plugin configuration,
  config/extension-pack metadata, and safe local template scaffolding.
- Phase 12 model-agnostic local AI workflow examples for prompt packages,
  vector export, and engineering context.
- Phase 13A-13D local deterministic golden datasets, workflow evals, baselines,
  regression tracking, and offline model-response fixture evals.
- Phase 15A-15C discovery-only MCP resources, prompts, metadata, contracts,
  snapshots, reports, and static fixtures.

Safety status for `v2.3.0`:

- Procore tool execution remains disabled.
- MCP remains discovery-only.
- Plugin manifests/configs are metadata only.
- Trusted plugin hooks run only when local application code explicitly
  registers callables in-process.
- Tests, examples, evals, and MCP fixtures are local and deterministic.
- No Procore write actions are included.
- No external AI/model calls are made by the SDK.

### v2.2.0

- Phase 7 Agent Layer.
- Agent Tool Registry.
- Local Agent API Server.
- OpenAPI / JSON Schema Export.
- Agent Run Logs + Replay.
- Discovery-only MCP Adapter.
- Local deterministic Agent Evaluation Harness.

### v2.1.0

- Expanded API coverage across documents, drawings, specifications, photos, and Daily Logs.
- Workflow automation foundations.
- AI-ready local exports and project context packages.
- Enhanced RFI and submittal review packages.
- Local workflow plans, scheduled examples, webhook helpers, Docker templates, and CI examples.
- Documentation site, recipes, examples, security docs, contributor docs, and release tooling.

## Future

### Prepared For The Next Unreleased Version

- Phase 16A adds read-only Project Tools metadata helpers for listing, getting,
  and finding project tool metadata. It does not execute tools, configure
  tools, mutate Procore, enable MCP execution, or call external AI/model APIs.
- Phase 16B adds a trusted plugin ecosystem foundation with JSON-only local
  trust policies, publisher/capability/safety metadata, and local trust
  reports. It does not install plugins, fetch registries, import plugin modules,
  execute plugin code, enable MCP execution, or enable Procore tool execution.
- Phase 17A adds a local OAS-backed safe endpoint catalog for user-provided
  OpenAPI/OAS JSON files. It produces read-only coverage intelligence, safety
  classification, and JSON/Markdown reports without fetching remote catalogs,
  generating executable tools, calling Procore, enabling MCP execution, or
  enabling Procore write actions.
- Phase 17B adds a local discovery router metadata layer for searching
  PyProcore capabilities by intent and suggesting metadata-only route
  candidates. It does not execute SDK functions, call Procore, fetch remote OAS
  files, generate executable tools, call external AI/model APIs, enable MCP
  execution, or enable write actions.
- Additional Daily Log types with ambiguous or environment-specific endpoint
  shapes remain deferred until safe documented GET/list paths are confirmed.

### Additional Read Coverage

Future SDK releases may add more read-only Procore resources where endpoint
shapes are safe and clear, such as transmittals, project emails, and additional
resource families requested by users.

### Guarded Execution Foundation

Future work may design guarded tool execution, guarded read-only execution,
human approval gates,
dry-run-first workflows, execution audit logs, and a write-action safety model.
This requires explicit safety design before any execution behavior is enabled.

### MCP Execution Research

MCP remains discovery-only today. Future MCP work may explore approval-aware
execution and deployment patterns after the safety model is designed and tested.

### Plugin Ecosystem

Future plugin work may explore signed or otherwise trusted plugin loading,
remote registry review, custom workflow steps, and organization-specific
extensions. Plugin install and remote execution are not enabled today.

## Live Verification

Live Procore project-level behavior remains environment-specific and can vary by
company, project, OAuth app installation, user permissions, enabled tools, and
sandbox vs production configuration.
