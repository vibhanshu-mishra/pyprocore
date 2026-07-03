"""Shared file download helpers for Procore resources."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from auth.token_manager import TokenManager
from core.client import DEFAULT_TIMEOUT_SECONDS
from core.exceptions import ProcoreAPIError, ValidationError
from core.logger import get_logger, log_exception, structured_message

DEFAULT_DOWNLOAD_DIR = Path(__file__).resolve().parents[1] / "downloads"
DEFAULT_CHUNK_SIZE = 1024 * 1024
UNSAFE_FILENAME_PATTERN = re.compile(r"[^A-Za-z0-9._ -]+")


class FileDownloadService:
    """Service for downloading signed Procore attachment URLs."""

    def __init__(
        self,
        token_manager: TokenManager | None = None,
        session: requests.Session | None = None,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ) -> None:
        """Initialize the file download service.

        Args:
            token_manager: Optional token manager for bearer tokens.
            session: Optional HTTP session for file requests.
            timeout_seconds: Timeout for file requests.
            chunk_size: Number of bytes written per streamed chunk.
        """
        self._token_manager = token_manager or TokenManager()
        self._session = session or requests.Session()
        self._timeout_seconds = timeout_seconds
        self._chunk_size = chunk_size
        self._logger = get_logger("files")

    def download_url(
        self,
        url: str,
        destination: Path | str,
        *,
        overwrite: bool = False,
    ) -> Path:
        """Download a signed Procore URL to a destination path.

        Args:
            url: Signed Procore attachment URL.
            destination: Full local destination path.
            overwrite: Whether to overwrite an existing destination file.

        Returns:
            The saved file path.
        """
        normalized_url = url.strip()
        if not normalized_url:
            raise ValidationError("Attachment URL cannot be empty.")

        destination_path = Path(destination)
        if destination_path.name in {"", ".", ".."}:
            raise ValidationError("Attachment destination must include a filename.")

        destination_path = destination_path.with_name(
            sanitize_filename(destination_path.name)
        )
        if destination_path.exists() and not overwrite:
            self._logger.info(
                structured_message(
                    "download_skipped",
                    path=str(destination_path),
                    reason="exists",
                )
            )
            return destination_path

        destination_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            response = self._get_with_retry(normalized_url)
            self._raise_for_download_status(response, normalized_url)
            self._write_stream(response, destination_path)
        except requests.RequestException as exc:
            log_exception(
                self._logger,
                exc=exc,
                request_url=normalized_url,
                http_status=getattr(
                    locals().get("response", None), "status_code", None
                ),
                response_body=getattr(locals().get("response", None), "text", None),
            )
            raise ProcoreAPIError(
                f"Attachment download failed for {normalized_url}: {exc}"
            ) from exc
        except Exception as exc:
            log_exception(
                self._logger,
                exc=exc,
                request_url=normalized_url,
                http_status=getattr(
                    locals().get("response", None), "status_code", None
                ),
                response_body=getattr(locals().get("response", None), "text", None),
            )
            raise

        self._logger.info(
            structured_message(
                "download_complete",
                path=str(destination_path),
                bytes=destination_path.stat().st_size,
            )
        )
        return destination_path

    def download_attachment(
        self,
        attachment: Mapping[str, Any],
        destination_dir: Path | str,
        fallback_name: str,
        *,
        overwrite: bool = False,
    ) -> Path | None:
        """Download an attachment mapping that contains a ``url`` value.

        Args:
            attachment: Procore attachment metadata.
            destination_dir: Local directory where the file should be saved.
            fallback_name: Filename used when metadata and URL do not provide
                one.
            overwrite: Whether to overwrite an existing destination file.

        Returns:
            The saved file path, or ``None`` when the attachment has no URL.
        """
        url = attachment.get("url")
        if not isinstance(url, str) or not url.strip():
            return None

        filename = attachment_filename(attachment, fallback_name)
        return self.download_url(
            url,
            Path(destination_dir) / filename,
            overwrite=overwrite,
        )

    def download_attachments(
        self,
        attachments: Iterable[Mapping[str, Any]],
        destination_dir: Path | str,
        *,
        fallback_prefix: str = "attachment",
        overwrite: bool = False,
    ) -> list[Path]:
        """Download multiple attachment mappings to a destination directory."""
        downloaded_files: list[Path] = []
        for index, attachment in enumerate(attachments, start=1):
            downloaded_file = self.download_attachment(
                attachment,
                destination_dir,
                fallback_name=f"{fallback_prefix}-{index}",
                overwrite=overwrite,
            )
            if downloaded_file is not None:
                downloaded_files.append(downloaded_file)
        return downloaded_files

    @retry(
        retry=retry_if_exception_type((requests.RequestException, ProcoreAPIError)),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def _get_with_retry(self, url: str) -> requests.Response:
        """GET a signed URL with retry support."""
        headers = {"Authorization": f"Bearer {self._token_manager.get_access_token()}"}
        response = self._session.get(
            url,
            headers=headers,
            stream=True,
            timeout=self._timeout_seconds,
        )
        if response.status_code >= 500 or response.status_code == 429:
            raise ProcoreAPIError(
                f"Attachment download failed with status {response.status_code} for {url}",
                status_code=response.status_code,
                response_body=response.text,
            )
        return response

    @staticmethod
    def _raise_for_download_status(response: requests.Response, url: str) -> None:
        """Raise when a download response is unsuccessful."""
        if response.ok:
            return
        raise ProcoreAPIError(
            f"Attachment download failed with status {response.status_code} for {url}",
            status_code=response.status_code,
            response_body=response.text,
        )

    def _write_stream(
        self, response: requests.Response, destination_path: Path
    ) -> None:
        """Write a streamed response to disk in chunks."""
        temporary_path = destination_path.with_suffix(f"{destination_path.suffix}.tmp")
        bytes_written = 0
        try:
            with temporary_path.open("wb") as file_handle:
                for chunk in response.iter_content(chunk_size=self._chunk_size):
                    if not chunk:
                        continue
                    file_handle.write(chunk)
                    bytes_written += len(chunk)
                    self._logger.info(
                        structured_message(
                            "download_progress",
                            path=str(destination_path),
                            bytes=bytes_written,
                        )
                    )
            temporary_path.replace(destination_path)
        except OSError as exc:
            raise ProcoreAPIError(
                f"Unable to save attachment {destination_path}: {exc}"
            ) from exc


def sanitize_filename(filename: str) -> str:
    """Return a filesystem-safe filename."""
    candidate = Path(filename.strip()).name
    candidate = UNSAFE_FILENAME_PATTERN.sub("_", candidate)
    candidate = candidate.strip(" .")
    return candidate or "attachment"


def attachment_filename(attachment: Mapping[str, Any], fallback_name: str) -> str:
    """Return a safe filename from attachment metadata or URL path."""
    for key in ("filename", "file_name", "name"):
        value = attachment.get(key)
        if isinstance(value, str) and value.strip():
            return sanitize_filename(value)

    url = attachment.get("url")
    if isinstance(url, str) and url.strip():
        parsed_path = unquote(urlparse(url).path)
        path_name = Path(parsed_path).name
        if path_name:
            return sanitize_filename(path_name)

    return sanitize_filename(fallback_name)


def download_url(
    url: str,
    destination: Path | str,
    token_manager: TokenManager | None = None,
    *,
    overwrite: bool = False,
) -> Path:
    """Download a signed Procore URL with the default file service."""
    return FileDownloadService(token_manager=token_manager).download_url(
        url,
        destination,
        overwrite=overwrite,
    )
