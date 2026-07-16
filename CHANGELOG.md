# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows semantic versioning.

## [Unreleased]

### Added

- Phase 9A enterprise auth hardening: explicit auth strategy normalization, safe local 401/403, app-connection, and environment-mismatch explanations, plus examples 111–114.
- Mode-aware diagnostics for token-store state, token renewal, Data Connection App/service-account permissions, and user permissions.
- Phase 9B local scheduled export planning for enterprise Data Connection App deployment patterns.
- `ScheduledExportPlan` models, validation reports, dry-run manifests, safe sample configs, CLI commands, helper scripts, examples, and deployment docs.
- `procore-sdk scheduled-export sample-config`, `procore-sdk scheduled-export validate`, and `procore-sdk scheduled-export dry-run`.

- Phase 8A read-only API coverage for Observations, Punch Items, and Generic Tool correspondence items.
- Typed flexible models for `Observation`, `PunchItem`, `GenericTool`, and `Correspondence`.
- Service, search, object-client, CLI, CSV/JSONL export, and agent registry metadata support for Phase 8A resources.
- Beginner-friendly Phase 8A examples and documentation.
- Phase 8B client credentials authentication support for Procore Data Connection Apps.
- `PROCORE_AUTH_MODE=authorization_code|client_credentials` configuration, defaulting to the existing authorization-code flow.
- `procore-sdk auth client-credentials-token` for requesting and saving a client credentials access token.
- Auth diagnostics, doctor checks, examples, and docs for client credentials setups without requiring a redirect URI or refresh token.
- Phase 8C read-only API coverage for Meetings, checklist-backed Inspections, and Incidents.
- Typed flexible models for `Meeting`, `Inspection`, `InspectionItem`, `Incident`, and `IncidentConfiguration`.
- Service, search, object-client, CLI, CSV/JSONL export, and agent registry metadata support for Phase 8C resources.
- Beginner-friendly Phase 8C examples and documentation.
- Phase 8D read-only API coverage for company/project users, Vendors, Departments, Distribution Groups, and Locations.
- Typed flexible models for `CompanyUser`, `ProjectUser`, `Vendor`, `Department`, `DistributionGroup`, and `Location`.
- Service, search, object-client, CLI, CSV/JSONL export, and agent registry metadata support for Phase 8D resources.
- Beginner-friendly Phase 8D examples and documentation.
- Phase 8E read-only API coverage for financial and change-management resources, including Change Events, Prime Change Orders, Commitment Change Orders, Change Order Packages, Direct Costs, Budget Views/Details, Cost Codes, WBS Codes, and Commitments.
- Typed flexible models for Phase 8E financial and change-management resources.
- Service, search, object-client, CLI, CSV/JSONL export, and agent registry metadata support for Phase 8E resources.
- Beginner-friendly Phase 8E examples and documentation.
- Phase 8F read-only API coverage for contracts, invoices, payments, and billing resources, including Prime Contracts, Commitment Contracts, Purchase Order Contracts, Work Order Contracts, Owner Invoices, Subcontractor Invoices, Contract Payments, Billing Periods, Cost Types, and Tax Codes.
- Typed flexible models for Phase 8F contract, invoice, payment, and billing resources.
- Service, search, object-client, CLI, CSV/JSONL export, and agent registry metadata support for Phase 8F resources.
- Beginner-friendly Phase 8F examples and documentation.
- Phase 8G read-only API coverage for project-management extras, including Schedule metadata/settings/type/integration/import status, Schedule Resource Assignments, Tasks, Task Requested Changes, Calendar Items, Coordination Issues, Forms, Form Templates, Action Plans, and Action Plan Change History Events.
- Typed flexible models for Phase 8G schedule, task, calendar, coordination issue, form, and action plan resources.
- Service, search, object-client, CLI, CSV/JSONL export, and agent registry metadata support for Phase 8G resources.
- Beginner-friendly Phase 8G examples and documentation.

### Security

