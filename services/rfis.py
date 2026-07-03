"""RFI service for the Procore SDK."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from core import endpoints
from core.client import ProcoreClient
from core.exceptions import ValidationError
from models import RFI
from services.files import FileDownloadService

DEFAULT_DOWNLOAD_DIR = Path(__file__).resolve().parents[1] / "downloads" / "rfis"


class RFIsService:
    """Service for Procore RFI resources."""

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

    def list_rfis(self, project_id: int) -> list[RFI]:
        """Return RFIs for a Procore project."""
        self._validate_positive_id(project_id, "project_id")

        response = self._client.get_all(endpoints.rfis(project_id))
        if isinstance(response, list):
            return [RFI.model_validate(rfi) for rfi in response]
        return [RFI.model_validate(response)]

    def get_rfi(self, project_id: int, rfi_id: int) -> RFI:
        """Return a single RFI for a Procore project."""
        self._validate_positive_id(project_id, "project_id")
        self._validate_positive_id(rfi_id, "rfi_id")

        response = self._client.get(endpoints.rfi(project_id, rfi_id))
        if not isinstance(response, dict):
            raise ValidationError("Expected Procore RFI response to be an object.")
        return RFI.model_validate(response)

    def download_rfi_attachments(
        self,
        project_id: int,
        rfi_id: int,
        destination_dir: Path | str | None = None,
    ) -> list[Path]:
        """Download all attachments from an RFI's questions.

        RFI attachment URLs are read from ``questions[].attachments[].url``.

        Args:
            project_id: Procore project ID.
            rfi_id: Procore RFI ID.
            destination_dir: Optional directory to save files. Defaults to
                ``downloads/rfis/{rfi_id}``.

        Returns:
            Paths to downloaded files.
        """
        rfi = self.get_rfi(project_id, rfi_id)
        attachments = self._extract_question_attachments(rfi.model_dump())
        output_dir = (
            Path(destination_dir)
            if destination_dir
            else DEFAULT_DOWNLOAD_DIR / str(rfi_id)
        )
        output_dir.mkdir(parents=True, exist_ok=True)

        return self._file_service.download_attachments(
            attachments,
            output_dir,
            fallback_prefix=f"rfi-{rfi_id}",
        )

    @staticmethod
    def _extract_question_attachments(rfi: Mapping[str, Any]) -> list[dict[str, Any]]:
        """Extract ``questions[].attachments[]`` dictionaries from an RFI."""
        questions = rfi.get("questions", [])
        if not isinstance(questions, Sequence) or isinstance(questions, (str, bytes)):
            return []

        attachments: list[dict[str, Any]] = []
        for question in questions:
            if not isinstance(question, Mapping):
                continue

            question_attachments = question.get("attachments", [])
            if not isinstance(question_attachments, Sequence) or isinstance(
                question_attachments,
                (str, bytes),
            ):
                continue

            attachments.extend(
                dict(attachment)
                for attachment in question_attachments
                if isinstance(attachment, Mapping)
            )

        return attachments

    @staticmethod
    def _validate_positive_id(value: int, name: str) -> None:
        """Validate Procore integer identifiers."""
        if value <= 0:
            raise ValidationError(f"{name} must be a positive integer.")


def list_rfis(project_id: int, client: ProcoreClient | None = None) -> list[RFI]:
    """Return RFIs for a Procore project."""
    return RFIsService(client=client).list_rfis(project_id)


def get_rfi(
    project_id: int,
    rfi_id: int,
    client: ProcoreClient | None = None,
) -> RFI:
    """Return a single RFI for a Procore project."""
    return RFIsService(client=client).get_rfi(project_id, rfi_id)


def download_rfi_attachments(
    project_id: int,
    rfi_id: int,
    destination_dir: Path | str | None = None,
    client: ProcoreClient | None = None,
) -> list[Path]:
    """Download all attachments from an RFI's questions."""
    return RFIsService(client=client).download_rfi_attachments(
        project_id,
        rfi_id,
        destination_dir,
    )
