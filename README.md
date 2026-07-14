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
- Unreleased branch work: Phase 8A, Phase 8C, and Phase 8D read-only API coverage, plus Phase 8B client-credentials auth support
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
- Observations, Punch Items, Generic Tool correspondence items, Meetings, Inspections, Incidents, Directory users, Vendors, Departments, Distribution Groups, and Locations in the current unreleased branch
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

### Phase 7 Agent Layer

Included in `v2.2.0`:

- Agent Tool Registry
- Local agent API server
- OpenAPI / JSON Schema Export
- Agent Run Logs + Replay
- Discovery-only MCP Adapter
- Agent Evaluation Harness

The Phase 7 layer is local-first discovery/spec/eval/replay infrastructure. Tool execution remains disabled, MCP remains discovery-only, evals are local and deterministic, and metadata/schema/replay/MCP/eval commands do not call live Procore APIs.

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

## Security And Safety

- Never commit `.env` files, OAuth token stores, Authorization headers, access tokens, refresh tokens, client secrets, logs containing credentials, downloads, or private project data.
- Token stores, logs, downloads, generated exports, build artifacts, and local virtual environments are ignored by default.
- SDK logs redact common secret fields.
- The SDK is read-oriented; workflow helpers write local files and do not mutate Procore data.
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

- Phase 8A read-only coverage for Observations, Punch Items, and Generic Tool correspondence
- Phase 8B client-credentials auth support
- Phase 8C read-only coverage for Meetings, Inspections, and Incidents
- Phase 8D read-only coverage for Directory users, Vendors, Departments, Distribution Groups, and Locations

### Future

- Additional read-only coverage for Commitments, Change Events, Change Orders, and budget/financial resources where appropriate
- Guarded tool execution and human approval gates
- Write-action safety model
- Real MCP execution after explicit safety design
- Developer platform: async client and plugin architecture
- AI workflow examples: vector DB examples and engineering assistant examples
- Evaluation: golden datasets and model evals
- Deployment: private deployment patterns and richer MCP integration

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