- Phase 9A redacts credential-like OAuth error fields and prevents malformed token-store validation details from echoing stored token values.
- Phase 9A makes no live Procore or external model calls, does not enable agent execution, and leaves MCP discovery-only.
- Phase 9B scheduled export validation and dry-runs are local-only, do not require credentials, do not call Procore, do not run exports, and do not print secrets.

- Phase 8A remains read-only and does not add create/update/delete Procore actions.
- Agent tool execution remains disabled; new Phase 8A agent entries are metadata only.
- Phase 8B does not enable Procore tool execution or add write APIs.
- Phase 8C remains read-only and does not add create/update/delete Procore actions.
- New Phase 8C agent entries are metadata only.
- Phase 8D remains read-only and does not add create/update/delete Procore actions.
- New Phase 8D agent entries are metadata only.
- Phase 8E remains read-oriented and does not add financial writes, approvals, status changes, budget modifications, commitments writes, invoices, or payment mutations.
- New Phase 8E agent entries are metadata only; Procore tool execution remains disabled and MCP remains discovery-only.
- Phase 8F remains read-oriented and does not add contract, invoice, payment, approval, submission, status-change, PDF-generation, SOV, or line-item mutations.
- New Phase 8F agent entries are metadata only; Procore tool execution remains disabled and MCP remains discovery-only.
- Phase 8G remains read-oriented and does not add schedule uploads/import creation, task writes, requested-change mutations, coordination issue mutations, form submissions, action plan completions, approvals, status changes, or project-management mutations.
- New Phase 8G agent entries are metadata only; Procore tool execution remains disabled and MCP remains discovery-only.

## [2.2.0] - 2026-07-12

PyProcore 2.2.0 is a released, additive update that includes the completed
Phase 7 Agent Layer. It has been published to PyPI, tagged as `v2.2.0`, and
released on GitHub.

### Added

- Phase 7A agent tool registry with metadata-only tool definitions, manifest export helpers, CLI inspection commands, examples, and docs for future assistant integrations.
- Phase 7B local agent API server for HTTP discovery of the agent manifest and tools, with tool execution explicitly disabled.
- Phase 7C OpenAPI and JSON Schema exports for the local Agent API, including CLI export commands, server discovery endpoints, examples, docs, and a local export script.
- Phase 7D opt-in local Agent API run logs and replay helpers for audit trails, future evals, regression checks, and safety reviews without tool execution.
- Phase 7E discovery-only MCP adapter with MCP-style tool, resource, prompt, manifest, CLI, stdio, examples, docs, and export script support while keeping tool execution disabled.
- Phase 7F local deterministic agent eval harness with registry safety, schema quality, OpenAPI completeness, MCP discovery, run replay, redaction, and disabled-execution suites.
- `procore-sdk agent evals` CLI commands, `scripts/run_agent_evals.py`, examples, recipes, and JSON/Markdown eval result exports without live Procore or AI calls.

### Security

- Agent metadata, schema, MCP discovery, replay, and eval commands avoid live Procore calls unless a separate live SDK workflow is run.
- External AI/model APIs are not called by the Phase 7 agent layer.
- Tool execution remains disabled for the local Agent API and discovery-only MCP adapter.

## [2.1.0] - 2026-07-11

PyProcore 2.1.0 is an additive, backward-compatible release. It expands API
coverage, adds AI-ready local workflow packages, strengthens automation
foundations, improves documentation and security posture, and adds local
release-candidate validation tooling.

### Added

