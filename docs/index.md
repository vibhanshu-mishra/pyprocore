# PyProcore Documentation

PyProcore is an open-source Python SDK and local automation framework for the
Procore REST API. It helps developers, consultants, and construction teams work
with Procore data without rebuilding OAuth, pagination, retries, typed models,
downloads, and workflow exports from scratch.

PyProcore focuses on safe, read-oriented automation. It is designed for listing,
retrieving, downloading, exporting, packaging, and reviewing project information
locally. The current workflow examples do not mutate Procore data.

Current published stable release: `2.1.0`.

Prepared next release: `2.2.0`, which includes the completed Phase 7
agent-layer infrastructure. `2.2.0` has not been published to PyPI yet.

## What PyProcore Can Do

- Authenticate with Procore using OAuth.
- Refresh tokens automatically.
- List companies and projects.
- Read RFIs, submittals, documents, drawings, specifications, photos, and Daily Logs.
- Download attachments and supported files.
- Return typed Pydantic models.
- Build local project context packages for review workflows.
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
- [Agent API](agent-api.md)
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
