"""Async export and download helpers for read-only Procore workflows."""

from __future__ import annotations

import asyncio
import csv
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from pyprocore.async_client import AsyncProcore
from pyprocore.core.async_transport import AsyncTransport
from pyprocore.core.exceptions import ProcoreAPIError, ValidationError
from pyprocore.services.files import sanitize_filename
from pyprocore.workflows.utils import get_value, model_to_dict, scalar_text

DEFAULT_ASYNC_CONCURRENCY = 4
DEFAULT_ASYNC_DOWNLOAD_FILENAME = "download"
DOWNLOAD_URL_KEYS = ("download_url", "url", "file_url", "pdf_url")


class AsyncExportResult(BaseModel):
    """Manifest for one async export file."""

    resource_name: str
    output_path: Path
    record_count: int
    format: Literal["csv", "jsonl"]
    dry_run: bool = False
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class AsyncExportManifest(BaseModel):
    """Manifest for a group of async export files."""

    resource_name: str
    output_path: Path
    record_count: int
    files: list[AsyncExportResult] = Field(default_factory=list)
    dry_run: bool = False
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class AsyncDownloadResult(BaseModel):
    """Result for one async download attempt."""

    source_label: str
    output_path: Path | None = None
    status: Literal["downloaded", "skipped", "failed", "dry_run"] = "downloaded"
    bytes_written: int = 0
    error: str | None = None


class AsyncDownloadManifest(BaseModel):
    """Manifest for async file download attempts."""

    resource_name: str
    output_dir: Path
    file_count: int
    success_count: int
    failure_count: int
    skipped_count: int
    dry_run: bool = False
    results: list[AsyncDownloadResult] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


async def async_export_records_csv(
    records: Sequence[object],
    output_path: Path | str,
    *,
    resource_name: str = "records",
    headers: Sequence[str] | None = None,
    dry_run: bool = False,
) -> AsyncExportResult:
    """Write records to CSV and return an export result."""
    path = Path(output_path)
    serializable_records = [model_to_dict(record) for record in records]
    csv_headers = list(headers or _infer_headers(serializable_records))
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as file_handle:
            writer = csv.DictWriter(file_handle, fieldnames=csv_headers)
            writer.writeheader()
            for record in serializable_records:
                writer.writerow({header: _csv_value(record.get(header)) for header in csv_headers})

    return AsyncExportResult(
        resource_name=resource_name,
        output_path=path,
        record_count=len(serializable_records),
        format="csv",
        dry_run=dry_run,
    )


async def async_export_records_jsonl(
    records: Sequence[object],
    output_path: Path | str,
    *,
    resource_name: str = "records",
    dry_run: bool = False,
) -> AsyncExportResult:
    """Write records to newline-delimited JSON and return an export result."""
    path = Path(output_path)
    serializable_records = [model_to_dict(record) for record in records]
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as file_handle:
            for record in serializable_records:
                file_handle.write(json.dumps(record, default=str, sort_keys=True))
                file_handle.write("\n")

    return AsyncExportResult(
        resource_name=resource_name,
        output_path=path,
        record_count=len(serializable_records),
        format="jsonl",
        dry_run=dry_run,
    )


async def async_export_companies(
    client: AsyncProcore,
    output_path: Path | str,
    *,
    output_format: Literal["csv", "jsonl"] = "jsonl",
    dry_run: bool = False,
) -> AsyncExportResult:
    """Export companies available to the authenticated user."""
    records = await client.list_companies()
    return await _write_export_result(records, output_path, "companies", output_format, dry_run)


async def async_export_projects(
    client: AsyncProcore,
    company_id: int,
    output_path: Path | str,
    *,
    output_format: Literal["csv", "jsonl"] = "jsonl",
    dry_run: bool = False,
) -> AsyncExportResult:
    """Export projects for a company."""
    records = await client.list_projects(company_id)
    return await _write_export_result(records, output_path, "projects", output_format, dry_run)