- Phase 3 expanded API coverage across Documents, Drawings, Specifications, Photos, and Daily Logs.
- Phase 4 AI-ready project intelligence workflows for project context, enhanced RFI packages, enhanced submittal packages, and local AI review exports.
- Phase 5 automation foundation for workflow plans, scheduled sync examples, webhook helpers, Docker templates, and CI dry-run examples.
- Phase 6 release readiness metadata, package manifest, release docs, and local release checks.
- Phase 6B GitHub project polish with contributor, support, security, issue template, pull request template, Dependabot, and label guidance.
- Phase 6C MkDocs documentation site structure with docs navigation, homepage, getting started, authentication, CLI, API coverage, workflows, AI review, automation, recipes, contributing, release, and changelog pages.
- Phase 6D security and quality hardening with local secret scanning, stronger log redaction, token-store safety tests, pre-commit configuration, CI quality checks, and security documentation.
- Phase 6E final release polish and readiness audit across README, docs, examples, changelog, CLI discoverability, and release-readiness reporting.
- Release-candidate validation tooling for local source distribution, wheel, metadata, clean-install, CLI, and package-export checks.
- Open-source repository support files, including contribution, security, issue, and pull request guidance.
- Expanded examples and recipe documentation.
- Runnable `examples/` scripts for common company, project, RFI, submittal, attachment, and workflow package tasks.
- `docs/recipes/` task-based guides.
- `scripts/check_examples.py` and `make examples-check` for validating example syntax and main guards without live Procore access.
- CI validation for example syntax and main-guard checks.
- `procore-sdk doctor` diagnostics command with human-readable and JSON output.
- Optional `procore-sdk doctor --live` authenticated connectivity check.
- Auth helper commands: `procore-sdk auth status`, `procore-sdk auth status --json`, `procore-sdk auth login-url`, and `procore-sdk auth refresh`.
- Global `Procore` client interface with grouped service clients for companies, projects, RFIs, and submittals.
- Client-interface example and documentation.
- Optional filter/query parameters for RFI and submittal list operations.
- Optional CLI filter flags for RFI and submittal listing.
- `procore-sdk auth exchange-code` to exchange a Procore OAuth authorization code and save tokens locally.
- `client.automation` object-client wrapper for existing workflow package builders.
- `client.workflows` object-client wrapper for export and sync workflows.
- CSV and JSONL workflow exports for RFIs and submittals.
- Folder sync workflows for RFIs and submittals with item JSON, Markdown summaries, tracker CSVs, manifests, and optional attachment downloads.
- `procore-sdk export-rfis`, `procore-sdk export-submittals`, `procore-sdk sync-rfis`, and `procore-sdk sync-submittals`.
- Workflow automation examples and recipes for CSV exports and folder sync.
- Dry-run support for RFI and submittal folder sync workflows.
- Richer sync results and manifests with per-item status, JSON path, summary path, attachment counts, warnings, and errors.
- Incremental sync state for RFI and submittal folder sync.
- Combined project sync workflow and `procore-sdk sync-project`.
- Sync summary reports for individual syncs and project syncs.
- Examples and recipes for incremental sync and project sync.
- Documents API models and services.
- Document folder and document list/get/download helpers.
- Document resolver helpers for finding documents and document folders by name.
- `client.documents` object-client wrapper.
- Document CLI commands for folder listing, document listing, document retrieval, document lookup, and document download.
- Document sync workflow and `procore-sdk sync-documents`.
- Document examples and recipes.
- Manual Documents smoke-test helper for validating sandbox folder/file payloads.
- Beginner-friendly Documents smoke-test setup errors and local import diagnostics.
- Drawings API models and services.
- Drawing area, drawing discipline, drawing list/get/find/download helpers.
- `client.drawings` object-client wrapper.
- Drawing CLI commands for areas, disciplines, drawing listing, drawing retrieval, drawing lookup, and drawing download.
- Drawing examples and recipes.
- Manual Drawings smoke-test helper for validating sandbox endpoint and payload behavior.
- Specifications API models and services.
- Specification set, section, section lookup, revision, and revision download helpers.
- `client.specifications` object-client wrapper.
- Specification CLI commands for sets, sections, section lookup, revisions, and revision downloads.
- Specification examples and recipes.
- Manual Specifications smoke-test helper for validating sandbox endpoint and payload behavior.
- Photos API models and services.
- Photo album, photo list/get/find, photo download, and photo album download helpers.
- `client.photos` object-client wrapper.
- Photo CLI commands for albums, photos, photo lookup, and downloads.
- Photo examples and recipes.
- Manual Photos smoke-test helper for validating sandbox endpoint and payload behavior.
- Daily Logs API models and services.
- Daily Log counts, headers, type-specific list helpers, local lookup helpers, and grouped date summary helpers.
- `client.daily_logs` object-client wrapper.
- Daily Logs CLI commands for counts, headers, type-specific logs, grouped date summaries, and delay log types.
- Daily Logs examples and recipes.
- Manual Daily Logs smoke-test helper for validating sandbox endpoint and payload behavior.
- AI-ready project context package workflow.
- `client.workflows.build_project_context_package`.
- `procore-sdk project-context` CLI command.
- Project context examples and recipes.
- Enhanced RFI intelligence package workflow with AI-ready review files.
- `client.workflows.build_enhanced_rfi_package`.
- `procore-sdk enhanced-rfi-package` CLI command.
- Enhanced RFI package examples and recipes.
- Keyword-matched related RFI context across submittals, documents, drawings, specifications, photos, and Daily Logs.
- Enhanced submittal intelligence package workflow with AI-ready review and approval assistance files.
- `client.workflows.build_enhanced_submittal_package`.
- `procore-sdk enhanced-submittal-package` CLI command.
- Enhanced submittal package examples and recipes.
- Keyword-matched related submittal context across RFIs, documents, drawings, specifications, photos, and Daily Logs.
- Local-file-only AI review export workflow with manifest, source index, prompt, system context, chunks, and checklists.
- `client.workflows.build_ai_review_export` and `client.workflows.build_ai_prompt_pack`.
- `procore-sdk ai-review-export` and `procore-sdk ai-prompt-pack` CLI commands.
- AI review export examples and recipes for reviewing existing package folders without live Procore or AI calls.
- Local automation runner for JSON workflow plans with validation, placeholder resolution, dry-run support, run manifests, summaries, warnings, and errors.
- `client.workflows.load_workflow_plan`, `client.workflows.validate_workflow_plan`, `client.workflows.run_workflow_plan`, and `client.workflows.list_available_workflows`.
- `procore-sdk workflow-plan list`, `procore-sdk workflow-plan validate`, and `procore-sdk workflow-plan run`.
- Workflow plan examples and recipes for repeatable project context, RFI review package, and lightweight sync workflows.
- Scheduled workflow plan examples for nightly project context, weekly AI export, RFI/submittal sync, and Daily Logs-focused exports.
- Local scheduled runner templates for shell, macOS `.command`, PowerShell, macOS launchd, and GitHub Actions.
- Automation docs for cron, launchd, Windows Task Scheduler, GitHub Actions, and local scheduled workflow plans.
- Local webhook helpers for parsing, normalizing, redacting, saving, listing, filtering, and dry-run dispatching webhook payloads.
- `procore-sdk webhook validate`, `procore-sdk webhook save`, `procore-sdk webhook list`, and `procore-sdk webhook dispatch`.
- Webhook sample payloads, local-only examples, automation docs, and recipes.
- Dockerfile, `.dockerignore`, Docker Compose template, Docker helper scripts, and Docker CI workflow example.
- Automation docs for Docker and CI usage with dry-run-first guidance.
- `scripts/check_release_ready.py` and `make release-check` for local package/release readiness checks.

