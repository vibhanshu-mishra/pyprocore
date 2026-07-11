# PyProcore

> PyProcore is the open-source automation layer for Procore built for developers, consultants, and construction teams who want typed API access, reliable file downloads, project exports, and AI-ready workflow packages without rebuilding OAuth, pagination, retries, and Procore-specific plumbing.

[![PyPI](https://img.shields.io/pypi/v/pyprocore.svg)](https://pypi.org/project/pyprocore/)
![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)
[![License](https://img.shields.io/pypi/l/pyprocore.svg)](LICENSE)
[![Tests](https://github.com/vibhanshu-mishra/pyprocore/actions/workflows/tests.yml/badge.svg)](https://github.com/vibhanshu-mishra/pyprocore/actions/workflows/tests.yml)
![Coverage](https://img.shields.io/badge/coverage-91%25-brightgreen.svg)

PyProcore handles the parts of a Procore integration that are tedious and easy to get wrong — OAuth, token refresh, pagination, retries, typed responses, structured logging, and attachment downloads - so you work with Python objects instead of raw JSON and API plumbing.

---

## Why PyProcore

Calling the Procore REST API directly means managing the OAuth handshake, refreshing expired tokens, following pagination headers, retrying failed requests, and parsing untyped JSON on every call.

PyProcore does that once, correctly, behind a clean interface. You call a service method and get back a typed Pydantic object. It is designed as the foundation layer for higher-level tools built on Procore data: engineering assistants, document analysis, workflow automation, and AI-powered review.

---

## Features

**Authentication and transport**

- OAuth 2.0 authorization-code flow
- Automatic access-token refresh
- Automatic pagination via Procore response headers
- Request retries and structured logging with secret redaction

**API coverage**

- Companies
- Projects
- RFIs
- Submittals
- Documents
- Drawings
- Specifications
- Photos
- Daily Logs
- Attachment downloads

**Developer experience**

- Typed Pydantic response models
- Command-line interface
- AI-ready project context packages
- Enhanced RFI review packages
- Enhanced submittal review packages
- Mocked unit tests with no live Procore dependency

---

## Architecture

| Package               | Responsibility                                                  |
| --------------------- | --------------------------------------------------------------- |
| `pyprocore/auth/`     | OAuth exchange, token persistence, token refresh                |
| `pyprocore/core/`     | Configuration, endpoint paths, HTTP client, logging, exceptions |
| `pyprocore/models/`   | Pydantic response models                                        |
| `pyprocore/services/` | Company, project, RFI, submittal, document, drawing, specification, photo, Daily Logs, and file services |
| `pyprocore/parser/`   | Email parsing utilities for future automation                   |
| `tests/`              | Mocked unit tests with no live Procore dependency               |

---

## Installation

Requires Python 3.12+.

```bash
pip3 install pyprocore
```

For local development:

```bash
git clone https://github.com/vibhanshu-mishra/pyprocore.git
cd pyprocore
python3 -m venv .venv
python3 -m pip install --upgrade pip
python3 -m pip install -e .
```

When testing unreleased local CLI changes, run commands with `PYTHONPATH=.` so
Python resolves the local checkout before any installed copy:

```bash
PYTHONPATH=. procore-sdk --help
PYTHONPATH=. procore-sdk doctor
PYTHONPATH=. procore-sdk auth status
PYTHONPATH=. python3 -m pyprocore.app --help
```

---

## Quick Example

Function style:

```python
from pyprocore.services import list_projects

projects = list_projects(company_id=123456)

for project in projects:
    print(project.name)
```

Client style:

```python
from pyprocore import Procore

client = Procore()
projects = client.projects.list(company_id=123456)

for project in projects:
    print(project.name)
```

---

## Configuration

Copy the example file and fill in real values:

```bash
cp .env.example .env
```

Required variables:

```bash
PROCORE_CLIENT_ID=your_client_id
PROCORE_CLIENT_SECRET=your_client_secret
PROCORE_REDIRECT_URI=http://localhost:8080/callback
PROCORE_LOGIN_URL=https://login.procore.com
PROCORE_API_BASE=https://api.procore.com
PROCORE_COMPANY_ID=123456
```

PyProcore loads `.env` automatically from your current working directory and
does not override environment variables that are already set.

Secrets, tokens, URLs, and company IDs are never hardcoded in source.

---

## Authentication

Use the auth helper commands to inspect and repair local setup:

```bash
procore-sdk doctor
procore-sdk auth login-url
procore-sdk auth exchange-code YOUR_AUTHORIZATION_CODE
procore-sdk auth status
procore-sdk auth refresh
```

First, run `procore-sdk auth login-url` and open the printed URL. After you
approve access, Procore redirects to your redirect URI with a `code` value. Copy
that value and run `procore-sdk auth exchange-code YOUR_AUTHORIZATION_CODE` to
save tokens locally.

After that, SDK clients read the token automatically:

```python
from pyprocore.auth.token_manager import get_access_token

access_token = get_access_token()
```

Expired access tokens refresh automatically whenever a refresh token is available.
You can also refresh manually with `procore-sdk auth refresh`.

---

## Usage

Once `.env` is configured and the one-time OAuth exchange is complete, calls return typed objects:

```python
from pyprocore.services import list_projects

for project in list_projects(company_id=123456):
    print(project.name)
```

You can also use the object-oriented client interface:

```python
from pyprocore import Procore

client = Procore()

companies = client.companies.list()
projects = client.projects.list(company_id=123456)
rfi = client.rfis.get(project_id=352338, rfi_id=102784)
open_rfis = client.rfis.list(project_id=352338, status="open")
pending_submittals = client.submittals.list(project_id=352338, status="pending")
documents = client.documents.list(project_id=352338)
documents_recursive = client.documents.list(project_id=352338, recursive=True)
document = client.documents.get(project_id=352338, document_id=456)
drawing_areas = client.drawings.list_areas(project_id=352338)
drawings = client.drawings.list(project_id=352338, drawing_area_id=123, current=True)
drawing = client.drawings.get(project_id=352338, drawing_id=789, drawing_area_id=123)
specification_sets = client.specifications.list_sets(project_id=352338)
specification_sections = client.specifications.list_sections(project_id=352338)
specification_section = client.specifications.find_section(
    project_id=352338,
    number="03 3000",
)
photo_albums = client.photos.list_albums(project_id=352338)
photos = client.photos.list(project_id=352338, album_id=123)
photo = client.photos.get(project_id=352338, photo_id=789)
```

Full service surface:

```python
from pyprocore.services import (
    download_rfi_attachments,
    download_submittal_attachments,
    download_document,
    download_drawing,
    get_document,
    get_document_folder,
    get_drawing,
    get_drawing_area,
    get_rfi,
    get_submittal,
    list_companies,
    list_document_folders,
    list_documents,
    list_drawing_areas,
    list_drawing_disciplines,
    list_drawings,
    list_photo_albums,
    list_photos,
    list_projects,
    list_rfis,
    list_specification_section_revisions,
    list_specification_sections,
    list_specification_sets,
    list_submittals,
)

companies = list_companies()
projects = list_projects(company_id=123456)

rfis = list_rfis(project_id=352338)
open_rfis = list_rfis(project_id=352338, status="open")
rfi = get_rfi(project_id=352338, rfi_id=102784)
first_attachment_url = rfi.questions[0].attachments[0].url

submittals = list_submittals(project_id=352338)
pending_submittals = list_submittals(project_id=352338, status="pending")
submittal = get_submittal(project_id=352338, submittal_id=309641)

folders = list_document_folders(project_id=352338)
documents = list_documents(project_id=352338)
folder_documents = list_documents(project_id=352338, folder_id=123)
all_documents = list_documents(project_id=352338, recursive=True)
document = get_document(project_id=352338, document_id=456)
saved_document = download_document(project_id=352338, document_id=456)

drawing_areas = list_drawing_areas(project_id=352338)
drawing_disciplines = list_drawing_disciplines(project_id=352338)
drawings = list_drawings(project_id=352338, current=True)
area_drawings = list_drawings(project_id=352338, drawing_area_id=123)
drawing = get_drawing(project_id=352338, drawing_id=789, drawing_area_id=123)
saved_drawing = download_drawing(project_id=352338, drawing_id=789, drawing_area_id=123)

specification_sets = list_specification_sets(project_id=352338)
specification_sections = list_specification_sections(project_id=352338, sort="number")
specification_revisions = list_specification_section_revisions(
    project_id=352338,
    per_page=1000,
)
photo_albums = list_photo_albums(project_id=352338)
photos = list_photos(project_id=352338, album_id=123)
```

Procore Documents are exposed through Project Folders and Files endpoints. PyProcore
keeps the user-friendly `client.documents` and `list_documents()` names while
internally sending `project_id` as a query parameter to `/rest/v1.0/folders`.
Folder scoping uses `filters[folder_id]`.

Procore Drawings are organized by drawing areas. PyProcore lists project
drawing areas first, then lists drawings from
`/rest/v1.0/drawing_areas/{drawing_area_id}/drawings`. Passing
`drawing_area_id` to `get_drawing()` or `download_drawing()` uses the exact
area-scoped endpoint. If omitted, PyProcore searches the project's drawing
areas for backward compatibility. Drawing downloads require Procore to include a
direct `url` or `download_url` in the drawing payload. Use
`PYTHONPATH=. python3 scripts/smoke_drawings.py --project "$PROCORE_PROJECT_ID"`
to inspect the live sandbox payload before building a drawing download workflow.

Procore Specifications use company/project-scoped V2 endpoints. PyProcore lists
specification sets and sections through verified collection endpoints, resolves
individual sections by matching the list locally, and uses the verified revision
show and download endpoints for revision workflows. Use
`PROCORE_PROJECT_ID=352338 make smoke-specifications` to inspect live payloads
before building a specification download workflow.

Procore Photos are exposed through the Images API. PyProcore uses SDK-facing
photo and album names, while the REST API calls albums `image_categories` and
photos `images`. Project scoping is sent with `project_id` as a query parameter
and `Procore-Company-Id` as a header.

Procore Daily Logs are organized by log type. PyProcore supports read-only
counts, headers, type-specific listing, local lookup by ID/date, and grouped
date summaries:

```python
from pyprocore import Procore, list_manpower_logs

client = Procore()
counts = client.daily_logs.counts(project_id=352338)
headers = client.daily_logs.headers(project_id=352338, log_date="2026-07-10")
manpower = list_manpower_logs(project_id=352338, log_date="2026-07-10")
summary = client.daily_logs.list_for_date(
    project_id=352338,
    log_date="2026-07-10",
    log_types=["manpower", "notes", "delay"],
)
```

Project context packages gather available project data into a local AI-friendly
folder with JSON, JSONL, Markdown summaries, a manifest, and recorded section
errors:

```python
from pyprocore.workflows import build_project_context_package

result = build_project_context_package(
    project_id=352338,
    company_id=4286480,
    output_dir="project-context",
    include=["project", "rfis", "submittals", "daily_logs"],
    max_items=100,
)
print(result.summary_path)
```

RFI and submittal list calls also accept optional date filters:

```python
recent_rfis = list_rfis(project_id=352338, updated_after="2026-07-01")
recent_submittals = client.submittals.list(
    project_id=352338,
    updated_after="2026-07-01",
)
```

Human-friendly resolvers are available when you do not already know Procore IDs:

```python
from pyprocore import (
    find_company,
    find_document,
    find_document_folder,
    find_drawing,
    find_drawings_contains,
    find_specification_section,
    find_project,
    find_rfi,
    find_submittal,
)
from pyprocore.services import find_project_contains

company = find_company("Tracker")
project = find_project("Sandbox Test Project")
project_by_number = find_project(number="001")
hospital_project = find_project_contains("Hospital")

rfi = find_rfi(project_id=352338, number="15")
submittal = find_submittal(project_id=352338, number="27")
folder = find_document_folder(project_id=352338, name="Drawings")
document = find_document(project_id=352338, filename="plan.pdf")
drawing = find_drawing(project_id=352338, number="S-101")
stair_drawings = find_drawings_contains(project_id=352338, text="stair")
spec_section = find_specification_section(project_id=352338, number="03 3000")
```

Resolvers use case-insensitive exact matching first, then partial matching. They raise `NotFoundError`, `DuplicateMatchError`, or `MultipleResultsError` when a lookup cannot produce exactly one typed result.

## Automation Layer

The automation layer builds a single typed package for downstream workflows. It resolves project and item identifiers, fetches full metadata, optionally downloads attachments, and returns one JSON-serializable `WorkflowPackage`.

```python
from pyprocore.automation import AutomationInput, build_workflow_package

package = build_workflow_package(
    AutomationInput(
        project_name="Sandbox Test Project",
        item_type="rfi",
        item_number="15",
    )
)

print(package.title)
print(package.attachments)
```

Convenience builders are available when you already know the workflow type:

```python
from pyprocore.automation import build_rfi_package, build_submittal_package

rfi_package = build_rfi_package(project_id=352338, rfi_id=102784)
submittal_package = build_submittal_package(
    project_name="Sandbox Test Project",
    number="27",
    download_attachments=False,
)
```

Default attachment output directories are created under `downloads/`, for example `downloads/rfi_15/` or `downloads/submittal_27/`. Pass `output_dir` to choose a custom destination.

The object client exposes the same builders:

```python
from pyprocore import Procore

client = Procore()
package = client.automation.build_rfi_package(project_id=352338, number="15")
```

## Workflow Automation

Workflow helpers create local files for reporting, handoff, and AI workflows.
They build on the existing typed services and do not require you to manually
request additional pages.

```python
from pyprocore.workflows import export_rfis_to_csv, sync_rfis_to_folder

csv_path = export_rfis_to_csv(
    project_id=352338,
    output_path="exports/rfis.csv",
    status="open",
)

sync_result = sync_rfis_to_folder(
    project_id=352338,
    output_dir="exports/rfi-sync",
    download_attachments=True,
)

print(csv_path)
print(sync_result.manifest_path)
```

Available helpers:

- `build_enhanced_rfi_package()`
- `build_enhanced_submittal_package()`
- `build_project_context_package()`
- `export_rfis_to_csv()`
- `export_submittals_to_csv()`
- `export_rfis_to_jsonl()`
- `export_submittals_to_jsonl()`
- `sync_rfis_to_folder()`
- `sync_submittals_to_folder()`
- `sync_documents_to_folder()`

The object client exposes these under `client.workflows`.

CSV exports are best when you want a spreadsheet-friendly tracker. JSONL
exports are best when another tool should process one complete typed item per
line. Folder sync creates:

- `rfis/`, `submittals/`, or `documents/` item folders
- `item.json` metadata for each item
- optional `summary.md` files
- a tracker CSV when enabled
- `sync_manifest.json` with project, item, folder, attachment, warning, and error metadata
- optional downloaded attachments

Attachment downloads skip existing files unless `overwrite=True`. Tracker CSV,
manifest, item JSON, and Markdown summary files are regenerated when sync runs.
Use `dry_run=True` or `--dry-run` to list/fetch items and preview paths without
writing files or downloading attachments.

Incremental sync skips unchanged items by comparing each item ID and
`updated_at` value against a local state file:

```python
from pyprocore.workflows import sync_project_to_folder

result = sync_project_to_folder(
    project_id=352338,
    output_dir="exports/project-sync",
    incremental=True,
)

print(result.synced_count)
print(result.skipped_count)
```

Project sync combines RFIs and submittals into one output folder and writes
`project_sync_manifest.json` plus `project_sync_summary.md`.

Document sync downloads project documents and writes `document_tracker.csv`,
`document_sync_manifest.json`, and `document_sync_summary.md`:

```python
from pyprocore.workflows import sync_documents_to_folder

result = sync_documents_to_folder(
    project_id=352338,
    output_dir="exports/documents",
    incremental=True,
    recursive=True,
)
```

Document downloads use `download_url` or `url` fields when Procore includes
them in the file payload. Some Procore environments may require a separate
secure file access step before a direct download URL is available.

Enhanced RFI packages create a read-only, AI-friendly review folder for one RFI.
They can include keyword-matched related submittals, documents, drawings,
specifications, photos, and Daily Logs. Downloads are off by default, related
section failures are recorded by default, and generated risk flags are only
possible review flags:

```python
from pyprocore.workflows import build_enhanced_rfi_package

result = build_enhanced_rfi_package(
    project_id=352338,
    company_id=4286480,
    rfi_number="15",
    output_dir="rfi-package",
    related_sections=["drawings", "specifications", "submittals"],
    max_related_items=10,
    download_files=False,
)

print(result.review_context_path)
```

Enhanced submittal packages follow the same conservative pattern for submittal
review. They include `ai/approval_review.md` for structured human review
assistance and never approve, reject, or revise anything:

```python
from pyprocore.workflows import build_enhanced_submittal_package

result = build_enhanced_submittal_package(
    project_id=352338,
    company_id=4286480,
    submittal_number="27",
    output_dir="enhanced-submittal-package",
    related_sections=["rfis", "drawings", "specifications"],
    max_related_items=10,
    download_files=False,
)

print(result.approval_review_path)
```

AI review exports are local-file-only. They read an existing PyProcore package
folder and write an `ai-export/` folder with prompts, source indexes, chunks,
and checklists for downstream review tools:

```python
from pyprocore.workflows import build_ai_review_export, build_ai_prompt_pack

review_export = build_ai_review_export("rfi-package")
prompt_pack = build_ai_prompt_pack("enhanced-submittal-package", review_type="submittal")

print(review_export.ai_review_path)
print(prompt_pack.prompt_path)
```

Every typed model serializes back to JSON:

```python
json_payload = rfi.model_dump(mode="json")
json_string = rfi.model_dump_json()
```

---

## Downloading Attachments

Attachment URLs live at:

```text
RFI:        questions[].attachments[].url
Submittal:  attachments[].url
```

Download through the service functions:

```python
rfi_files = download_rfi_attachments(project_id=352338, rfi_id=102784)
submittal_files = download_submittal_attachments(
    project_id=352338,
    submittal_id=309641,
)
```

The shared file service supports safe filenames, streaming writes, retries, progress logging, batch downloads, and skip-existing behavior by default:

```python
from pyprocore.services.files import FileDownloadService

files = FileDownloadService().download_attachments(
    attachments,
    "downloads/custom",
    fallback_prefix="attachment",
    overwrite=False,
)
```

---

## CLI

```bash
procore-sdk companies
procore-sdk find-company Tracker
procore-sdk projects
procore-sdk find-project Hospital
procore-sdk find-project --number 001
procore-sdk rfis --project 352338
procore-sdk rfis --project 352338 --status open
procore-sdk rfis --project 352338 --updated-after 2026-07-01
procore-sdk rfi --project 352338 --id 102784
procore-sdk find-rfi --project 352338 --number 15
procore-sdk submittals --project 352338
procore-sdk submittals --project 352338 --status pending
procore-sdk submittals --project 352338 --updated-after 2026-07-01
procore-sdk submittal --project 352338 --id 309641
procore-sdk find-submittal --project 352338 --number 27
procore-sdk document-folders --project 352338
procore-sdk document-folder --project 352338 --id 123
procore-sdk find-document-folder --project 352338 --name Drawings
procore-sdk documents --project 352338
procore-sdk documents --project 352338 --folder 123
procore-sdk documents --project 352338 --recursive
procore-sdk document --project 352338 --id 456
procore-sdk find-document --project 352338 --filename plan.pdf
procore-sdk download-rfi --project 352338 --id 102784
procore-sdk download-submittal --project 352338 --id 309641
procore-sdk download-document --project 352338 --id 456 --output ./documents
procore-sdk drawing-areas --project 352338
procore-sdk drawing-disciplines --project 352338
procore-sdk drawings --project 352338 --current
procore-sdk drawings --project 352338 --area 123 --current
procore-sdk drawing --project 352338 --area 123 --id 789
procore-sdk find-drawing --project 352338 --number S-101
procore-sdk find-drawings --project 352338 --contains stair
procore-sdk download-drawing --project 352338 --area 123 --id 789 --output ./drawings
procore-sdk specification-sets --project 352338
procore-sdk specification-sections --project 352338 --sort number
procore-sdk specification-section --project 352338 --section 123
procore-sdk find-specification-section --project 352338 --number "03 3000"
procore-sdk specification-revisions --project 352338 --section 123 --per-page 1000
procore-sdk specification-revision --project 352338 --revision 456
procore-sdk download-specification-revision --project 352338 --revision 456 --output-dir ./specifications
procore-sdk photo-albums --project 352338
procore-sdk photo-album --project 352338 --album 123
procore-sdk find-photo-album --project 352338 --name Progress
procore-sdk photos --project 352338 --album 123 --sort=-created_at
procore-sdk photo --project 352338 --photo 789
procore-sdk find-photo --project 352338 --filename site.jpg
procore-sdk download-photo --project 352338 --photo 789 --output-dir ./photos
procore-sdk download-photo-album --project 352338 --album 123 --limit 10 --output-dir ./photos
procore-sdk daily-log-counts --project 352338 --log-date 2026-07-10
procore-sdk daily-log-headers --project 352338
procore-sdk daily-log-header --project 352338 --header 123
procore-sdk daily-logs --project 352338 --log-type manpower --log-date 2026-07-10
procore-sdk daily-log --project 352338 --log-type notes --log 456
procore-sdk daily-logs-date --project 352338 --log-date 2026-07-10 --types manpower,notes,delay
procore-sdk manpower-logs --project 352338 --log-date 2026-07-10
procore-sdk delay-log-types --project 352338
procore-sdk package-rfi --project 352338 --id 102784
procore-sdk package-rfi --project-name "Sandbox Test Project" --number 15
procore-sdk package-submittal --project 352338 --id 309641
procore-sdk package-submittal --project-name "Sandbox Test Project" --number 27
procore-sdk export-rfis --project 352338 --output ./rfis.csv
procore-sdk export-submittals --project 352338 --output ./submittals.csv
procore-sdk sync-rfis --project 352338 --output ./rfi-sync
procore-sdk sync-rfis --project 352338 --output ./rfi-sync --dry-run
procore-sdk sync-rfis --project 352338 --output ./rfi-sync --incremental
procore-sdk sync-submittals --project 352338 --output ./submittal-sync
procore-sdk sync-documents --project 352338 --output ./documents
procore-sdk sync-documents --project 352338 --output ./documents --incremental
procore-sdk sync-documents --project 352338 --output ./documents --recursive
procore-sdk sync-project --project 352338 --output ./project-sync
procore-sdk sync-project --project 352338 --output ./project-sync --incremental
procore-sdk project-context --project 352338 --company 4286480 --output ./project-context
procore-sdk project-context --project 352338 --include rfis,submittals,daily_logs --max-items 50
procore-sdk enhanced-rfi-package --project 352338 --company 4286480 --rfi-number 15
procore-sdk enhanced-rfi-package --project 352338 --rfi-id 102784 --related-sections drawings,specifications,submittals
procore-sdk enhanced-submittal-package --project 352338 --company 4286480 --submittal-number 27
procore-sdk enhanced-submittal-package --project 352338 --submittal-id 309641 --related-sections rfis,drawings,specifications
procore-sdk ai-review-export --package-dir ./rfi-package
procore-sdk ai-prompt-pack --package-dir ./submittal-package --review-type submittal
procore-sdk workflow-plan list
procore-sdk workflow-plan validate ./workflow.json
procore-sdk workflow-plan run ./workflow.json --dry-run
procore-sdk workflow-plan run ./workflow.json --output-dir ./runs
procore-sdk auth status
procore-sdk auth login-url
procore-sdk auth refresh
```

Most CLI commands print formatted JSON. Export and sync workflow commands print
short human-readable summaries.

---

## Examples and Recipes

Runnable example scripts live in [examples/](examples/README.md). They show
common SDK tasks such as listing projects, fetching RFIs, downloading
attachments, documents, drawings, specification revisions, photos, and Daily
Logs, building workflow packages, exporting CSVs, syncing local review folders,
building AI-ready project context packages, and creating enhanced RFI review
and submittal review packages. The local AI export examples show how to turn an
existing package folder into prompt, chunk, source-index, and checklist files
without calling Procore or an AI service.

Local workflow plans let you repeat existing PyProcore workflows from JSON files
for scheduled syncs, repeatable exports, and AI review package generation.
Plans do not execute shell commands and do not mutate Procore data. Validate and
dry-run plans before scheduling them:

```bash
procore-sdk workflow-plan list
procore-sdk workflow-plan validate examples/workflow_plans/project_context_and_ai_export.json
procore-sdk workflow-plan run examples/workflow_plans/project_context_and_ai_export.json --dry-run
```

Examples can be syntax-checked without credentials or live Procore access:

```bash
make examples-check
```

Task-based guides live in [docs/recipes/](docs/recipes/). Recipes explain when
to use each pattern, which environment variables are needed, what output to
expect, and how to troubleshoot beginner-friendly issues.

For AI-ready RFI review workflows, start with
[Build Enhanced RFI Package](docs/recipes/build-enhanced-rfi-package.md) or
[RFI AI Review Context](docs/recipes/rfi-ai-review-context.md).

For AI-ready submittal review workflows, start with
[Build Enhanced Submittal Package](docs/recipes/build-enhanced-submittal-package.md)
or [Submittal AI Review Context](docs/recipes/submittal-ai-review-context.md).

For local-file-only AI review exports, start with
[Build an AI Review Export](docs/recipes/build-ai-review-export.md),
[Build an AI Prompt Pack](docs/recipes/build-ai-prompt-pack.md), or
[Review a Procore Package with AI](docs/recipes/review-procore-package-with-ai.md).

For local automation plans, start with
[Validate a Workflow Plan](docs/recipes/validate-workflow-plan.md),
[Run a Workflow Plan](docs/recipes/run-workflow-plan.md), or
[Workflow Plan Examples](docs/recipes/workflow-plan-examples.md).

Before releasing Documents changes against a new Procore environment, run the
manual smoke helper with sandbox credentials:

```bash
PROCORE_PROJECT_ID=352338 make smoke-documents
PYTHONPATH=. python3 scripts/smoke_documents.py --project 352338 --folder 123
```

Before relying on drawing downloads in a new Procore environment, inspect the
live drawing payload:

```bash
PROCORE_PROJECT_ID=352338 make smoke-drawings
PYTHONPATH=. python3 scripts/smoke_drawings.py --project 352338 --area 123 --drawing 789
```

A Drawings 403 usually means authentication succeeded, but Procore rejected the
project/company context. Confirm the project belongs to the company, production
vs sandbox is correct, the OAuth user has project access, the Drawings tool is
enabled, and the user can view Drawings.

Before relying on specification revision downloads in a new Procore environment,
inspect the live specification payload:

```bash
PROCORE_PROJECT_ID=352338 make smoke-specifications
PYTHONPATH=. python3 scripts/smoke_specifications.py --project 352338 --section 123 --revision 456
```

A Specifications 403 usually means authentication succeeded, but Procore
rejected the project/company context. Confirm the project belongs to the
company, the app is connected to that company, production vs sandbox is correct,
the OAuth user has project access, the Specifications tool is enabled, and the
user can view Specifications.

Before relying on photo downloads in a new Procore environment, inspect the live
Photos payload:

```bash
PROCORE_PROJECT_ID=352338 make smoke-photos
PYTHONPATH=. python3 scripts/smoke_photos.py --project 352338 --album 123 --photo 456
```

A Photos 403 usually means authentication succeeded, but Procore rejected the
project/company context. Confirm the app is connected to the company, production
vs sandbox is correct, the Photos tool is enabled, and the user can view Photos.
If a photo download says no URL was found, inspect the `photo` payload to see
which URL fields Procore returned.

Before relying on Daily Logs automation in a new Procore environment, inspect
the live Daily Logs payload:

```bash
PROCORE_PROJECT_ID=352338 make smoke-daily-logs
PYTHONPATH=. python3 scripts/smoke_daily_logs.py --project 352338 --log-date 2026-07-10 --log-type manpower
```

A Daily Logs 403 usually means authentication succeeded, but Procore rejected
the project/company context. Confirm the app is connected to the company,
production vs sandbox is correct, the Daily Log tool is enabled, and the user
can view Daily Logs. Empty responses can simply mean there are no entries for
that date or log type.

---

## Pagination

Collection methods use `ProcoreClient.get_all()`, which follows Procore pagination headers automatically. Business logic should call the service method or `get_all()` directly and never request page 2 by hand.

---

## Logging

Structured logs are written to:

```text
logs/sdk.log
logs/errors.log
```

Request logs record method, endpoint, status, elapsed time, and retry count. Exception logs record stack traces, exception type, request URL, HTTP status, and response body when available. The logger redacts sensitive keys such as authorization headers, access tokens, refresh tokens, and client secrets.

---

## Implemented Endpoints

```text
GET /rest/v1.0/companies
GET /rest/v1.0/companies/{company_id}/projects
GET /rest/v1.1/projects/{project_id}/rfis
GET /rest/v1.1/projects/{project_id}/rfis/{rfi_id}
GET /rest/v1.1/projects/{project_id}/submittals
GET /rest/v1.1/projects/{project_id}/submittals/{submittal_id}
GET /rest/v1.0/folders?project_id={project_id}
GET /rest/v1.0/folders?project_id={project_id}&filters[folder_id]={folder_id}
GET /rest/v1.0/folders/{folder_id}?project_id={project_id}
GET /rest/v1.0/files/{document_id}?project_id={project_id}
GET /rest/v1.0/projects/{project_id}/drawing_areas
GET /rest/v1.0/projects/{project_id}/drawing_areas/{drawing_area_id}
GET /rest/v1.0/projects/{project_id}/drawing_disciplines
GET /rest/v1.0/drawing_areas/{drawing_area_id}/drawings
GET /rest/v1.0/drawing_areas/{drawing_area_id}/drawings/{drawing_id}
GET /rest/v1.0/projects/{project_id}/drawing_revisions
GET /rest/v2.0/companies/{company_id}/projects/{project_id}/specification_sets
GET /rest/v2.1/companies/{company_id}/projects/{project_id}/specification_sections
GET /rest/v2.1/companies/{company_id}/projects/{project_id}/specification_section_revisions
GET /rest/v2.1/companies/{company_id}/projects/{project_id}/specification_section_revisions/{revision_id}
GET /rest/v2.1/companies/{company_id}/projects/{project_id}/specification_section_revisions/{revision_id}/download
GET /rest/v1.0/image_categories?project_id={project_id}
GET /rest/v1.0/image_categories/{image_category_id}?project_id={project_id}
GET /rest/v1.0/images?project_id={project_id}
GET /rest/v1.0/images/{image_id}?project_id={project_id}
```

---

## Roadmap

### Phase 1: SDK Foundation
- OAuth and token refresh
- Reusable HTTP client with retries and pagination
- Companies, projects, RFIs, and submittals
- Typed models and attachment downloads
- Search/resolver helpers
- Object-oriented client interface

### Phase 2: Workflow Automation
- RFI CSV and JSONL export
- Submittal CSV and JSONL export
- RFI folder sync with JSON, Markdown, tracker CSV, manifest, and attachments
- Submittal folder sync with JSON, Markdown, tracker CSV, manifest, and attachments
- Dry-run folder sync planning
- Incremental sync state
- Combined project folder sync
- Sync summary reports
- AI-ready workflow packages
- AI-ready project context packages

### Phase 3: Expanded API Coverage
- Documents: Completed
- Drawings: Completed
  - Drawing areas
  - Drawing disciplines
  - Drawing list/get/find/download helpers
  - Manual smoke-test validation
- Specifications: Completed
  - Specification sets
  - Specification sections
  - Specification section revisions
  - Specification revision downloads
  - Manual smoke-test validation
- Photos: Completed
  - Photo albums/image categories
  - Photo list/get/find helpers
  - Photo and album download helpers
  - Manual smoke-test validation
- Daily Logs: Completed
  - Counts and headers
  - Type-specific read-only log listing
  - Grouped date summaries
  - Manual smoke-test validation
- Project Context Packages: In Progress
  - Read-only AI-friendly project exports
  - JSON, JSONL, Markdown, and manifest outputs
  - Continue-on-error section handling
- Observations
- Correspondence

### Phase 4: AI and Review Workflows
- RFI review packages
- Submittal review packages
- Drawing/spec context packages
- LLM-safe JSON exports
- Vector database examples
- Engineering assistant examples

### Phase 5: Developer Platform
- Client object interface
- Async client
- Webhook helpers
- Rate-limit handling
- Advanced filter models
- Plugin architecture

### Phase 6: Production Tooling
- CLI doctor command
- Sync logs
- Manifest files
- Retry reports
- Scheduled sync examples
- Docker example

---

## Diagnostics

Run:

```bash
procore-sdk doctor
```

This checks local configuration, token storage, Python version, and writable SDK
folders without making live Procore calls.

For an authenticated Procore connectivity check:

```bash
procore-sdk doctor --live
```

---

## Troubleshooting

| Error                       | Likely cause and fix                                                                                           |
| --------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `ConfigurationError`        | `.env` is missing or a required key is absent.                                                                 |
| `AuthenticationError`       | Complete the first OAuth code exchange; confirm `pyprocore/auth/token_store.json` holds a refresh token.       |
| `AuthorizationError`        | The Procore user lacks access to the target company, project, or resource.                                     |
| `ResourceNotFoundError`     | Project, RFI, or submittal ID is wrong for the configured company.                                             |
| Attachments not downloading | Check `logs/errors.log` for HTTP status and response body. Existing files are skipped unless `overwrite=True`. |

---

## Tests

Run unit tests:

```bash
make test
```

Run coverage:

```bash
make coverage
```

---

## Development

Clone the repository and install the package in editable mode:

```bash
git clone https://github.com/vibhanshu-mishra/pyprocore.git
cd pyprocore

python3 -m venv .venv
source .venv/bin/activate

pip install -e ".[dev]"
```

If you're working in a restricted environment where build isolation cannot access PyPI, install with:

```bash
pip install --no-build-isolation -e ".[dev]"
```

When testing unreleased local CLI changes, run commands with `PYTHONPATH=.` so
Python resolves the local checkout before any installed copy:

```bash
PYTHONPATH=. procore-sdk --help
PYTHONPATH=. procore-sdk doctor
PYTHONPATH=. procore-sdk auth status
PYTHONPATH=. python3 -m pyprocore.app --help
```

Useful development commands:

```bash
make lint
make typecheck
make test
make coverage
```

---

## Project Resources

- [Changelog](CHANGELOG.md)
- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Architecture notes](docs/architecture.md)
- [Roadmap](docs/roadmap.md)
- [Examples](examples/README.md)
- [Recipes](docs/recipes/)

---

## Supported Environments

- Procore Production
- Procore Sandbox

---

## Contributing

Contributions, issues, and feature requests are welcome. Please open an issue before submitting large changes.

---

## License

Released under the MIT License. See [LICENSE](LICENSE) for details.

---

> **Disclaimer** : PyProcore is an independent open-source project and is not affiliated with or endorsed by Procore Technologies.
