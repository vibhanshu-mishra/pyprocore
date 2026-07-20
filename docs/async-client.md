# Async Client

Phase 10A adds an async client foundation in the current stable release.
Phase 10B builds on that foundation with async export helpers, local download
patterns, manifests, and simple concurrency controls. Phase 10C adds async
multi-project batch planning, collection, and export helpers. Phase 10D expands
async read coverage across field, operations, correspondence, and directory
resources. Phase 10E expands async read coverage to financial, contract,
billing, and project-management resources. The published stable release is
`2.3.0`; Phase 10A through Phase 10E are included in this release.

Phase 11A plugin manifests may describe future async extension categories, but
they are metadata-only and do not execute async plugin code. See
[Plugin Architecture](plugins.md).

## What this does

`AsyncProcore` is an additive, read-oriented client for scalable workflows such
as multi-project reporting, large-company exports, and concurrent read patterns.
It does not replace the existing sync `Procore` client.

Initial async coverage includes:

- Companies
- Projects
- RFIs
- Submittals
- Documents
- Drawing areas and drawings
- Specification sections
- Photo albums and photos
- Daily Logs
- Observations and punch items
- Generic Tools and correspondence items
- Meetings, inspections, incidents, and incident configuration
- Company/project users, vendors, departments, distribution groups, and locations
- Financial and change-management records such as change events, change orders,
  direct costs, budget views/details, cost codes, WBS codes, and commitments
- Contract and billing records such as prime contracts, owner invoices,
  subcontractor invoices, contract payments, billing periods, cost types, and
  tax codes
- Project-management records such as schedule metadata, tasks, calendar items,
  coordination issues, forms, form templates, and action plans

No create, update, delete, upload, approval, status-change, or mutation helpers
are added in Phase 10A through Phase 10E.

## Optional async transport

The base PyProcore install does not require an async HTTP dependency. Local
tests and examples use `MockAsyncTransport`, which never calls Procore.

For real async HTTP calls, install the optional async extra:

```bash
python3 -m pip install "pyprocore[async]"
```

If `httpx` is not installed and a real async HTTP transport is requested,
PyProcore raises a clear configuration error explaining how to install the
optional extra.

## Local mock example

```python
import asyncio

from pyprocore import AsyncProcore, AsyncResponse, MockAsyncTransport


class DemoTokenManager:
    def get_access_token(self, force_refresh: bool = False) -> str:
        return "PLACEHOLDER_ACCESS_TOKEN"


async def main() -> None:
    transport = MockAsyncTransport(
        [
            AsyncResponse(
                status_code=200,
                url="https://api.example.com/rest/v1.0/companies",
                headers={"Content-Type": "application/json"},
                json_data=[{"id": 123, "name": "Placeholder Company"}],
                content=b"[]",
            )
        ]
    )
    async with AsyncProcore(
        token_manager=DemoTokenManager(),
        transport=transport,
        retry_sleep_seconds=0,
    ) as client:
        companies = await client.list_companies()
        print(companies[0].name)


asyncio.run(main())
```

## Real usage shape

After OAuth is configured and the optional async extra is installed, the same
client can use the real async HTTP transport:

```python
import asyncio

from pyprocore import AsyncProcore


async def main() -> None:
    async with AsyncProcore() as client:
        projects = await client.projects.list(company_id=123456)
        for project in projects:
            print(project.id, project.name)


asyncio.run(main())
```

## Async Exports

Phase 10B adds local CSV and JSONL export helpers for the async client:

- `async_export_records_csv`
- `async_export_records_jsonl`
- `async_export_companies`
- `async_export_projects`
- `async_export_rfis`
- `async_export_submittals`
- `async_export_documents`
- `async_export_drawings`
- `async_export_specification_sections`
- `async_export_photo_albums`
- `async_export_photos`
- `async_export_daily_logs`
- `async_export_observations`
- `async_export_punch_items`
- `async_export_generic_tools`
- `async_export_correspondences`
- `async_export_meetings`
- `async_export_inspections`
- `async_export_incidents`
- `async_export_company_users`
- `async_export_project_users`
- `async_export_vendors`
- `async_export_departments`
- `async_export_distribution_groups`
- `async_export_locations`
- `async_export_change_events`
- `async_export_prime_change_orders`
- `async_export_commitment_change_orders`
- `async_export_change_order_packages`
- `async_export_direct_costs`
- `async_export_budget_views`
- `async_export_budget_details`
- `async_export_cost_codes`
- `async_export_commitments`
- `async_export_contracts`
- `async_export_owner_invoices`
- `async_export_subcontractor_invoices`
- `async_export_contract_payments`
- `async_export_billing_periods`
- `async_export_project_schedule`
- `async_export_tasks`
- `async_export_calendar_items`
- `async_export_coordination_issues`
- `async_export_forms`
- `async_export_action_plans`

Each helper writes to a local path, creates parent directories, and returns an
`AsyncExportResult` with the resource name, output path, record count, format,
warnings, errors, and dry-run status.

```python
import asyncio
from pathlib import Path

from pyprocore import AsyncProcore, async_export_projects


async def main() -> None:
    async with AsyncProcore() as client:
        result = await async_export_projects(
            client,
            company_id=123456,
            output_path=Path("exports/projects.jsonl"),
        )
        print(result.record_count)


asyncio.run(main())
```

The examples use mock transports so they do not call Procore. Real exports
require valid Procore credentials and access to the requested company/project.

## Async File And Download Patterns

Phase 10B also adds local download patterns:

- `async_download_file_from_url`
- `async_download_with_manifest`
- `async_download_document_files`
- `async_download_drawing_files`
- `async_download_specification_files`

These helpers are read-only. They save files locally when a resource record
contains a direct download URL such as `download_url`, `url`, `file_url`, or
`pdf_url`. Not every Procore endpoint returns a direct download URL, so these
helpers are intentionally documented as patterns. If a payload does not include
a usable direct URL, the manifest records a failure instead of guessing.

Filenames are sanitized, existing files are skipped unless `overwrite=True`, and
destination paths are kept inside the output directory.

## Manifests

Async exports return `AsyncExportResult`. Grouped export and download workflows
can use:

- `AsyncExportManifest`
- `AsyncDownloadResult`
- `AsyncDownloadManifest`

Download manifests include:

- resource name
- output directory
- file count
- success, skipped, and failure counts
- dry-run status
- per-file status and non-sensitive error text

Manifests do not include raw access tokens, refresh tokens, client secrets, or
signed download URLs.

## Concurrency Limits

`async_download_with_manifest` accepts `max_concurrency`. The default is
conservative. Internally the helper uses an async semaphore, captures per-file
results, and can continue after individual failures:

```python
manifest = await async_download_with_manifest(
    transport,
    records,
    "exports/files",
    max_concurrency=4,
    continue_on_error=True,
)
```

This is a local helper, not a scheduler, queue, webhook processor, or background
job runner.

## Async Multi-Project Batch Operations

Phase 10C adds read-only async batch helpers for large-company workflows that
need to collect or export the same resource family across many projects:

- `AsyncBatchPlan`
- `AsyncBatchManifest`
- `AsyncBatchResourceResult`
- `AsyncProjectResult`
- `build_async_batch_plan`
- `validate_async_batch_plan`
- `build_async_batch_dry_run_manifest`
- `async_run_project_batch`
- `async_export_multi_project_resources`
- `async_collect_multi_project_resources`

Supported async batch resources are:

- `rfis`
- `submittals`
- `documents`
- `drawings`
- `specification_sections`
- `observations`
- `punch_items`
- `meetings`
- `inspections`
- `incidents`
- `locations`
- `project_users`
- `vendors`
- `change_events`
- `prime_change_orders`
- `commitment_change_orders`
- `direct_costs`
- `budget_views`
- `commitments`
- `contracts`
- `subcontractor_invoices`
- `billing_periods`
- `project_schedule`
- `tasks`
- `calendar_items`
- `coordination_issues`
- `forms`
- `action_plans`