### Changed

- Standardized the Makefile Python command default to `python3` while preserving `PYTHON=...` override support.
- Updated README and troubleshooting docs for examples, recipes, diagnostics, and auth helper workflows.
- Updated client interface, examples, and docs for filtered list workflows.
- Updated auth documentation to show the full CLI-based setup flow.
- Updated README, roadmap, examples, and recipes for workflow automation commands.
- Improved CLI summaries for workflow export and sync commands.
- Marked Phase 2 workflow automation complete in the roadmap.
- Marked Phase 3 expanded API coverage in progress in the roadmap.
- Corrected Documents implementation to align with Procore Project Folders and Files endpoint structure.
- Updated Documents docs to explain folder/file endpoint behavior and direct download URL requirements.
- Updated Documents smoke-test docs to recommend `PYTHONPATH=.` for local checkout validation.
- Updated README, roadmap, examples, and recipes for Specifications support.
- Updated README, roadmap, examples, and recipes for Photos support.
- Updated README, roadmap, examples, and recipes for Daily Logs support.
- Updated README, roadmap, examples, and recipes for project context package support.
- Updated README, roadmap, examples, and recipes for enhanced RFI package support.
- Updated README, roadmap, examples, and recipes for enhanced submittal package support.
- Updated README, roadmap, examples, and recipes for local AI review export workflows.
- Updated README, roadmap, examples, and recipes for local workflow plan automation.
- Updated README, roadmap, examples, and recipes for scheduled workflow plan automation.
- Updated README, roadmap, examples, and recipes for local webhook helper workflows.
- Updated README, roadmap, examples, and automation docs for Docker and CI templates.
- Improved package metadata, source distribution manifest, and typed package marker.

