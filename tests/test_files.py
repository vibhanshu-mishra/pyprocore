"""Unit tests for shared file download helpers."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock

import requests
from requests import Response
from tenacity import wait_none

from pyprocore.core.exceptions import ProcoreAPIError, ValidationError
from pyprocore.services.files import FileDownloadService, attachment_filename, download_url


def file_response(
    status_code: int = 200,
    body: bytes = b"file-bytes",
    text: str = "file-bytes",
) -> Response:
    """Build a mocked file response."""
    response = Response()
    response.status_code = status_code
    response._content = body
    response.encoding = "utf-8"
    response.iter_content = Mock(return_value=[body[:4], b"", body[4:]])
    return response


class FileDownloadServiceTestCase(unittest.TestCase):
    """Validate signed attachment download behavior."""

    def setUp(self) -> None:
        """Create fresh mocks for each test."""
        self.token_manager = Mock()
        self.token_manager.get_access_token.return_value = "access-token"
        self.session = Mock(spec=requests.Session)
        self.service = FileDownloadService(
            token_manager=self.token_manager,
            session=self.session,
            timeout_seconds=3,
        )

    def test_download_url_streams_file_with_bearer_token(self) -> None:
        """Signed URLs are downloaded with the current bearer token."""
        self.session.get.return_value = file_response(body=b"abcdef")

        with TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "nested" / "file.txt"
            saved_path = self.service.download_url("https://signed.example/file.txt", destination)

            self.assertEqual(saved_path, destination)
            self.assertEqual(destination.read_bytes(), b"abcdef")

        self.session.get.assert_called_once()
        request_kwargs = self.session.get.call_args.kwargs
        self.assertEqual(request_kwargs["headers"]["Authorization"], "Bearer access-token")
        self.assertTrue(request_kwargs["stream"])
        self.assertEqual(request_kwargs["timeout"], 3)

    def test_download_url_validates_blank_url(self) -> None:
        """Blank URLs are rejected before HTTP calls."""
        with self.assertRaises(ValidationError):
            self.service.download_url("   ", Path("file.txt"))

        self.session.get.assert_not_called()

    def test_download_url_raises_on_http_failure(self) -> None:
        """HTTP failures become ProcoreAPIError."""
        self.session.get.return_value = file_response(status_code=404, body=b"missing")

        with TemporaryDirectory() as temporary_directory:
            with self.assertRaises(ProcoreAPIError) as context:
                self.service.download_url(
                    "https://signed.example/missing.pdf",
                    Path(temporary_directory) / "missing.pdf",
                )

        self.assertEqual(context.exception.status_code, 404)

    def test_download_url_raises_on_request_exception(self) -> None:
        """Network exceptions become ProcoreAPIError."""
        original_wait = FileDownloadService._get_with_retry.retry.wait
        FileDownloadService._get_with_retry.retry.wait = wait_none()
        self.session.get.side_effect = requests.RequestException("timeout")

        try:
            with TemporaryDirectory() as temporary_directory:
                with self.assertRaises(ProcoreAPIError):
                    self.service.download_url(
                        "https://signed.example/file.pdf",
                        Path(temporary_directory) / "file.pdf",
                    )
        finally:
            FileDownloadService._get_with_retry.retry.wait = original_wait

    def test_download_url_skips_existing_file_by_default(self) -> None:
        """Existing files are skipped unless overwrite is enabled."""
        with TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "existing.txt"
            destination.write_text("already here", encoding="utf-8")

            saved_path = self.service.download_url("https://signed.example/file.txt", destination)

            self.assertEqual(saved_path, destination)
            self.assertEqual(destination.read_text(encoding="utf-8"), "already here")
            self.session.get.assert_not_called()

    def test_download_url_retries_transient_download_failure(self) -> None:
        """Transient download failures are retried."""
        original_wait = FileDownloadService._get_with_retry.retry.wait
        FileDownloadService._get_with_retry.retry.wait = wait_none()
        self.session.get.side_effect = [
            file_response(status_code=500, body=b"temporary"),
            file_response(status_code=200, body=b"ok"),
        ]

        try:
            with TemporaryDirectory() as temporary_directory:
                destination = Path(temporary_directory) / "file.txt"
                saved_path = self.service.download_url(
                    "https://signed.example/file.txt",
                    destination,
                )
                self.assertEqual(saved_path.read_bytes(), b"ok")
        finally:
            FileDownloadService._get_with_retry.retry.wait = original_wait

        self.assertEqual(self.session.get.call_count, 2)

    def test_download_attachment_returns_none_when_url_missing(self) -> None:
        """Attachment metadata without a usable URL is skipped."""
        result = self.service.download_attachment(
            {"name": "file.pdf"},
            Path("/tmp"),
            "fallback.pdf",
        )

        self.assertIsNone(result)
        self.session.get.assert_not_called()

    def test_download_attachment_uses_metadata_filename(self) -> None:
        """Attachment metadata names are sanitized and used for destinations."""
        self.session.get.return_value = file_response(body=b"ok")

        with TemporaryDirectory() as temporary_directory:
            saved = self.service.download_attachment(
                {
                    "url": "https://signed.example/path/ignored.pdf",
                    "filename": "../safe.pdf",
                },
                temporary_directory,
                "fallback.pdf",
            )

            self.assertIsNotNone(saved)
            assert saved is not None
            self.assertEqual(saved.name, "safe.pdf")
            self.assertEqual(saved.read_bytes(), b"ok")

    def test_download_attachments_downloads_multiple_files(self) -> None:
        """Batch attachment downloads return saved paths and skip missing URLs."""
        self.session.get.side_effect = [
            file_response(body=b"one"),
            file_response(body=b"two"),
        ]

        with TemporaryDirectory() as temporary_directory:
            paths = self.service.download_attachments(
                [
                    {"url": "https://signed.example/one.pdf"},
                    {"name": "missing-url"},
                    {"url": "https://signed.example/two.pdf"},
                ],
                temporary_directory,
                fallback_prefix="batch",
            )

            self.assertEqual([path.name for path in paths], ["one.pdf", "two.pdf"])
            self.assertEqual(paths[0].read_bytes(), b"one")
            self.assertEqual(paths[1].read_bytes(), b"two")

    def test_attachment_filename_falls_back_to_url_or_fallback(self) -> None:
        """Filename extraction prefers metadata, then URL, then fallback."""
        self.assertEqual(
            attachment_filename(
                {"url": "https://signed.example/path/spec.pdf?x=1"}, "fallback.bin"
            ),
            "spec.pdf",
        )
        self.assertEqual(
            attachment_filename({"url": "https://signed.example/"}, "../fallback.bin"),
            "fallback.bin",
        )

    def test_module_level_download_url_uses_file_service(self) -> None:
        """The convenience function delegates to FileDownloadService."""
        token_manager = Mock()
        token_manager.get_access_token.return_value = "token"

        with TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "file.txt"
            with unittest.mock.patch("pyprocore.services.files.requests.Session") as session_class:
                session = Mock()
                session.get.return_value = file_response(body=b"ok")
                session_class.return_value = session

                self.assertEqual(
                    download_url("https://signed.example/file.txt", destination, token_manager),
                    destination,
                )


if __name__ == "__main__":
    unittest.main()
