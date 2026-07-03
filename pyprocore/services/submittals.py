"""Submittal service for the Procore SDK."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from pyprocore.core import endpoints
from pyprocore.core.client import ProcoreClient
from pyprocore.core.exceptions import ValidationError
from pyprocore.models import Submittal
from pyprocore.services.files import FileDownloadService

DEFAULT_DOWNLOAD_DIR = Path(__file__).resolve().parents[1] / "downloads" / "submittals"


class SubmittalsService:
    """Service for Procore submittal resources."""

    def __init__(
        self,
        client: ProcoreClient | None = None,
        file_service: FileDownloadService | None = None,
    ) -> None:
        """Initialize the service.

        Args:
            client: Optional shared Procore HTTP client.
            file_service: Optional shared file download service.
        """
        self._client = client or ProcoreClient()
        self._file_service = file_service or FileDownloadService()

    def list_submittals(self, project_id: int) -> list[Submittal]:
        """Return submittals for a Procore project."""
        self._validate_positive_id(project_id, "project_id")

        response = self._client.get_all(endpoints.submittals(project_id))
        return [Submittal.model_validate(submittal) for submittal in response]

    def get_submittal(self, project_id: int, submittal_id: int) -> Submittal:
        """Return a single submittal for a Procore project."""
        self._validate_positive_id(project_id, "project_id")
        self._validate_positive_id(submittal_id, "submittal_id")

        response = self._client.get(endpoints.submittal(project_id, submittal_id))
        if not isinstance(response, dict):
            raise ValidationError("Expected Procore submittal response to be an object.")
        return Submittal.model_validate(response)

    def download_submittal_attachments(
        self,
        project_id: int,
        submittal_id: int,
        destination_dir: Path | str | None = None,
    ) -> list[Path]:
        """Download all attachments from a submittal.

        Submittal attachment URLs are read from ``attachments[].url``.

        Args:
            project_id: Procore project ID.
            submittal_id: Procore submittal ID.
            destination_dir: Optional directory to save files. Defaults to
                ``downloads/submittals/{submittal_id}``.

        Returns:
            Paths to downloaded files.
        """
        submittal = self.get_submittal(project_id, submittal_id)
        attachments = self._extract_attachments(submittal.model_dump())
        output_dir = (
            Path(destination_dir) if destination_dir else DEFAULT_DOWNLOAD_DIR / str(submittal_id)
        )
        output_dir.mkdir(parents=True, exist_ok=True)

        return self._file_service.download_attachments(
            attachments,
            output_dir,
            fallback_prefix=f"submittal-{submittal_id}",
        )

    @staticmethod
    def _extract_attachments(submittal: Mapping[str, Any]) -> list[dict[str, Any]]:
        """Extract ``attachments[]`` dictionaries from a submittal."""
        attachments = submittal.get("attachments", [])
        if not isinstance(attachments, Sequence) or isinstance(attachments, (str, bytes)):
            return []

        return [dict(attachment) for attachment in attachments if isinstance(attachment, Mapping)]

    @staticmethod
    def _validate_positive_id(value: int, name: str) -> None:
        """Validate Procore integer identifiers."""
        if value <= 0:
            raise ValidationError(f"{name} must be a positive integer.")


def list_submittals(
    project_id: int,
    client: ProcoreClient | None = None,
) -> list[Submittal]:
    """Return submittals for a Procore project."""
    return SubmittalsService(client=client).list_submittals(project_id)


def get_submittal(
    project_id: int,
    submittal_id: int,
    client: ProcoreClient | None = None,
) -> Submittal:
    """Return a single submittal for a Procore project."""
    return SubmittalsService(client=client).get_submittal(project_id, submittal_id)


def download_submittal_attachments(
    project_id: int,
    submittal_id: int,
    destination_dir: Path | str | None = None,
    client: ProcoreClient | None = None,
) -> list[Path]:
    """Download all attachments from a submittal."""
    return SubmittalsService(client=client).download_submittal_attachments(
        project_id,
        submittal_id,
        destination_dir,
    )