### Fixed

- No runtime fixes in this release.

### Security

- Hardened local release workflows with secret scanning, safer log redaction, token-store safety documentation, and no-secrets contributor guidance.

### Docs

- Added release process documentation with versioning, validation, PyPI checklist, and changelog guidance.
- Added GitHub/community documentation for contributing, support, security reporting, code of conduct, issue forms, pull requests, Dependabot, and labels.
- Added MkDocs documentation-site configuration, local docs preview/build targets, and beginner-friendly docs indexes.
- Added security hardening documentation for OAuth credentials, `.env`, token stores, logs, secret checks, pre-commit, CI, and vulnerability reporting.
- Added public project status and release documentation covering capabilities, validation commands, known limitations, live verification guidance, and publishing status.
- Added release-candidate validation documentation for local artifact builds, metadata checks, clean wheel installs, and manual publishing safeguards.
- Polished README release-facing metadata, safety notes, and package-readiness links.

### Tests

- Added release readiness tests for metadata, docs, Makefile targets, and secret-exclusion hygiene.
- Added GitHub project file tests for community docs, templates, Dependabot, README links, and no-secrets guidance.
- Added docs-site structure tests for MkDocs config, key docs pages, README links, optional docs dependency, and Makefile docs targets.
- Added security hardening tests for secret scanning, logging redaction, token-store-safe CLI diagnostics, pre-commit config, CI quality checks, Makefile targets, and security docs.
- Added final release polish tests for README feature coverage, changelog phase summaries, docs presence, examples coverage, and release-readiness claims.
- Added release-candidate tests for package-check tooling, Makefile targets, documentation, ignored artifacts, and no-publish/no-live-call safeguards.

## [2.0.0] - 2026-07-03

### Added

- Search and resolver layer for human-friendly project, company, RFI, and submittal lookup.
- Automation layer for packaging resolved Procore items for downstream workflows.
- `WorkflowPackage` model for metadata, raw payloads, and downloaded attachment references.
- `package-rfi` and `package-submittal` CLI commands.
- `find-company`, `find-project`, `find-rfi`, and `find-submittal` CLI commands.
- Expanded test suite to 114 tests with 96% coverage.

## [1.0.2] - 2026-07-03

### Changed

- Cleaned up PyPI metadata and license information.

## [1.0.1] - 2026-07-03

### Changed

- Restructured the project into a proper `pyprocore` package.
- Added `import pyprocore` support.
- Added `__version__` support.
- Added the installed `procore-sdk` CLI entry point.

## [1.0.0] - 2026-07-03

### Added

- Initial public release.
- OAuth authorization-code flow.
- Automatic token refresh.
- Company, project, RFI, and submittal services.
- Attachment download support.
- Typed Pydantic models.
- Command-line interface.
- Structured logging.
- Mocked unit tests.
