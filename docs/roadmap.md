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

Status: In Progress

Phase 3 will focus on expanded endpoint coverage for project resources such as
Documents, Drawings, Specifications, Photos, and Daily Logs.

- Documents: In Progress
- Drawings: In Progress
  - List/get drawing areas
  - List drawing disciplines
  - List/get/find drawings
  - Download drawings when Procore provides a direct URL
  - Manual smoke test for sandbox endpoint and payload validation
  - Folder sync planned after live download behavior is confirmed
- Specifications: In Progress
  - List specification sets
  - List/get/find specification sections
  - List/get specification section revisions
  - Download specification section revisions
  - Manual smoke test for sandbox endpoint and payload validation
- Photos: In Progress
  - List/get/find photo albums
  - List/get/find photos
  - Download photos and photo albums
  - Manual smoke test for sandbox endpoint and payload validation
- Daily Logs
- Observations
- Correspondence

## Phase 7: Examples and Recipes

Status: Completed

- Runnable examples
- Task-based recipes
- Beginner-friendly troubleshooting
- AI workflow package examples

## Planned Capabilities

- Async client
- Richer filtering and search
- Webhook helpers
- AI assistant examples outside the core SDK
