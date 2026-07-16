# Async Client

Phase 10A adds an async client foundation in the current unreleased branch.
Phase 10B builds on that foundation with async export helpers, local download
patterns, manifests, and simple concurrency controls. The published stable
release remains `2.2.0`; Phase 10A and Phase 10B remain branch-only until a
future release is cut.

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

No create, update, delete, upload, approval, status-change, or mutation helpers
are added in Phase 10A or Phase 10B.

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

## Safety boundaries

- Existing sync APIs remain backward compatible.
- Existing sync exports remain supported.
- Tests and examples do not call live Procore APIs.
- No external AI/model APIs are called.
- No required vector DB or AI dependencies are added.
- Async exports and downloads are read-only and local-file-only.
- No upload or Procore mutation actions are added.
- Agent tool execution remains disabled.
- MCP remains discovery-only.
- Agent evals remain local and deterministic.
