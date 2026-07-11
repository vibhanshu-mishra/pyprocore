# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows semantic versioning.

## [Unreleased]

### Added

- Open-source repository support files, including contribution, security, issue, and pull request guidance.
- Phase 7 examples and recipe documentation.
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
