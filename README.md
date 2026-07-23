# PyProcore

> Open-source Python SDK and automation toolkit for safe, read-oriented Procore integrations.

[![PyPI](https://img.shields.io/pypi/v/pyprocore.svg)](https://pypi.org/project/pyprocore/)
![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)
[![License](https://img.shields.io/pypi/l/pyprocore.svg)](LICENSE)
[![Tests](https://github.com/vibhanshu-mishra/pyprocore/actions/workflows/tests.yml/badge.svg)](https://github.com/vibhanshu-mishra/pyprocore/actions/workflows/tests.yml)
![Coverage](https://img.shields.io/badge/coverage-90%25-brightgreen.svg)

PyProcore helps developers, consultants, and construction-tech teams build
Procore integrations without rebuilding OAuth, token refresh, pagination,
retries, typed response parsing, downloads, exports, and local automation
plumbing from scratch.

The SDK is read-oriented and safety-first. It is designed for listing,
retrieving, searching, downloading, exporting, packaging, and validating Procore
project data while keeping write and execution surfaces closed by default.

The current stable release is `2.3.0`. It includes typed API access, local
workflow exports, async read helpers, enterprise scheduled-export planning,
metadata-only plugin scaffolding, deterministic evals, and discovery-only MCP
metadata. PyProcore does not call external AI/model APIs by default.

## Installation

Install the current stable release:

```bash
python3 -m pip install pyprocore==2.3.0
```

Install optional async HTTP support:

```bash
python3 -m pip install "pyprocore[async]==2.3.0"
```

## Quick Start

Create and configure a local `.env` file:

```bash
cp .env.example .env
```

Check your setup and complete OAuth:

```bash
procore-sdk doctor
procore-sdk auth login-url
procore-sdk auth exchange-code YOUR_AUTHORIZATION_CODE
procore-sdk companies
```

Use the object client:

```python
from pyprocore import Procore

client = Procore()

projects = client.projects.list(company_id=123456)
for project in projects:
    print(project.id, project.name)
```

Build a local project context package:

```python
from pyprocore.workflows import build_project_context_package

result = build_project_context_package(
    project_id=352338,
    company_id=4286480,
    output_dir="exports/project-context",
    include=["project", "rfis", "submittals"],
    max_items=100,
)

print(result.summary_path)
```

PyProcore loads `.env` from the current working directory and does not override
environment variables that are already set.

## What You Can Build

### Typed Procore API Access

- Work with typed Pydantic models instead of raw JSON dictionaries.
- Use an object-oriented `Procore` client or function-style service helpers.
- Rely on automatic pagination, retries, token refresh, and custom SDK errors.

### Local Exports And Sync Workflows

- Export supported resources to CSV, JSONL, Markdown, and manifest files.
- Build repeatable local workflow plans for project exports.
- Run dry-run and validation helpers before scheduled automation.

### AI-Ready Local Context Packages

- Package RFIs, submittals, documents, drawings, specs, and project context for
  review workflows.
- Generate local prompt packs, checklists, source indexes, and vector-export
  manifests.
- Keep model selection outside the SDK; no AI provider is called by default.

### Async Read Workflows

- Use `AsyncProcore` for read-oriented async workflows.
- Export and download with conservative concurrency controls.
- Plan async multi-project batches with local validation and dry-run manifests.

### Enterprise Scheduled-Export Planning

- Validate scheduled export configs locally.
- Review token-store safety and credential rotation guidance.
- Use private deployment and production runbook docs for operational planning.

### Plugin Metadata And Local Extension Scaffolding

- Inspect metadata-only plugin manifests and extension-pack files.
- Register trusted in-process hooks only from local application code.
- Generate local plugin developer templates without fetching or installing
  remote plugins.
- Validate local plugin trust policies and metadata-only trust reports without
  installing, importing, or executing plugin code.

### Local OAS Catalog Intelligence

- Inspect a user-provided local OpenAPI/OAS JSON file.
- Classify endpoints as read-only, risky/write, or unknown from metadata.
- Compare endpoint areas to known PyProcore read coverage.
- Produce JSON or Markdown reports without fetching remote catalogs, generating
  executable tools, calling Procore, or enabling writes.

### Deterministic Evals And Regression Checks

- Run local golden eval suites for workflow packages and manifests.
- Compare deterministic baselines and regression reports.
- Score offline model-response fixtures without calling a model.

### MCP Discovery Metadata

- Inspect MCP-style resources, prompts, contracts, snapshots, and reports.
- Inspect the local agent tool registry, local agent API server, agent OpenAPI
  and JSON Schema exports, and replay metadata.
- Validate discovery metadata locally without credentials.
- Keep MCP discovery separate from tool execution.

## Supported Resource Families

PyProcore supports read-oriented access across these resource families:

- Companies and Projects
- RFIs and Submittals
- Project Tools, Documents, Drawings, Specifications, Photos, and Daily Logs
- Observations, Punch Items, Correspondence, Meetings, Inspections, and Incidents
- Directory, Vendors, Departments, Distribution Groups, and Locations
- Read-only financial, contract, billing, schedule, task, form, coordination
  issue, and action-plan metadata

See [API Coverage](docs/api-coverage.md) for endpoint notes, permission context,
and live-verification limitations.

## CLI Overview

Common commands:

```bash
procore-sdk doctor
procore-sdk companies
procore-sdk projects
procore-sdk rfis --project 352338
procore-sdk submittals --project 352338
procore-sdk project-context --project 352338 --company 4286480
procore-sdk scheduled-export dry-run examples/configs/scheduled_export_client_credentials.json
procore-sdk evals run
procore-sdk mcp validate
procore-sdk catalog summarize examples/catalog/fake_procore_oas.json
```

See [CLI Usage](docs/cli.md) for the full command reference.

## Safety Model

PyProcore is intentionally conservative:

- PyProcore is read-oriented.
- Workflow helpers write local files, not Procore data.
- Procore tool execution is disabled.
- MCP is discovery-only.
- No external AI/model APIs are called by default.
- Plugin manifests, configs, extension packs, and scaffolds are metadata or
  templates only.
- No Procore create, update, delete, upload, approve, submit, payment, or other
  mutation actions are enabled.

Never commit `.env` files, OAuth tokens, token stores, Authorization headers, or
private project data.

## Documentation Site

| Topic | Link |
| --- | --- |
| Documentation Home | [docs/index.md](docs/index.md) |
| Getting Started | [docs/getting-started.md](docs/getting-started.md) |
| Authentication | [docs/authentication.md](docs/authentication.md) |
| API Coverage | [docs/api-coverage.md](docs/api-coverage.md) |
| Workflows | [docs/workflows.md](docs/workflows.md) |
| Docker Automation | [docs/automation/docker.md](docs/automation/docker.md) |
| CI Automation | [docs/automation/ci.md](docs/automation/ci.md) |
| Docker Examples | [examples/docker](examples/docker) |
| Async Client | [docs/async-client.md](docs/async-client.md) |
| AI Workflows | [docs/ai-workflows.md](docs/ai-workflows.md) |
| Agent API | [docs/agent-api.md](docs/agent-api.md) |
| MCP Discovery | [docs/mcp.md](docs/mcp.md) |
| Plugins | [docs/plugins.md](docs/plugins.md) |
| Golden Evals | [docs/evals.md](docs/evals.md) |
| Release Guide | [docs/release.md](docs/release.md) |
| Roadmap | [docs/roadmap.md](docs/roadmap.md) |
| Examples | [examples/README.md](examples/README.md) |
| Project Status | [docs/project-status.md](docs/project-status.md) |
| GitHub Labels | [docs/github-labels.md](docs/github-labels.md) |

Run `make docs-build` to build the MkDocs site or `make docs-serve` to preview
it locally.

## What Is New In v2.3.0

`v2.3.0` is an additive, backward-compatible release. Highlights include:

- Expanded read coverage for field, directory, financial, contract, billing,
  schedule, task, form, coordination issue, and action-plan metadata.
- Enterprise auth, token-store, scheduled-export, private deployment, and
  production runbook hardening.
- Async client, async export/download helpers, async batch planning, and broader
  async read coverage.
- Metadata-only plugin manifests, JSON config, local hooks, extension-pack
  metadata, and local scaffolding.
- Model-agnostic AI workflow examples and local context package helpers.
- Deterministic evals, regression checks, and offline model-response fixtures.
- Discovery-only MCP resources, prompts, contracts, snapshots, and reports.

Detailed release history lives in [CHANGELOG.md](CHANGELOG.md),
[Project Status](docs/project-status.md), and [Roadmap](docs/roadmap.md).

## Contributing and Support

Contributions, issues, and feature requests are welcome. Start with
[CONTRIBUTING.md](CONTRIBUTING.md), [SUPPORT.md](SUPPORT.md),
[SECURITY.md](SECURITY.md), and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Security

Do not paste or commit Procore client secrets, access tokens, refresh tokens,
Authorization headers, `.env` files, token stores, or private project data. See
[SECURITY.md](SECURITY.md) and [docs/security.md](docs/security.md).

Maintainers can run `make secret-check` and `make quality-check` before release
or documentation changes.

## License

PyProcore is released under the license described in [LICENSE](LICENSE).

## Disclaimer

PyProcore is an independent open-source project. It is not affiliated with,
endorsed by, or supported by Procore Technologies. For official Procore product
support, use Procore's support channels.
