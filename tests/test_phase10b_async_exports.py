"""Tests for Phase 10B async export and download patterns."""

from __future__ import annotations

import asyncio
import csv
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

import pyprocore
from pyprocore import AsyncProcore, MockAsyncTransport
from pyprocore.core.async_transport import AsyncResponse
from pyprocore.core.config import ProcoreSettings
from pyprocore.core.exceptions import ProcoreAPIError, ValidationError
from pyprocore.workflows.async_exports import (
    AsyncDownloadManifest,
    AsyncExportResult,
    async_download_file_from_url,
    async_download_with_manifest,
    async_export_companies,
    async_export_documents,
    async_export_projects,
    async_export_records_csv,
    async_export_records_jsonl,
    async_export_rfis,
    async_export_submittals,
)
from pyprocore.workflows.exports import write_rfis_csv


class FakeTokenManager:
    """Token manager test double that never calls Procore."""

    def get_access_token(self, force_refresh: bool = False) -> str:
        """Return a placeholder token."""
        return "placeholder-access-token"


def settings() -> ProcoreSettings:
    """Return test settings."""
    return ProcoreSettings(
        client_id="client-id",
        client_secret="client-secret",
        redirect_uri="http://localhost/callback",
        login_url="https://login.example.com",
        api_base="https://api.example.com",
        company_id=123,
    )


def json_response(payload: Any) -> AsyncResponse:
    """Build a JSON async response."""
    return AsyncResponse(
        status_code=200,
        url="https://api.example.com/rest/v1.0/example",
        headers={"Content-Type": "application/json"},
        json_data=payload,
        content=b"{}",
    )


def file_response(content: bytes, *, status_code: int = 200, text: str = "") -> AsyncResponse:
    """Build a file-like async response."""
    return AsyncResponse(
        status_code=status_code,
        url="https://download.example.com/file.pdf",
        headers={"Content-Type": "application/octet-stream"},
        content=content,
        text=text,
    )


def async_client(responses: list[AsyncResponse]) -> AsyncProcore:
    """Build an async client backed by mock responses."""
    return AsyncProcore(
        settings=settings(),
        token_manager=FakeTokenManager(),  # type: ignore[arg-type]
        transport=MockAsyncTransport(responses),
        retry_sleep_seconds=0,
    )


