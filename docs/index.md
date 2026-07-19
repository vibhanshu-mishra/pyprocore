# PyProcore Documentation

PyProcore is an open-source Python SDK and local automation framework for the
Procore REST API. It helps developers, consultants, and construction teams work
with Procore data without rebuilding OAuth, pagination, retries, typed models,
downloads, and workflow exports from scratch.

PyProcore focuses on safe, read-oriented automation. It is designed for listing,
retrieving, downloading, exporting, packaging, and reviewing project information
locally. The current workflow examples do not mutate Procore data.

Current stable release: `2.2.0`.

PyProcore `2.2.0` includes the completed Phase 7 Agent Layer: local discovery,
schema, replay, MCP discovery, and deterministic eval infrastructure for future
assistant integrations. Tool execution remains disabled.

## What PyProcore Can Do

- Authenticate with Procore using OAuth.
- Refresh tokens automatically.
- List companies and projects.
- Read RFIs, submittals, documents, drawings, specifications, photos, and Daily Logs.
- Download attachments and supported files.
- Return typed Pydantic models.
- Build local project context packages for review workflows.
- Prepare model-agnostic local AI workflow prompts, checklists, and vector manifests.
- Use the unreleased async client foundation for read-oriented workflows.
- Inspect unreleased metadata-only plugin manifests for future extension packs.
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
- [Async Client](async-client.md), including unreleased Phase 10A async reads,
  Phase 10B async export/download patterns, and Phase 10C async batch helpers
- [Agent API](agent-api.md)
- [Plugin Architecture](plugins.md)
  includes metadata-only manifests, local hooks, JSON configs, extension packs,
  and unreleased local plugin developer scaffolding.
- [Golden Evals](evals.md), including unreleased Phase 13A local deterministic
  datasets, Phase 13B workflow-specific eval suites, and Phase 13C local
  baselines/regression tracking.
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
