# PyProcore

> Open-source Python SDK and automation toolkit for safe, read-oriented Procore integrations.

<p align="center">
  <img src="https://img.shields.io/pypi/v/pyprocore?style=for-the-badge&logo=pypi&logoColor=white&label=PyPI" alt="PyPI version">
  <img src="https://img.shields.io/badge/Python-3.12%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.12+">
  <img src="https://img.shields.io/github/actions/workflow/status/vibhanshu-mishra/pyprocore/tests.yml?branch=main&style=for-the-badge&logo=github&label=Tests" alt="Tests">
  <img src="https://img.shields.io/badge/Coverage-90%25-2E8B57?style=for-the-badge" alt="Coverage 90%">
  <img src="https://img.shields.io/pypi/l/pyprocore?style=for-the-badge&label=License" alt="License">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Read--Oriented-Safety--First-0B1320?style=for-the-badge" alt="Read-oriented safety-first">
  <img src="https://img.shields.io/badge/MCP-Discovery--Only-5D2E8C?style=for-the-badge" alt="MCP discovery-only">
  <img src="https://img.shields.io/badge/API%20Maintenance-Human--Review-D72638?style=for-the-badge" alt="Human-review API maintenance">
  <img src="https://img.shields.io/badge/Procore%20Writes-Disabled-8B0000?style=for-the-badge" alt="Procore writes disabled">
</p>

PyProcore helps developers, consultants, and construction-tech teams build
Procore integrations without rebuilding OAuth, token refresh, pagination,
retries, typed response parsing, downloads, exports, and local automation
plumbing from scratch.

The SDK is read-oriented and safety-first. It is designed for listing,
retrieving, searching, downloading, exporting, packaging, and validating Procore
project data while keeping write and execution surfaces closed by default.

The latest published stable release is `2.4.0`.

Highlights:
- Read-only Project Tools coverage
- Local analytics and FastAPI starter template
- OAS catalog and discovery metadata
- Human-review API maintenance workflows for drift, impact, migration plans, PR drafts, compatibility contracts, and migration guides

These features remain read-only, local, or report-oriented. MCP is
discovery-only, Procore tool execution is disabled, and no external AI/model
API is called by default. Maintenance helpers do not fetch remote code/specs,
edit customer code, apply patches, run git, call GitHub, or open pull requests.

## Installation

Install the current stable release:

```bash
python3 -m pip install pyprocore==2.4.0
```

Install optional async HTTP support:

```bash
python3 -m pip install "pyprocore[async]==2.4.0"
```

The `2.4.0` package is available from PyPI and the source repository.

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

### Read-Only Procore Data Tools

- Build typed Procore integrations for companies, projects, RFIs, submittals,
  documents, drawings, specifications, photos, Daily Logs, observations, punch
  items, correspondence, meetings, inspections, incidents, directory data,
  financial metadata, contracts, schedules, tasks, forms, and Project Tools.
- Use OAuth, token refresh, pagination, retries, typed models, exports, and
  custom SDK errors without rebuilding the plumbing from scratch.

### Local Reporting And Export Workflows

- Export supported resources to CSV, JSONL, Markdown, manifests, and local
  project context packages.
- Build repeatable read-only workflows for audits, reviews, reporting,
  scheduled-export planning, and project documentation.

### AI-Ready Local Context Packages

- Package project data into local prompt packs, source indexes, checklists, and
  vector-export manifests.
- Keep model choice outside the SDK: PyProcore prepares local context, but does
  not call external AI/model APIs by default.

### Async And Batch Read Workflows

- Use `AsyncProcore` for read-oriented async integrations.
- Plan multi-project exports and downloads with conservative concurrency,
  dry-run manifests, and local validation.

### Local Analytics And Project Health Reviews

- Analyze exported/local RFI, submittal, change, and Daily Log records.
- Generate deterministic project health summaries without calling Procore,
  running AI, hosting dashboards, or adding database dependencies.

### API Discovery And OAS Intelligence

- Inspect local OpenAPI/OAS files, classify endpoints, compare coverage gaps,
  and detect API drift.
- Generate local JSON and Markdown reports for endpoint review without fetching
  remote specs, generating executable tools, calling Procore, or enabling writes.

### Templates, Blueprints, And Plugin Metadata

- Copy optional starter templates such as the FastAPI read-only API example.
- Inspect local integration blueprints, plugin manifests, extension packs, trust
  policies, and scaffolds without installing remote plugins or executing plugin
  code.

### Agent, MCP, And Evaluation Metadata

- Inspect local agent API metadata, JSON Schemas, OpenAPI exports, run logs,
  replay metadata, MCP-style resources, prompts, contracts, and snapshots.
- Run deterministic golden evals and offline model-response fixture checks
  without calling live models or enabling tool execution.

### Self-Maintaining API Maintenance Assistant

- Compare local OAS files and detect API drift.
- Scan a local codebase for PyProcore usage.
- Generate migration plans, patch suggestions, PR draft packs, compatibility contracts, and migration guides.
- Keep everything local and human-reviewed: no code edits, no git commands, no GitHub API calls, no Procore calls.

See the [complete feature inventory](docs/features.md) for the full
phase-by-phase breakdown.

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
procore-sdk discovery search "overdue rfis"
procore-sdk analytics project-health --rfis examples/analytics/fake_rfis.json --format markdown
procore-sdk templates show fastapi-read-api
procore-sdk templates copy fastapi-read-api --output-dir ./tmp-fastapi-read-api --dry-run
procore-sdk maintenance drift old_oas.json new_oas.json --format markdown
procore-sdk maintenance usage-scan ./my-project --format markdown
procore-sdk maintenance migration-guide --from-contract old.json --to-contract new.json --format markdown
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
| Complete Feature Inventory | [docs/features.md](docs/features.md) |
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
| Analytics Recipes | [docs/analytics-recipes.md](docs/analytics-recipes.md) |
| FastAPI Starter | [docs/fastapi-starter.md](docs/fastapi-starter.md) |
| Golden Evals | [docs/evals.md](docs/evals.md) |
| Release Guide | [docs/release.md](docs/release.md) |
| Roadmap | [docs/roadmap.md](docs/roadmap.md) |
| Examples | [examples/README.md](examples/README.md) |
| Project Status | [docs/project-status.md](docs/project-status.md) |
| GitHub Labels | [docs/github-labels.md](docs/github-labels.md) |

Run `make docs-build` to build the MkDocs site or `make docs-serve` to preview
it locally.

## Released In v2.4.0

`v2.4.0` is an additive, backward-compatible published release. Highlights:

- Read-only Project Tools metadata helpers.
- Local plugin trust policies and compatibility reports.
- Local OAS catalog, discovery routing, integration blueprints, analytics
  recipes, and an optional copied FastAPI starter.
- Human-review API drift, codebase impact, migration planning, PR draft,
  compatibility contract, and migration-guide reports.
- Examples through `334` and corresponding mocked/local tests.

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

PyProcore is released under the [MIT license](LICENSE).

## Disclaimer

PyProcore is an independent open-source project. It is not affiliated with,
endorsed by, or supported by Procore Technologies. For official Procore product
support, use Procore's support channels.
