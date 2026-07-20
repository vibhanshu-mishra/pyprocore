# Project Status

## Current Versions

- Current stable release: `2.3.0`
- Previous stable release: `2.2.0`
- `v2.3.0` is published on PyPI and released on GitHub.
- `2.3.0` includes the additive work completed after `2.2.0`: Phase 8 expanded
  read coverage, Phase 9 enterprise hardening, Phase 10 async support, Phase 11
  plugin metadata/hooks/scaffolding, Phase 12 AI workflow examples, Phase 13
  deterministic evals, and Phase 15 discovery-only MCP compatibility tooling.

## Current Stable Release: 2.3.0

PyProcore `2.3.0` includes the Phase 7 Agent Layer plus substantial additive
SDK, automation, async, plugin, eval, and MCP discovery improvements:

- Agent Tool Registry
- Local Agent API Server
- OpenAPI / JSON Schema Export
- Agent Run Logs + Replay
- Discovery-only MCP Adapter
- Agent Evaluation Harness
- Expanded read-oriented API coverage across field, financial, contract,
  billing, schedule, task, form, action-plan, directory, and related resources
- Enterprise auth, token-store, scheduled export, private deployment, and
  production runbook hardening
- Async client, async export/download helpers, and async batch planning
- Metadata-only plugin manifests, explicit local hooks, JSON config,
  extension-pack metadata, and local scaffolding
- Model-agnostic AI workflow examples and deterministic eval tooling
- Discovery-only MCP resources, prompts, contracts, snapshots, reports, and
  fixtures

The `2.3.0` release has been published to PyPI, verified from a clean install,
tagged as `v2.3.0`, and released on GitHub.

## What Changed Since 2.2.0

Upgrade to `2.3.0` if you want broader read coverage, safer enterprise
deployment patterns, async read/export helpers, metadata-only plugin extension
points, local AI workflow examples, deterministic eval infrastructure, or
discovery-only MCP compatibility artifacts.

CLI smoke commands:

```bash
procore-sdk --version
procore-sdk doctor
procore-sdk agent tools
procore-sdk evals run
procore-sdk mcp validate
```

Local validation commands:

```bash
python3 scripts/audit_docs_truth.py
python3 scripts/check_release_ready.py
python3 scripts/check_secrets.py
make examples-check
make test
make coverage
make lint
make typecheck
make docs-build
```

## Previous Stable Release: 2.2.0

PyProcore `2.2.0` delivered the completed Phase 7 Agent Layer: local
discovery/spec/eval/replay infrastructure for future assistant integrations.

## Earlier Stable Release: 2.1.0

PyProcore `2.1.0` delivered expanded API coverage, AI-ready local exports,
workflow automation foundations, documentation, security hardening, release
tooling, and package metadata.

## Current Released in 2.3.0

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
Phase 9 enterprise hardening work included in `v2.3.0`.

Phase 12 adds model-agnostic AI workflow examples, local prompt/checklist
helpers, vector export manifests, templates, examples, and safety checks. It
does not call Procore, call external AI/model APIs, add AI framework
dependencies, enable agent execution, or change discovery-only MCP behavior.

Phase 10A adds an async client foundation for read-oriented workflows. It adds
`AsyncProcore`, async transport abstractions, mock async tests/examples,
optional `pyprocore[async]` HTTP support, async pagination/retry/error handling,
and initial async coverage for companies, projects, RFIs, submittals, documents,
drawings, and specification sections. It does not add Procore write actions.

Phase 10B adds async CSV/JSONL export helpers, local download patterns,
manifest/result models, and conservative concurrency controls for read-only
workflows. It does not replace sync exports, upload files, mutate Procore data,
call external AI/model APIs, enable agent execution, or change discovery-only
MCP behavior.

Phase 10C adds async multi-project batch plans, validation, dry-run manifests,
read-only CSV/JSONL exports, in-memory collection helpers, conservative
concurrency controls, partial-failure capture, and simple manifest resume/skip
behavior. CLI planning commands are local-only and do not call Procore.

Phase 10D expands async read coverage for photo albums/photos, Daily Logs,
observations, punch items, Generic Tools/correspondence, meetings, inspections,
incidents, incident configuration, and directory resources. It also adds local
async export helpers and extends async batch support for selected field,
operations, and directory resources.

Phase 10E expands async read coverage for selected financial,
change-management, contract, billing, schedule, task, calendar, coordination
issue, form, and action-plan resources. It also adds local async export helpers
and selected async batch resources. It does not add approvals, submissions,
status changes, payment actions, budget edits, contract edits, schedule imports,
form submissions, action-plan completions, agent execution, or MCP execution.

Phase 11A adds a metadata-only plugin architecture foundation for future
extension packs, custom workflows, exporters, validators, reports, integration
adapters, agent metadata, and MCP metadata. It does not install plugins, fetch
remote registries, import arbitrary plugin modules, execute plugin code, call
Procore, call external AI/model APIs, enable agent execution, or change
discovery-only MCP behavior.