async def async_export_rfis(
    client: AsyncProcore,
    company_id: int,
    project_id: int,
    output_path: Path | str,
    *,
    output_format: Literal["csv", "jsonl"] = "jsonl",
    dry_run: bool = False,
    **filters: Any,
) -> AsyncExportResult:
    """Export RFIs for a project."""
    records = await client.list_rfis(company_id, project_id, **filters)
    return await _write_export_result(records, output_path, "rfis", output_format, dry_run)


async def async_export_submittals(
    client: AsyncProcore,
    company_id: int,
    project_id: int,
    output_path: Path | str,
    *,
    output_format: Literal["csv", "jsonl"] = "jsonl",
    dry_run: bool = False,
    **filters: Any,
) -> AsyncExportResult:
    """Export submittals for a project."""
    records = await client.list_submittals(company_id, project_id, **filters)
    return await _write_export_result(records, output_path, "submittals", output_format, dry_run)


async def async_export_documents(
    client: AsyncProcore,
    company_id: int,
    project_id: int,
    output_path: Path | str,
    *,
    output_format: Literal["csv", "jsonl"] = "jsonl",
    dry_run: bool = False,
    **filters: Any,
) -> AsyncExportResult:
    """Export documents for a project."""
    records = await client.list_documents(company_id, project_id, **filters)
    return await _write_export_result(records, output_path, "documents", output_format, dry_run)


async def async_export_drawings(
    client: AsyncProcore,
    company_id: int,
    project_id: int,
    output_path: Path | str,
    *,
    drawing_area_id: int | None = None,
    output_format: Literal["csv", "jsonl"] = "jsonl",
    dry_run: bool = False,
    **filters: Any,
) -> AsyncExportResult:
    """Export drawings for one drawing area or all project drawing areas."""
    records = await client.list_drawings(
        company_id,
        project_id,
        drawing_area_id=drawing_area_id,
        **filters,
    )
    return await _write_export_result(records, output_path, "drawings", output_format, dry_run)


async def async_export_specification_sections(
    client: AsyncProcore,
    company_id: int,
    project_id: int,
    output_path: Path | str,
    *,
    output_format: Literal["csv", "jsonl"] = "jsonl",
    dry_run: bool = False,
    **filters: Any,
) -> AsyncExportResult:
    """Export specification sections for a project."""
    records = await client.list_specification_sections(company_id, project_id, **filters)
    return await _write_export_result(
        records,
        output_path,
        "specification_sections",
        output_format,
        dry_run,
    )


