# Roadmap

This roadmap is directional and may change based on user needs and Procore API
coverage priorities.

## Current Stable Areas

- OAuth authorization-code flow
- Token refresh and persistence
- Reusable HTTP client
- Pagination
- Structured logging
- Companies
- Projects
- RFIs
- Submittals
- Documents
- Drawings
- Specifications
- Photos
- Attachment downloads
- Typed models
- Search and resolver helpers
- Automation workflow packages
- AI-ready project context packages
- CLI
- Mocked unit test suite

## Phase 1: SDK Foundation

Status: Completed

- OAuth, token refresh, retries, pagination, and structured logging
- Typed service layers for companies, projects, RFIs, and submittals
- Attachment downloads
- Human-friendly search and resolver helpers
- Object-oriented client interface

## Phase 2: Workflow Automation

Status: Completed

- AI-ready RFI and submittal workflow packages
- CSV and JSONL exports for RFIs and submittals
- Local RFI and submittal folder sync
- Markdown summaries, tracker CSVs, manifests, and attachment downloads
- Dry-run planning and richer sync manifests
- Incremental sync state
- Combined project sync
- Sync summary reports

## Phase 3: Expanded API Coverage

Status: Completed

Phase 3 will focus on expanded endpoint coverage for project resources such as
Documents, Drawings, Specifications, Photos, and Daily Logs.

- Documents: Completed
- Drawings: Completed
  - List/get drawing areas
  - List drawing disciplines
  - List/get/find drawings
  - Download drawings when Procore provides a direct URL
  - Manual smoke test for sandbox endpoint and payload validation
  - Folder sync planned after live download behavior is confirmed
- Specifications: Completed
  - List specification sets
  - List/get/find specification sections
  - List/get specification section revisions
  - Download specification section revisions
  - Manual smoke test for sandbox endpoint and payload validation
- Photos: Completed
  - List/get/find photo albums
  - List/get/find photos
  - Download photos and photo albums
  - Manual smoke test for sandbox endpoint and payload validation
- Daily Logs: Completed
  - Daily Log counts and headers
  - Type-specific read-only log listing
  - Local lookup helpers for headers and log entries
  - Grouped date summary helper
  - CLI, examples, recipes, and manual smoke test
- Observations
- Correspondence

## Phase 4: AI-Ready Project Context

Status: In Progress

- Read-only project context package builder
- Enhanced RFI intelligence package builder
- Enhanced submittal intelligence package builder
- JSON, JSONL, Markdown, and manifest outputs
- Safe defaults with downloads off
- Continue-on-error behavior for partial project permissions
- Lightweight include/exclude controls
- Keyword-matched related context for RFI review
- Keyword-matched related context for submittal review
- AI review-context, reviewer-questions, and possible risk-flag files
- Structured submittal approval review assistance files
- Local-file-only AI review export layer
- Prompt packs, source indexes, deterministic chunks, and review checklists
- CLI and client helpers for reviewing existing package folders without live Procore or AI calls

## Phase 5: Local Automation Runner

Status: In Progress

- JSON workflow plan loading and validation
- Safe placeholder resolution without shell execution
- Dry-run support for repeatable local automation
- Run manifests, summaries, resolved plans, warnings, and errors
- CLI and client helpers for workflow plan list, validate, and run
- Sample plans for project context, RFI review packages, and lightweight syncs
- Scheduled sync examples for cron, launchd, Windows Task Scheduler, GitHub Actions, and local scripts
- Beginner-friendly scheduled automation docs with dry-run-first guidance
- Local webhook helpers for validating, redacting, saving, listing, filtering, and dry-run dispatching webhook payloads
- Webhook CLI commands, examples, and recipes for future webhook-triggered workflows
- Docker, Docker Compose, and CI dry-run templates for repeatable automation environments

## Phase 7: Examples and Recipes

Status: Completed

- Runnable examples
- Task-based recipes
- Beginner-friendly troubleshooting
- AI workflow package examples

## Planned Capabilities

- Async client
- Richer filtering and search
- AI assistant examples outside the core SDK
