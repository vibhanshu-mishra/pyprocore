# PyProcore

> PyProcore is an open-source Python SDK, automation toolkit, and agent-ready infrastructure layer for Procore.

[![PyPI](https://img.shields.io/pypi/v/pyprocore.svg)](https://pypi.org/project/pyprocore/)
![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)
[![License](https://img.shields.io/pypi/l/pyprocore.svg)](LICENSE)
[![Tests](https://github.com/vibhanshu-mishra/pyprocore/actions/workflows/tests.yml/badge.svg)](https://github.com/vibhanshu-mishra/pyprocore/actions/workflows/tests.yml)
![Coverage](https://img.shields.io/badge/coverage-90%25-brightgreen.svg)

PyProcore helps developers, consultants, and construction teams build safe Procore integrations without rebuilding OAuth, token refresh, pagination, retries, typed response parsing, file downloads, exports, and local automation plumbing from scratch.

It is model-agnostic, local-first, and safety-first. The current stable release, `2.2.0`, includes the Phase 7 Agent Layer: local discovery/spec/eval/replay infrastructure for future assistant workflows. Procore tool execution remains disabled, the MCP adapter is discovery-only, and Phase 7 commands do not call external AI/model APIs.

Current repository status:

- Published stable release: `2.2.0`
- Unreleased branch work: Phase 8A–8G API/auth additions, Phase 9A
  enterprise authentication hardening, Phase 9B scheduled export planning,
  Phase 9C token-store/credential-rotation hardening, and Phase 9D private
  deployment/runbook guidance, plus Phase 12 model-agnostic AI workflow
  examples, plus Phase 10A async client foundation, Phase 10B async
  export/download patterns, Phase 10C async multi-project batch helpers, and
  Phase 10D async field, operations, correspondence, and directory coverage,
  plus Phase 10E async financial, contract, billing, and project-management
  read coverage, plus Phase 11A metadata-only plugin architecture foundation,
  Phase 11B safe local plugin extension hooks, Phase 11C plugin configuration
  and local extension-pack manifests, and Phase 11D plugin developer
  scaffolding/templates, plus Phase 13A local deterministic golden datasets
  and eval reports, plus Phase 13B workflow-specific golden eval suites for
  RFI, submittal, async export, async batch, AI workflow, plugin metadata/config,
  and safety-boundary artifacts
- Procore tool execution remains disabled

```bash
python3 -m pip install pyprocore==2.2.0
```

---

## What PyProcore Does

PyProcore turns Procore REST API responses into typed Python objects and gives you a practical toolkit for read-oriented automation:

- Authenticate with Procore through OAuth 2.0 and refresh tokens automatically.
- Work with typed Pydantic models instead of raw JSON dictionaries.
- List, fetch, search, export, sync, and download supported Procore resources.
- Build local review packages for RFIs, submittals, documents, and project context.
- Validate and dry-run enterprise scheduled export plans without calling Procore.
- Inspect token-store safety and print credential rotation checklists locally.
- Check private deployment readiness and review production runbook guidance locally.
- Build model-agnostic local AI workflow prompts, checklists, and vector export manifests.
- Use the unreleased async client foundation for read-oriented workflows with optional async HTTP support.
- Use unreleased async export and local download patterns with manifests and conservative concurrency controls.
- Plan read-only async multi-project batches with local dry-run manifests.
- Read additional field, operations, correspondence, and directory resources through the unreleased async client.
- Read financial, contract, billing, and project-management resources through
  the unreleased async client.
- Inspect metadata-only plugin manifests through the unreleased Phase 11A
  plugin architecture foundation.
- Register trusted local plugin hooks explicitly in-process through the
  unreleased Phase 11B hook registry.
- Validate JSON-only plugin configuration and extension-pack metadata through
  the unreleased Phase 11C helpers.
- Generate safe local plugin developer templates through the unreleased Phase
  11D scaffolding helpers.
- Run unreleased Phase 13A local deterministic golden evals for exports,
  manifests, workflow packages, async batch plans, plugin metadata, and safety
  boundaries.
- Run unreleased Phase 13B workflow-specific golden evals for RFI, submittal,
  async export, async batch, AI workflow package, plugin metadata/config, and
  safety-boundary artifacts.
- Use CLI diagnostics and automation commands without hardcoding credentials.
- Expose local agent metadata, OpenAPI/JSON Schema, run logs, replay, MCP discovery, and deterministic evals for future assistant integrations.

---

## Quick Start

Install the current stable release:

```bash
python3 -m pip install pyprocore==2.2.0
```

Create a `.env` file:

```bash
cp .env.example .env
```

Fill in your Procore OAuth and API values:

```bash
PROCORE_CLIENT_ID=your_client_id
PROCORE_CLIENT_SECRET=your_client_secret_keep_private
PROCORE_AUTH_MODE=authorization_code
PROCORE_REDIRECT_URI=http://localhost:8080/callback
PROCORE_LOGIN_URL=https://login.procore.com
PROCORE_API_BASE=https://api.procore.com
PROCORE_COMPANY_ID=123456
```

Check setup and complete OAuth:

```bash
procore-sdk doctor
procore-sdk auth login-url
procore-sdk auth exchange-code YOUR_AUTHORIZATION_CODE
procore-sdk companies
```

PyProcore loads `.env` from the current working directory and does not override environment variables that are already set.

---

## Feature Overview

### Core SDK

- OAuth 2.0 authorization-code flow
- Optional client-credentials flow for Data Connection Apps in the current unreleased branch
- Automatic token refresh
- Typed Pydantic models
- `requests.Session` transport
- Retries and transient failure handling
- Automatic pagination
- Structured logging with secret redaction
- Custom SDK exceptions
- Object-oriented `Procore` client
- Function-style service helpers
- Human-friendly resolver/search helpers
- CLI diagnostics and auth helpers

### Procore API Coverage

PyProcore is mostly read-oriented and built for safe automation. Current supported resource families include:

- Companies
- Projects
- RFIs
- Submittals
- Documents
- Drawings
- Specifications
- Photos
- Daily Logs
- Observations, Punch Items, Generic Tool correspondence items, Meetings, Inspections, Incidents, Directory users, Vendors, Departments, Distribution Groups, Locations, contracts, invoices, payments, schedules, tasks, calendar items, coordination issues, forms, and action plans in the current unreleased branch
- Attachments and files when Procore returns usable URLs

See [API Coverage](docs/api-coverage.md) for endpoint notes, live-verification limitations, and Procore permission context.

### Workflow Automation

- CSV exports
- JSONL exports
- Local folder sync
- Document sync
- Project sync
- Incremental sync state
- Workflow plans
- Scheduled export plan validation and dry-run manifests in the current unreleased branch
- Scheduled sync examples
- Local webhook helpers
- Docker and CI examples

Workflow helpers create local files and do not mutate Procore data.

### AI-Ready Local Packages

- Project context packages
- Enhanced RFI packages
- Enhanced submittal packages
- AI review exports
- AI prompt packs
- JSON, JSONL, Markdown, manifest, source-index, prompt, and checklist files

AI-ready package builders write local files only. They do not call external AI/model services by default.

### Phase 12 AI Workflow Examples

Prepared in the current unreleased branch:

- RFI review assistant prompt packages
- Submittal review assistant prompt packages
- Project context Q&A packages
- Drawing/spec comparison prompt packages
- Vector DB/chunk export manifests without a vector database dependency
- Engineering assistant context bundles
- Field issue summarizer packages
- Change-risk review packages

Phase 12 is model-agnostic and local-only. PyProcore does not call external
AI/model APIs, does not require AI framework dependencies, does not execute MCP
tools, and does not enable Procore tool execution. See
[AI Workflows](docs/ai-workflows.md).

### Phase 10A Async Client Foundation

Prepared in the current unreleased branch:

- `AsyncProcore` async entry point
- async transport abstraction and local `MockAsyncTransport`
- optional real async HTTP transport via `pyprocore[async]`
- async request, retry, 401 refresh, error mapping, and pagination helpers
- async read coverage for companies, projects, RFIs, submittals, documents,
  drawings, and specification sections

The existing sync `Procore` client remains supported and unchanged. Phase 10A
does not add write actions, does not call external AI/model APIs, does not
enable agent execution, and keeps MCP discovery-only. See
[Async Client](docs/async-client.md).

### Phase 10B Async Exports And Download Patterns

Prepared in the current unreleased branch:

- async CSV and JSONL export helpers for common read resources
- async local download helpers for records that include direct download URLs
- `AsyncExportResult`, `AsyncDownloadResult`, and manifest models
- conservative `max_concurrency` controls for download batches
- examples 147–152 using mock transports and temporary folders

Phase 10B is additive and read-only. It does not replace sync exports, does not
upload files, does not mutate Procore data, does not call external AI/model
APIs, does not enable agent execution, and keeps MCP discovery-only. See
[Async Client](docs/async-client.md).

### Phase 10C Async Multi-Project Batch Helpers

Prepared in the current unreleased branch:

- async batch plans, manifests, project/resource results, and findings
- local-only validation and dry-run planning for multi-project async exports
- async exports for RFIs, submittals, documents, drawings, and specification sections
- in-memory async collection helpers for the same resource set
- conservative concurrency controls, partial-failure capture, and simple manifest resume/skip support
- `procore-sdk async-batch sample-config`, `validate`, and `dry-run`

Phase 10C is additive and read-only. CLI validation and dry-runs do not call
Procore or require credentials. Library exports call Procore only when a
developer passes a configured async client and uses a non-dry-run plan. No
upload, create, update, delete, approval, status-change, external AI/model,
agent execution, or MCP execution behavior is added.

### Phase 10D Async Coverage Expansion

Prepared in the current unreleased branch:

- async read coverage for photo albums, photos, Daily Logs, observations, punch items, Generic Tools, correspondence, meetings, inspections, incidents, and directory resources
- async find helpers for observations, punch items, correspondence, meetings, inspections, incidents, users, vendors, departments, distribution groups, and locations
- async CSV/JSONL export helpers for the new resource families
- async batch support for observations, punch items, meetings, inspections, incidents, locations, project users, and vendors
- examples 161–168 using mock transports or local dry-runs

Phase 10D is additive and read-only. It does not add Procore writes, uploads,
approvals, status changes, external AI/model calls, agent execution, or MCP
execution.

### Phase 10E Async Financial, Contract, And Project Management Coverage

Prepared in the current unreleased branch:

- async read coverage for change events, change orders, direct costs, budget views/details, cost codes, WBS codes, and commitments
- async read coverage for prime contracts, owner invoices, subcontractor invoices, contract payments, billing periods, cost types, and tax codes
- async read coverage for schedule metadata, tasks, calendar items, coordination issues, forms, form templates, and action plans
- async CSV/JSONL export helpers for selected Phase 10E resource families
- async batch support for selected financial, contract, billing, and project-management resources
- examples 169–176 using mock transports or local dry-runs

Phase 10E is additive and read-only. It does not add approvals, submissions,
status changes, payment actions, budget edits, contract edits, schedule imports,
form submissions, action-plan completions, external AI/model calls, agent
execution, or MCP execution.

### Phase 11A Plugin Architecture Foundation

Prepared in the current unreleased branch:

- metadata-only plugin manifests
- safe local plugin registry
- built-in example manifests for future exporter, workflow, validator, report,
  agent metadata, and MCP metadata extension categories
- local manifest validation
- `procore-sdk plugins list`
- `procore-sdk plugins show NAME`
- `procore-sdk plugins manifest`
- `procore-sdk plugins sample-manifest`
- `procore-sdk plugins validate PATH`

Phase 11A does not install plugins, fetch remote registries, import arbitrary
plugin modules, execute plugin code, call Procore, call external AI/model APIs,
or enable agent/MCP execution. See [Plugin Architecture](docs/plugins.md).

### Phase 11B Safe Local Plugin Extension Hooks

Prepared in the current unreleased branch:

- typed hook metadata for validators, exporters, formatters, reports, workflow
  helpers, and record transformers
- explicit in-process hook registration for trusted local callables
- built-in deterministic local hooks for validation, summaries, field selection,
  JSONL payloads, and quality reports
- `procore-sdk plugins hooks`
- `procore-sdk plugins hook-manifest`
- `procore-sdk plugins sample-hook-manifest`
- built-in sample hook demo commands

Phase 11B does not install plugins, fetch remote registries, import arbitrary
modules, run manifest metadata as code, call Procore, call external AI/model
APIs, add write actions, or enable agent/MCP execution. See
[Plugin Architecture](docs/plugins.md).

### Phase 11C Plugin Configuration and Local Extension Packs

Prepared in the current unreleased branch:

- JSON-only plugin configuration models
- hook preference metadata
- capability preference metadata
- local extension-pack manifests
- registry metadata filtering from config
- `procore-sdk plugins config sample`
- `procore-sdk plugins config validate PATH`
- `procore-sdk plugins config summary PATH`
- `procore-sdk plugins config manifest PATH`
- `procore-sdk plugins extension-pack sample`
- `procore-sdk plugins extension-pack validate PATH`
- `procore-sdk plugins extension-pack summary PATH`

Phase 11C config files and extension packs are metadata only. They do not
install plugins, fetch remote resources, import modules, register executable
callables, execute hooks, call Procore, call external AI/model APIs, add write
actions, or enable agent/MCP execution. See
[Plugin Architecture](docs/plugins.md).

### Phase 11D Plugin Developer Scaffolding

Prepared in the current unreleased branch:

- local scaffold request, plan, file, finding, and result models
- dry-run scaffold planning
- safe writes under a selected output directory
- overwrite controls that skip existing files by default
- static JSON, Markdown, docs, example, and test templates
- `procore-sdk plugins scaffold sample-plan`
- `procore-sdk plugins scaffold dry-run --name NAME --output-dir PATH`
- `procore-sdk plugins scaffold create --name NAME --output-dir PATH`
- `procore-sdk plugins scaffold extension-pack --name NAME --output-dir PATH`
- `procore-sdk plugins scaffold config --name NAME --output-dir PATH`
- `procore-sdk plugins scaffold hook-pack --name NAME --output-dir PATH`

Phase 11D scaffolding creates templates only. It does not install plugins,
fetch remote resources, auto-load modules, execute generated files, execute
hooks from config, call Procore, call external AI/model APIs, add write
actions, or enable agent/MCP execution. See
[Plugin Architecture](docs/plugins.md).

### Phase 13 Golden Dataset Evals

Prepared in the current unreleased branch:

- typed golden dataset, case, expected-output, finding, score, suite, and
  report models
- deterministic scoring helpers for exact matches, required keys, forbidden
  keys, text checks, row counts, JSON serializability, redaction checks, and
  manifest integrity
- built-in placeholder datasets for export rows, agent manifests, AI workflow
  packages, async batch plans, plugin metadata, and safety boundaries
- workflow-specific golden eval suites for RFI exports/packages, submittal
  exports/packages, async exports, async batch manifests, AI workflow packages,
  plugin metadata/config, and cross-SDK safety boundaries
- JSON and Markdown report builders
- `procore-sdk evals list`
- `procore-sdk evals run`
- `procore-sdk evals run --suite rfi_workflow_golden`
- `procore-sdk evals validate-dataset PATH`
- `procore-sdk evals report --format json`
- `procore-sdk evals sample-dataset`
- `procore-sdk evals sample-report`

Phase 13 evals inspect local deterministic artifacts only. They do not call
Procore, call external AI/model APIs, execute Procore tools, execute MCP,
execute plugins, fetch remote datasets, load arbitrary code, or upload reports. See
[Golden Evals](docs/evals.md).

### Phase 7 Agent Layer

Included in `v2.2.0`:

- Agent Tool Registry
- Local agent API server
- OpenAPI / JSON Schema Export
- Agent Run Logs + Replay
- Discovery-only MCP Adapter
- Agent Evaluation Harness

The Phase 7 layer is local-first discovery/spec/eval/replay infrastructure. Tool execution remains disabled, MCP remains discovery-only, evals are local and deterministic, and metadata/schema/replay/MCP/eval commands do not call live Procore APIs.

### Unreleased Phase 8G Read Coverage

The current branch adds read-only helpers for project-management extras:

- Schedule metadata, settings, type, integration, import status, and resource assignments
- Tasks and task requested changes
- Calendar items
- Coordination issues, change history, activity feed, and filter options
- Forms and form templates
- Action plans and change history events

No schedule uploads/import creation, task writes, coordination issue mutations,
form submissions, action plan completions, approvals, status changes, or other
project-management mutations are implemented.

---

## Python Examples

Use the object client:

```python
from pyprocore import Procore

client = Procore()

projects = client.projects.list(company_id=123456)
for project in projects:
    print(project.id, project.name)
```

List RFIs and submittals:

```python
from pyprocore import Procore

client = Procore()

open_rfis = client.rfis.list(project_id=352338, status="open")
pending_submittals = client.submittals.list(project_id=352338, status="pending")

print(len(open_rfis))
print(len(pending_submittals))
```

Build an enhanced RFI package:

```python
from pyprocore.workflows import build_enhanced_rfi_package

result = build_enhanced_rfi_package(
    project_id=352338,
    company_id=4286480,
    rfi_number="15",
    output_dir="exports/rfi-15",
    related_sections=["drawings", "specifications", "submittals"],
    download_files=False,
)

print(result.review_context_path)
```

Build a project context package:

```python
from pyprocore.workflows import build_project_context_package

result = build_project_context_package(
    project_id=352338,
    company_id=4286480,
    output_dir="exports/project-context",
    include=["project", "rfis", "submittals", "daily_logs"],
    max_items=100,
)

print(result.summary_path)
```

Inspect the local agent registry:

```python
from pyprocore.agent.registry import get_default_agent_registry

registry = get_default_agent_registry()
for tool in registry.list_tools():
    print(tool.name, tool.description)
```

---

## CLI Overview

Use `procore-sdk --help` for the full command list. Common command groups include:

```bash
procore-sdk doctor
procore-sdk auth status
procore-sdk companies
procore-sdk projects
procore-sdk rfis --project 352338
procore-sdk submittals --project 352338
procore-sdk documents --project 352338
procore-sdk drawings --project 352338
procore-sdk specification-sections --project 352338
procore-sdk photo-albums --project 352338
procore-sdk daily-log-counts --project 352338
procore-sdk project-context --project 352338 --company 4286480
procore-sdk enhanced-rfi-package --project 352338 --company 4286480 --rfi-number 15
procore-sdk enhanced-submittal-package --project 352338 --company 4286480 --submittal-number 27
procore-sdk ai-review-export --package-dir ./exports/rfi-15
procore-sdk ai-prompt-pack --package-dir ./exports/rfi-15
procore-sdk workflow-plan validate examples/workflow_plans/project_context_and_ai_export.json
procore-sdk scheduled-export validate examples/configs/scheduled_export_client_credentials.json
procore-sdk scheduled-export dry-run examples/configs/scheduled_export_client_credentials.json
procore-sdk webhook validate examples/webhooks/rfi_created_event.json
```

See [CLI](docs/cli.md) for the full command reference.

---

## Agent Layer

Phase 7 commands expose local metadata and safety checks for future assistant workflows:

```bash
procore-sdk agent tools
procore-sdk agent manifest --json
procore-sdk agent openapi --pretty
procore-sdk agent schemas --pretty
procore-sdk agent serve --port 8765
procore-sdk agent mcp tools --pretty
procore-sdk agent evals run
```

The local agent API server exposes discovery endpoints for manifests, schemas,
OpenAPI output, and disabled tool-call responses.

Safety posture:

- Tool execution is disabled.
- MCP adapter is discovery-only.
- Agent evals are local and deterministic.
- Metadata, schema, replay, MCP, and eval commands do not call live Procore APIs.
- Phase 7 does not call external AI/model APIs.

See [Agent API](docs/agent-api.md) for details.

Docker and CI helpers are documented in [Docker Automation](docs/automation/docker.md)
and [CI Automation](docs/automation/ci.md). Example Docker assets live under
[examples/docker](examples/docker/).

---

## Enterprise Scheduled Exports

Unreleased Phase 9B adds local scheduled export plan validation and dry-run
manifests for enterprise Data Connection App deployment patterns:

```bash
procore-sdk scheduled-export sample-config
procore-sdk scheduled-export validate examples/configs/scheduled_export_client_credentials.json
procore-sdk scheduled-export dry-run examples/configs/scheduled_export_client_credentials.json
```

These commands do not call Procore, do not require credentials, do not run
exports, and do not print secrets. Use `client_credentials` for unattended
server-to-server jobs and `authorization_code` for user-owned local workflows.

See [Enterprise Scheduled Exports](docs/enterprise-scheduled-exports.md).

---

## Token Store And Credential Rotation

Unreleased Phase 9C adds local token-store backend diagnostics and credential
rotation guidance:

```bash
procore-sdk token-store status
procore-sdk token-store inspect
procore-sdk token-store sample-paths
procore-sdk auth rotation-checklist --auth-mode client_credentials
```

These commands never print raw token values or client secrets. Keep token stores
outside the repository, separate sandbox and production token stores, and dry-run
scheduled exports after credential rotation.

See [Token Store and Rotation](docs/token-store-and-rotation.md).

---

## Private Deployment And Production Runbooks

Unreleased Phase 9D adds local-only private deployment readiness checks,
production runbooks, and placeholder deployment templates for internal teams.
PyProcore does not host infrastructure, does not automatically schedule jobs,
does not call external AI/model APIs by default, and does not enable tool
execution.

```bash
procore-sdk enterprise readiness-check
procore-sdk enterprise sample-layout
procore-sdk enterprise runbook-summary
procore-sdk enterprise deployment-pattern --pattern cron
```

Client Credentials / Data Connection App auth is recommended for unattended
server-to-server scheduled exports. Authorization Code remains supported for
user-driven local workflows.

See [Private Deployment](docs/private-deployment.md) and
[Production Runbook](docs/production-runbook.md).

---

## Security And Safety

- Never commit `.env` files, OAuth token stores, Authorization headers, access tokens, refresh tokens, client secrets, logs containing credentials, downloads, or private project data.
- Token stores, logs, downloads, generated exports, build artifacts, and local virtual environments are ignored by default.
- SDK logs redact common secret fields.
- The SDK is read-oriented; workflow helpers write local files and do not mutate Procore data.
- Scheduled export validation and dry-runs are local planning tools only.
- Agent tool execution remains disabled.
- MCP is discovery-only.
- Run the local secret scanner before opening pull requests:

```bash
make secret-check
```

See [Security](docs/security.md) and [SECURITY.md](SECURITY.md).

---

## Documentation Site

- [Documentation Home](docs/index.md)
- [Project Status](docs/project-status.md)
- [Getting Started](docs/getting-started.md)
- [Authentication](docs/authentication.md)
- [CLI](docs/cli.md)
- [API Coverage](docs/api-coverage.md)
- [Workflows](docs/workflows.md)
- [AI Review](docs/ai-review.md)
- [AI Workflows](docs/ai-workflows.md)
- [Async Client](docs/async-client.md)
- [Agent API](docs/agent-api.md)
- [Automation](docs/automation.md)
- [Recipes](docs/recipes/)
- [Examples](examples/README.md)
- [Release Guide](docs/release.md)
- [Changelog](CHANGELOG.md)
- [Security Policy](SECURITY.md)

For local docs development:

```bash
make docs-serve
make docs-build
```

---

## Local Development

```bash
git clone https://github.com/vibhanshu-mishra/pyprocore.git
cd pyprocore
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[dev]"
```

When testing unreleased local CLI changes, use `PYTHONPATH=.` so Python resolves the checkout before any installed copy:

```bash
PYTHONPATH=. procore-sdk --help
PYTHONPATH=. python3 -m pyprocore.app --help
```

Common checks:

```bash
make examples-check
make test
make coverage
make lint
make typecheck
make quality-check
```

---

## Roadmap

### Released in 2.2.0

- Phase 7 Agent Layer
- Agent Tool Registry
- Local Agent API Server
- OpenAPI / JSON Schema Export
- Agent Run Logs + Replay
- Discovery-only MCP Adapter
- Agent Evaluation Harness

### Unreleased Branch Work

- Phase 9A hardens Authorization Code OAuth and Client Credentials/Data
  Connection App workflows with strict mode validation, safer token-store errors,
  and local permission diagnostics.
- Phase 9B adds local scheduled export plan models, validation, dry-run
  manifests, safe sample configs, examples, scripts, and enterprise deployment
  guidance. Version `2.2.0` remains the published stable release; this work is
  unreleased.
- Phase 9C adds token-store backend architecture, safe token-store inspection,
  memory backends for tests/examples, credential rotation checklists, and
  enterprise deployment readiness guidance. It is unreleased branch work.
- Phase 9D completes Phase 9 on main with private deployment patterns,
  production runbooks, enterprise readiness checks, safe templates, examples,
  and scripts. It is unreleased branch work.
- Phase 12 adds model-agnostic AI workflow examples, local prompt/checklist
  helpers, vector export manifest samples, templates, and safety checks. It is
  unreleased branch work and does not call external AI/model APIs.
- Phase 10A adds an async client foundation, mock async transport, optional
  async HTTP transport, async pagination/retry/error handling, and initial
  read-only async coverage for core resources. It is unreleased branch work.
- Phase 10C adds async multi-project batch planning, validation, dry-run
  manifests, read-only exports, in-memory collection helpers, and conservative
  concurrency controls. It is unreleased branch work.
- Phase 10D expands async read coverage to field, operations, correspondence,
  and directory resources, with local exports and selected async batch
  resources. It is unreleased branch work.
- Phase 10E expands async read coverage to financial, contract, billing, and
  project-management resources, with local exports and selected async batch
  resources. It is unreleased branch work.

- Phase 8A read-only coverage for Observations, Punch Items, and Generic Tool correspondence
- Phase 8B client-credentials auth support
- Phase 8C read-only coverage for Meetings, Inspections, and Incidents
- Phase 8D read-only coverage for Directory users, Vendors, Departments, Distribution Groups, and Locations
- Phase 8E read-only coverage for financial and change-management resources:
  Change Events, Prime Change Orders, Commitment Change Orders, Change Order
  Packages, Direct Costs, Budget Views/Details, Cost Codes, WBS Codes, and
  Commitments
- Phase 8F read-only coverage for contracts, invoices, payments, and billing:
  Prime Contracts, Commitment/Purchase Order/Work Order Contracts, Owner
  Invoices, Subcontractor Invoices, Contract Payments, Billing Periods, Cost
  Types, and Tax Codes. No contract, invoice, payment, approval, submission,
  status-change, PDF-generation, SOV, or line-item mutation behavior is included.
- Phase 8G read-only coverage for schedules, tasks, calendar items,
  coordination issues, forms, and action plans. No project-management write,
  upload, submission, approval, status-change, or completion behavior is included.

### Future

- Additional read-only Procore coverage where endpoint shapes are safe and clear
- Guarded tool execution and human approval gates
- Write-action safety model
- Real MCP execution after explicit safety design
- Developer platform: richer async orchestration and plugin architecture
- Evaluation: saved model-response comparison patterns without live model calls
- Deployment: richer MCP integration after explicit safety design

See [Roadmap](docs/roadmap.md).

---

## About

Built by **Vibhanshu Mishra, PE** — Structural Engineer at AG&E Structural Engenuity, Austin, TX.

Specialising in steel and mission-critical structures. Building AI and automation tools for a niche that deserves better software.

- [RISA-3D MCP Server](https://github.com/vibhanshu-mishra/risa3d-mcp-server) — Connect Claude AI to RISA-3D structural models
- [TSD MCP Server](https://github.com/vibhanshu-mishra/tsd-mcp) — Connect Claude AI to TSD structural models

---

## Contributing and Support

Contributions, issues, and feature requests are welcome. Start with [CONTRIBUTING.md](CONTRIBUTING.md), [SUPPORT.md](SUPPORT.md), [SECURITY.md](SECURITY.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), and [docs/github-labels.md](docs/github-labels.md).

Please open an issue before submitting large changes, and never paste Procore client secrets, access tokens, refresh tokens, `.env` values, token stores, Authorization headers, or private project data into public issues or pull requests.

---

## License

Released under the MIT License. See [LICENSE](LICENSE) for details.

---

> PyProcore is an independent open-source project and is not affiliated with or endorsed by Procore Technologies.