Batch helpers use the existing `AsyncProcore` read methods and Phase 10B
CSV/JSONL writers. They do not add Procore write, upload, approval, or mutation
operations.

## Dry-Run Planning

Dry-run planning is local-only. It validates the company ID, project IDs,
resources, output format, output path, and concurrency settings, then returns a
manifest describing the project/resource output paths:

```python
from pyprocore import build_async_batch_dry_run_manifest, build_async_batch_plan

plan = build_async_batch_plan(
    company_id=123456,
    project_ids=[111, 222],
    resources=["rfis", "submittals"],
    output_dir="./exports/async-batch",
    dry_run=True,
)

manifest = build_async_batch_dry_run_manifest(plan)
print(len(manifest.results))
```

No Procore API calls are made during validation or dry-run planning.

## Multi-Project Exports

For real read-only exports, pass a configured `AsyncProcore` client and a
non-dry-run plan:

```python
import asyncio

from pyprocore import AsyncProcore, build_async_batch_plan, async_export_multi_project_resources


async def main() -> None:
    plan = build_async_batch_plan(
        company_id=123456,
        project_ids=[111, 222],
        resources=["rfis", "documents"],
        output_dir="./exports/async-batch",
        output_format="jsonl",
        dry_run=False,
        max_concurrency=4,
    )
    async with AsyncProcore() as client:
        manifest = await async_export_multi_project_resources(client, plan)
        print(manifest.completed_count)


asyncio.run(main())
```

The convenience helpers `async_export_multi_project_rfis`,
`async_export_multi_project_submittals`, `async_export_multi_project_documents`,
`async_export_multi_project_drawings`, and
`async_export_multi_project_specification_sections` build one-resource plans for
you.

## In-Memory Collection

Use collection helpers when you want structured records in memory instead of
local files:

- `async_collect_multi_project_rfis`
- `async_collect_multi_project_submittals`
- `async_collect_multi_project_documents`
- `async_collect_multi_project_drawings`
- `async_collect_multi_project_specifications`

Collected records are available on the result objects at runtime, but manifest
JSON serialization excludes those in-memory records so signed URLs and large
payloads are not accidentally written into summary files.

## Batch Manifests And Resume Pattern

Batch manifests capture project/resource status, output paths, record counts,
warnings, and redacted errors. A previous manifest can be passed back into a
batch run so completed project/resource pairs are skipped and failed pairs can
be retried.

This is intentionally a simple resume/skip pattern, not a scheduler, queue,
database, background worker, or cloud sync engine.

## Async Batch CLI

Phase 10C adds local-only planning commands:

```bash
procore-sdk async-batch sample-config
procore-sdk async-batch validate examples/configs/async_batch_dry_run.json
procore-sdk async-batch dry-run examples/configs/async_batch_dry_run.json
```

These commands do not construct a Procore client, do not require credentials,
and do not call Procore. Live batch export commands are intentionally left out
of the CLI for this phase.

## Safety boundaries

- Existing sync APIs remain backward compatible.
- Existing sync exports remain supported.
- Tests and examples do not call live Procore APIs.
- No external AI/model APIs are called.
- No required vector DB or AI dependencies are added.
- Async exports and downloads are read-only and local-file-only.
- Async batch helpers are read-only and additive.
- Financial, contract, billing, and project-management async coverage is
  read-only.
- No upload or Procore mutation actions are added.
- No invoice submissions, payment actions, budget edits, contract edits,
  schedule imports, form submissions, or action-plan completions are added.
- Agent tool execution remains disabled.
- MCP remains discovery-only.
- Agent evals remain local and deterministic.

Phase 15A, Phase 15B, and Phase 15C MCP discovery include async capability,
resource, export, batch, download-pattern, safety, read-only coverage,
contract, and compatibility metadata so MCP clients can inspect async coverage
without credentials or live API calls.