async def async_download_file_from_url(
    transport: AsyncTransport,
    url: str,
    output_dir: Path | str,
    *,
    filename: str | None = None,
    source_label: str = "download",
    headers: Mapping[str, str] | None = None,
    overwrite: bool = False,
    dry_run: bool = False,
    timeout: int | None = None,
) -> AsyncDownloadResult:
    """Download one direct URL through an async transport into a safe local path."""
    output_root = _safe_output_root(output_dir)
    normalized_url = url.strip()
    if not normalized_url:
        raise ValidationError("Download URL cannot be empty.")

    safe_name = sanitize_filename(filename or _filename_from_url(normalized_url))
    output_path = _safe_child_path(output_root, safe_name)
    if dry_run:
        return AsyncDownloadResult(
            source_label=source_label,
            output_path=output_path,
            status="dry_run",
        )
    if output_path.exists() and not overwrite:
        return AsyncDownloadResult(
            source_label=source_label,
            output_path=output_path,
            status="skipped",
            bytes_written=output_path.stat().st_size,
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    response = await transport.request(
        method="GET",
        url=normalized_url,
        headers=headers,
        timeout=timeout,
    )
    if not response.ok:
        raise ProcoreAPIError(
            f"Async download failed with status {response.status_code} for {source_label}",
            status_code=response.status_code,
            response_body=_safe_download_error_body(response.text),
        )
    content = response.content or response.text.encode("utf-8")
    temporary_path = output_path.with_suffix(f"{output_path.suffix}.tmp")
    temporary_path.write_bytes(content)
    temporary_path.replace(output_path)
    return AsyncDownloadResult(
        source_label=source_label,
        output_path=output_path,
        status="downloaded",
        bytes_written=len(content),
    )


async def async_download_with_manifest(
    transport: AsyncTransport,
    items: Sequence[Mapping[str, Any] | object],
    output_dir: Path | str,
    *,
    resource_name: str = "files",
    max_concurrency: int = DEFAULT_ASYNC_CONCURRENCY,
    continue_on_error: bool = True,
    overwrite: bool = False,
    dry_run: bool = False,
    headers: Mapping[str, str] | None = None,
    timeout: int | None = None,
) -> AsyncDownloadManifest:
    """Download many records that contain direct URLs and return a manifest."""
    output_root = _safe_output_root(output_dir)
    semaphore = asyncio.Semaphore(max(1, max_concurrency))
    results: list[AsyncDownloadResult] = []
    errors: list[str] = []

    async def download_one(index: int, item: Mapping[str, Any] | object) -> None:
        async with semaphore:
            url = _record_download_url(item)
            label = _record_source_label(item, index)
            if not url:
                result = AsyncDownloadResult(
                    source_label=label,
                    status="failed",
                    error="No direct download URL found.",
                )
                results.append(result)
                errors.append(f"{label}: no direct download URL found")
                if not continue_on_error:
                    raise ValidationError(f"{label} does not include a direct download URL.")
                return
            try:
                results.append(
                    await async_download_file_from_url(
                        transport,
                        url,
                        output_root,
                        filename=_record_filename(item, index),
                        source_label=label,
                        headers=headers,
                        overwrite=overwrite,
                        dry_run=dry_run,
                        timeout=timeout,
                    )
                )
            except Exception as exc:
                result = AsyncDownloadResult(
                    source_label=label,
                    status="failed",
                    error=str(exc),
                )
                results.append(result)
                errors.append(f"{label}: {exc}")
                if not continue_on_error:
                    raise

    await asyncio.gather(*(download_one(index, item) for index, item in enumerate(items, start=1)))
    return _download_manifest(
        resource_name=resource_name,
        output_dir=output_root,
        results=results,
        dry_run=dry_run,
        errors=errors,
    )


async def async_download_document_files(
    client: AsyncProcore,
    transport: AsyncTransport,
    company_id: int,
    project_id: int,
    output_dir: Path | str,
    **options: Any,
) -> AsyncDownloadManifest:
    """List and download document records that include direct download URLs."""
    documents = await client.list_documents(company_id, project_id)
    return await async_download_with_manifest(
        transport,
        documents,
        output_dir,
        resource_name="documents",
        **options,
    )


async def async_download_drawing_files(
    client: AsyncProcore,
    transport: AsyncTransport,
    company_id: int,
    project_id: int,
    output_dir: Path | str,
    *,
    drawing_area_id: int | None = None,
    **options: Any,
) -> AsyncDownloadManifest:
    """List and download drawing records that include direct download URLs."""
    drawings = await client.list_drawings(
        company_id,
        project_id,
        drawing_area_id=drawing_area_id,
    )
    return await async_download_with_manifest(
        transport,
        drawings,
        output_dir,
        resource_name="drawings",
        **options,
    )


async def async_download_specification_files(
    client: AsyncProcore,
    transport: AsyncTransport,
    company_id: int,
    project_id: int,
    output_dir: Path | str,
    **options: Any,
) -> AsyncDownloadManifest:
    """List and download specification records that include direct download URLs."""
    sections = await client.list_specification_sections(company_id, project_id)
    return await async_download_with_manifest(
        transport,
        sections,
        output_dir,
        resource_name="specification_sections",
        **options,
    )


async def _write_export_result(
    records: Sequence[object],
    output_path: Path | str,
    resource_name: str,
    output_format: Literal["csv", "jsonl"],
    dry_run: bool,
) -> AsyncExportResult:
    """Write records in the requested format."""
    if output_format == "csv":
        return await async_export_records_csv(
            records,
            output_path,
            resource_name=resource_name,
            dry_run=dry_run,
        )
    return await async_export_records_jsonl(
        records,
        output_path,
        resource_name=resource_name,
        dry_run=dry_run,
    )


def _infer_headers(records: Sequence[Mapping[str, Any]]) -> list[str]:
    """Infer stable CSV headers from record keys."""
    headers: list[str] = []
    for record in records:
        for key in record:
            if key not in headers:
                headers.append(key)
    return headers or ["value"]


def _csv_value(value: object) -> str:
    """Return a CSV-safe scalar string."""
    return scalar_text(value)


def _safe_output_root(output_dir: Path | str) -> Path:
    """Return a resolved output root without requiring it to exist first."""
    return Path(output_dir).expanduser().resolve()


def _safe_child_path(output_root: Path, filename: str) -> Path:
    """Return a path guaranteed to stay inside the output root."""
    candidate = (output_root / sanitize_filename(filename)).resolve()
    if not candidate.is_relative_to(output_root):
        raise ValidationError("Download destination cannot escape the output directory.")
    return candidate


def _filename_from_url(url: str) -> str:
    """Return a safe filename candidate from a URL path."""
    path_name = Path(url.split("?", 1)[0]).name
    return path_name or DEFAULT_ASYNC_DOWNLOAD_FILENAME


def _record_download_url(item: Mapping[str, Any] | object) -> str | None:
    """Return the first direct download URL found on a record."""
    for key in DOWNLOAD_URL_KEYS:
        value = get_value(item, key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _record_filename(item: Mapping[str, Any] | object, index: int) -> str:
    """Return a safe local filename for a downloadable record."""
    for key in ("filename", "file_name", "name", "title", "number"):
        value = get_value(item, key)
        if isinstance(value, str) and value.strip():
            return sanitize_filename(value)
    return f"{DEFAULT_ASYNC_DOWNLOAD_FILENAME}-{index}"


def _record_source_label(item: Mapping[str, Any] | object, index: int) -> str:
    """Return a non-sensitive source label for manifest entries."""
    identifier = get_value(item, "id", "number", "name", "title")
    return scalar_text(identifier) or f"item-{index}"


def _download_manifest(
    *,
    resource_name: str,
    output_dir: Path,
    results: Sequence[AsyncDownloadResult],
    dry_run: bool,
    errors: Sequence[str],
) -> AsyncDownloadManifest:
    """Build a summarized download manifest."""
    success_count = sum(1 for result in results if result.status == "downloaded")
    skipped_count = sum(1 for result in results if result.status in {"skipped", "dry_run"})
    failure_count = sum(1 for result in results if result.status == "failed")
    return AsyncDownloadManifest(
        resource_name=resource_name,
        output_dir=output_dir,
        file_count=len(results),
        success_count=success_count,
        failure_count=failure_count,
        skipped_count=skipped_count,
        dry_run=dry_run,
        results=list(results),
        errors=list(errors),
    )


def _safe_download_error_body(text: str) -> str:
    """Return bounded non-secret error text for manifests and exceptions."""
    lowered = text.casefold()
    if any(secret in lowered for secret in ("access_token", "refresh_token", "client_secret")):
        return "[REDACTED]"
    return text[:500]


__all__ = [
    "AsyncDownloadManifest",
    "AsyncDownloadResult",
    "AsyncExportManifest",
    "AsyncExportResult",
    "async_download_document_files",
    "async_download_drawing_files",
    "async_download_file_from_url",
    "async_download_specification_files",
    "async_download_with_manifest",
    "async_export_companies",
    "async_export_documents",
    "async_export_drawings",
    "async_export_projects",
    "async_export_records_csv",
    "async_export_records_jsonl",
    "async_export_rfis",
    "async_export_specification_sections",
    "async_export_submittals",
]