class Phase10BAsyncExportTestCase(unittest.IsolatedAsyncioTestCase):
    """Validate async exports using local files only."""

    async def test_async_records_csv_export(self) -> None:
        """Records should export to CSV with inferred headers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "records.csv"

            result = await async_export_records_csv(
                [{"id": 1, "name": "Project"}, {"id": 2, "name": "Hospital"}],
                output_path,
                resource_name="projects",
            )

            self.assertIsInstance(result, AsyncExportResult)
            self.assertEqual(result.record_count, 2)
            with output_path.open(encoding="utf-8") as file_handle:
                rows = list(csv.DictReader(file_handle))
            self.assertEqual(rows[0]["name"], "Project")

    async def test_async_records_jsonl_export(self) -> None:
        """Records should export to JSONL."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "records.jsonl"

            result = await async_export_records_jsonl(
                [{"id": 1, "name": "Company"}],
                output_path,
                resource_name="companies",
            )

            self.assertEqual(result.format, "jsonl")
            lines = output_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(json.loads(lines[0])["name"], "Company")

    async def test_async_dry_run_export_does_not_write_file(self) -> None:
        """Dry-run exports should return a manifest without creating output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "dry-run.jsonl"

            result = await async_export_records_jsonl(
                [{"id": 1}],
                output_path,
                dry_run=True,
            )

            self.assertTrue(result.dry_run)
            self.assertFalse(output_path.exists())

    async def test_async_resource_exports_use_async_client_methods(self) -> None:
        """Resource-specific exports should fetch typed async records and write files."""
        client = async_client(
            [
                json_response([{"id": 1, "name": "Company"}]),
                json_response([{"id": 2, "name": "Project"}]),
                json_response([{"id": 3, "subject": "RFI"}]),
                json_response([{"id": 4, "title": "Submittal"}]),
                json_response([{"files": [{"id": 5, "name": "Document"}]}]),
            ]
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            companies = await async_export_companies(client, root / "companies.jsonl")
            projects = await async_export_projects(
                client, 123, root / "projects.csv", output_format="csv"
            )
            rfis = await async_export_rfis(client, 123, 456, root / "rfis.jsonl")
            submittals = await async_export_submittals(client, 123, 456, root / "submittals.jsonl")
            documents = await async_export_documents(client, 123, 456, root / "documents.jsonl")

            self.assertEqual(companies.record_count, 1)
            self.assertEqual(projects.format, "csv")
            self.assertEqual(rfis.record_count, 1)
            self.assertEqual(submittals.record_count, 1)
            self.assertEqual(documents.record_count, 1)


class Phase10BAsyncDownloadTestCase(unittest.IsolatedAsyncioTestCase):
    """Validate async download safety and manifest behavior."""

    async def test_async_download_file_from_mock_url(self) -> None:
        """One direct URL should download to a sanitized filename."""
        transport = MockAsyncTransport([file_response(b"pdf-bytes")])
        with tempfile.TemporaryDirectory() as temp_dir:
            result = await async_download_file_from_url(
                transport,
                "https://download.example.com/signed/file.pdf?token=secret",
                temp_dir,
                filename="../unsafe:name.pdf",
                source_label="document-1",
            )

            self.assertEqual(result.status, "downloaded")
            self.assertEqual(result.bytes_written, len(b"pdf-bytes"))
            self.assertEqual(result.output_path.name, "unsafe_name.pdf")
            self.assertTrue(result.output_path.read_bytes(), b"pdf-bytes")

    async def test_async_download_skips_existing_file(self) -> None:
        """Existing files should be skipped unless overwrite is requested."""
        transport = MockAsyncTransport([file_response(b"new")])
        with tempfile.TemporaryDirectory() as temp_dir:
            existing = Path(temp_dir) / "file.pdf"
            existing.write_bytes(b"old")

            result = await async_download_file_from_url(
                transport,
                "https://download.example.com/file.pdf",
                temp_dir,
                filename="file.pdf",
            )

            self.assertEqual(result.status, "skipped")
            self.assertEqual(existing.read_bytes(), b"old")
            self.assertEqual(transport.requests, [])

    async def test_async_download_manifest_captures_partial_failure(self) -> None:
        """Download manifest should capture failures when continue-on-error is enabled."""
        transport = MockAsyncTransport(
            [
                file_response(b"ok"),
                file_response(b"missing", status_code=404, text="missing"),
            ]
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest = await async_download_with_manifest(
                transport,
                [
                    {"id": 1, "name": "one.pdf", "url": "https://download.example.com/one.pdf"},
                    {"id": 2, "name": "two.pdf", "url": "https://download.example.com/two.pdf"},
                    {"id": 3, "name": "three.pdf"},
                ],
                temp_dir,
                resource_name="documents",
            )

            self.assertIsInstance(manifest, AsyncDownloadManifest)
            self.assertEqual(manifest.success_count, 1)
            self.assertEqual(manifest.failure_count, 2)
            self.assertNotIn("https://download.example.com", manifest.model_dump_json())

    async def test_async_download_manifest_can_fail_fast(self) -> None:
        """continue_on_error=False should raise on a missing URL."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ValidationError):
                await async_download_with_manifest(
                    MockAsyncTransport([]),
                    [{"id": 1, "name": "missing"}],
                    temp_dir,
                    continue_on_error=False,
                )

    async def test_path_traversal_is_sanitized_to_output_directory(self) -> None:
        """User-provided filenames should not escape the output directory."""
        transport = MockAsyncTransport([file_response(b"safe")])
        with tempfile.TemporaryDirectory() as temp_dir:
            result = await async_download_file_from_url(
                transport,
                "https://download.example.com/file.pdf",
                temp_dir,
                filename="../../outside.pdf",
            )

            self.assertEqual(result.output_path.parent.resolve(), Path(temp_dir).resolve())
            self.assertEqual(result.output_path.name, "outside.pdf")

    async def test_max_concurrency_limits_downloads(self) -> None:
        """Downloads should respect the configured semaphore limit."""

        class TrackingTransport:
            def __init__(self) -> None:
                self.active = 0
                self.max_active = 0

            async def request(self, **_: Any) -> AsyncResponse:
                self.active += 1
                self.max_active = max(self.max_active, self.active)
                await asyncio.sleep(0.01)
                self.active -= 1
                return file_response(b"ok")

            async def close(self) -> None:
                return None

        transport = TrackingTransport()
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest = await async_download_with_manifest(
                transport,
                [
                    {"id": index, "name": f"{index}.pdf", "url": f"https://example.com/{index}.pdf"}
                    for index in range(6)
                ],
                temp_dir,
                max_concurrency=2,
            )

            self.assertEqual(manifest.success_count, 6)
            self.assertLessEqual(transport.max_active, 2)

    async def test_download_error_body_redacts_secret_terms(self) -> None:
        """Download exceptions should not expose obvious secret response bodies."""
        transport = MockAsyncTransport(
            [file_response(b"", status_code=403, text='{"access_token": "secret"}')]
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ProcoreAPIError) as error:
                await async_download_file_from_url(
                    transport,
                    "https://download.example.com/secret.pdf",
                    temp_dir,
                    filename="secret.pdf",
                    source_label="safe-label",
                )

            self.assertEqual(error.exception.response_body, "[REDACTED]")
            self.assertNotIn("access_token", str(error.exception.response_body))


class Phase10BAsyncSafetyTestCase(unittest.TestCase):
    """Validate Phase 10B safety boundaries."""

    def test_sync_exports_remain_available(self) -> None:
        """Existing sync export helpers should remain importable and usable."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = write_rfis_csv([], Path(temp_dir) / "rfis.csv")

            self.assertTrue(output_path.exists())

    def test_root_exports_include_phase10b_helpers(self) -> None:
        """Phase 10B helpers should be available from the package root."""
        self.assertIs(pyprocore.AsyncExportResult, AsyncExportResult)
        self.assertIs(pyprocore.AsyncDownloadManifest, AsyncDownloadManifest)
        self.assertIs(pyprocore.async_export_projects, async_export_projects)
        self.assertEqual(pyprocore.__version__, "2.3.0")

    def test_phase10b_does_not_add_write_upload_helpers(self) -> None:
        """Async export module should remain read/download only."""
        forbidden = ("create", "update", "delete", "upload", "post", "put", "patch")
        for name in dir(pyprocore):
            if not name.startswith("async_"):
                continue
            for marker in forbidden:
                self.assertNotIn(marker, name.casefold())

    def test_agent_and_mcp_execution_remain_disabled(self) -> None:
        """Agent and MCP tool execution must remain disabled."""
        response = pyprocore.build_mcp_tool_execution_disabled_response("procore.async_export")

        self.assertFalse(response["metadata"]["execution_enabled"])
        self.assertTrue(response["metadata"]["discovery_only"])


if __name__ == "__main__":
    unittest.main()