Phase 11B adds safe local plugin extension hooks for trusted callables that are
explicitly registered in-process. It adds built-in deterministic validators,
formatters, transformers, exporters, and reports for local data only. Manifest
hook metadata does not execute code, and no remote loading, plugin installation,
Procore writes, live API calls, external AI/model calls, agent execution, or MCP
execution are added.

Phase 11C adds JSON-only plugin configuration and local extension-pack manifest
support. Config files can describe enabled plugin metadata, capability
preferences, hook preferences, and extension-pack metadata. They do not install
plugins, fetch remote resources, import modules, register callables, execute
hooks, call Procore, call external AI/model APIs, add write actions, or enable
agent/MCP execution.

Phase 11D adds safe local plugin developer scaffolding for manifests, configs,
hook metadata, extension-pack manifests, README files, docs, examples, and test
templates. Generated files are templates only. Scaffolding does not install
plugins, fetch remote resources, auto-load modules, execute generated files,
execute hooks, call Procore, call external AI/model APIs, add write actions, or
enable agent/MCP execution.

Phase 13A adds local golden dataset models, deterministic scoring helpers,
built-in placeholder datasets, eval runners, JSON/Markdown reports, CLI
commands, docs, and examples for local artifacts. It evaluates saved/local
structures only and does not call Procore, call external AI/model APIs, execute
plugins, fetch remote datasets, upload reports, or enable tool/MCP execution.

Phase 13B adds workflow-specific golden eval suites for RFIs, submittals, async
exports, async batch manifests, AI workflow packages, plugin metadata/configs,
and safety boundaries. It remains local and deterministic, uses placeholder
fixtures only, and does not call Procore, call external AI/model APIs, execute
plugins, fetch remote datasets, load arbitrary code, upload reports, or enable
tool/MCP execution.

Phase 13C adds local eval baseline files, deterministic regression comparison,
score threshold policies, JSON/Markdown regression reports, and optional local
history snapshots. It compares local eval results only and does not call
Procore, call external AI/model APIs, execute plugins, fetch remote datasets,
upload remote reports, load arbitrary code, or enable tool/MCP execution.

Phase 13D adds offline model-response fixture evals for saved/sample AI-style
responses. It checks grounding, citations, hallucination risk, prohibited
action language, limitation disclosure, secret-like text, and live/model-call
claims. It does not call Procore, call model providers, use model-as-judge
scoring, execute plugins, fetch remote fixtures, upload reports, load arbitrary
code, or enable tool/MCP execution.

Phase 15A adds richer MCP discovery resources, prompt templates, capability
summaries, and stdio-friendly discovery payloads. It does not enable MCP
execution, Procore tool execution, plugin execution, live Procore calls,
external model calls, remote resource fetching, uploads, or write actions.

Phase 15B deepens that discovery-only MCP surface with eval baseline,
regression, history, and model-fixture resources; plugin extension-pack and
scaffold metadata; async resource/export/batch/download metadata; AI workflow
review metadata; additional artifact review prompts; kind filters; and richer
stdio discovery summaries. It does not enable MCP execution, Procore tool
execution, plugin execution, live Procore calls, external model calls, remote
resource fetching, remote report uploads, or write actions.

Phase 15C adds discovery-only MCP contract validation, local discovery
snapshots, JSON/Markdown compatibility reports, static client fixtures, and
safe CLI commands for disabled and unknown-response shapes. It does not enable
MCP execution, Procore tool execution, plugin execution, live Procore calls,
external model calls, remote resource fetching, remote report uploads, or write
actions.

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
- Phase 10A async client support is read-oriented and additive.
- Phase 10B async export/download helpers are read-only, local-file-only, and additive.
- Phase 10C async batch helpers are read-only, additive, and local-first.
- Phase 10D async coverage is read-only, mocked/local in tests and examples,
  and does not enable agent/MCP execution.
- Phase 10E async coverage is read-only, mocked/local in tests and examples,
  and does not enable financial/contract/project-management mutations,
  agent execution, or MCP execution.
- Phase 11A plugin helpers are metadata-only, local-first, and do not install,
  fetch, import, or execute plugins.
- Phase 13A golden evals are local and deterministic; they do not call Procore,
  call external AI/model APIs, execute plugins, fetch/upload datasets, or enable
  tool/MCP execution.
- Phase 13B, Phase 13C, and Phase 13D eval work remains local and deterministic; it does
  not call Procore, call external AI/model APIs, execute plugins, fetch remote
  datasets, fixtures, or baselines, upload reports, use model-as-judge scoring,
  or enable tool/MCP execution.

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
- Richer async attachment extraction
- Controlled plugin extension hooks beyond metadata
- Saved model-response comparison patterns without live model calls
- Richer MCP integration
