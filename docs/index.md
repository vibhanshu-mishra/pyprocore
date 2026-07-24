# PyProcore Documentation

PyProcore is an open-source Python SDK and local automation framework for the
Procore REST API. It helps developers, consultants, and construction teams work
with Procore data without rebuilding OAuth, pagination, retries, typed models,
downloads, and workflow exports from scratch.

PyProcore focuses on safe, read-oriented automation. It is designed for listing,
retrieving, downloading, exporting, packaging, and reviewing project information
locally. The current workflow examples do not mutate Procore data.

Current stable release: `2.3.0`.

PyProcore `2.3.0` includes the completed Phase 7 Agent Layer plus expanded read
coverage, enterprise hardening, async helpers, plugin metadata/hooks, AI
workflow examples, deterministic evals, and discovery-only MCP compatibility
tooling. Tool execution remains disabled.

The current repository also documents completed post-`v2.3.0` unreleased
additions: local OAS catalog reports, discovery router metadata, integration
blueprints, local project health analytics recipes, and an optional copied
FastAPI starter template. These additions remain local metadata, report, or
template helpers and do not enable Procore writes or execution.

## What PyProcore Can Do

- Authenticate with Procore using OAuth.
- Refresh tokens automatically.
- List companies and projects.
- Read RFIs, submittals, documents, drawings, specifications, photos, and Daily Logs.
- Download attachments and supported files.
- Return typed Pydantic models.
- Build local project context packages for review workflows.
- Prepare model-agnostic local AI workflow prompts, checklists, and vector manifests.
- Use the async client foundation for read-oriented workflows.
- Inspect metadata-only plugin manifests for future extension packs.
- Run deterministic local analytics recipes for exported project-health review
  signals.
- Export CSV, JSONL, Markdown, and manifest files.
- Run repeatable workflow plans from local JSON files.
- Inspect a local agent tool registry, local HTTP discovery API, OpenAPI export, JSON Schema export, MCP-style discovery metadata, opt-in run logs, and deterministic agent evals for future assistant integrations.
- Validate examples, release metadata, and automation templates without live Procore access.

## Quick Links

- [Getting Started](getting-started.md)
- [Authentication](authentication.md)
- [CLI Usage](cli.md)
- [API Coverage](api-coverage.md)
- [Workflows](workflows.md)
- [AI Review](ai-review.md)
- [AI Workflows](ai-workflows.md)
- [Async Client](async-client.md), including Phase 10A async reads,
  Phase 10B async export/download patterns, and Phase 10C async batch helpers
- [Agent API](agent-api.md)
- [MCP Discovery](mcp.md)
- [Plugin Architecture](plugins.md)
  includes metadata-only manifests, local hooks, JSON configs, extension packs,
  and local plugin developer scaffolding.
- [Local Project Health Analytics](analytics-recipes.md)
- [FastAPI Read API Starter](fastapi-starter.md), an optional copied template.
  FastAPI is not a PyProcore dependency.
- [Golden Evals](evals.md), including Phase 13A local deterministic
  datasets, Phase 13B workflow-specific eval suites, Phase 13C local
  baselines/regression tracking, and Phase 13D offline model-response fixture
  evals.
- Safe local plugin hooks are documented in the plugin architecture guide.
- Plugin configuration and local extension-pack metadata are documented in the
  plugin architecture guide.
- [Project Status](project-status.md)
- [Security](security.md)
- [Automation](automation.md)
- [Recipes](recipes/index.md)
- [Contributing](contributing.md)
- [Release Guide](release.md)
- [Project Status](project-status.md)

## Important Notice

PyProcore is an independent open-source project. It is not affiliated with,
endorsed by, or supported by Procore Technologies. For official Procore product
support, use Procore's support channels.

Never commit `.env` files, OAuth tokens, token stores, Authorization headers, or
private project data.

The source repository is available on
[GitHub](https://github.com/vibhanshu-mishra/pyprocore). The repository README
remains the best single-page overview for installation, quick examples, and
project status.
