"""Document services for the Procore SDK."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from pyprocore.core import endpoints
from pyprocore.core.client import ProcoreClient
from pyprocore.core.exceptions import ValidationError
from pyprocore.models import Document, DocumentFolder
from pyprocore.services.files import FileDownloadService, sanitize_filename
from pyprocore.services.query_params import build_query_params

DEFAULT_DOWNLOAD_DIR = Path(__file__).resolve().parents[1] / "downloads" / "documents"


class DocumentsService:
    """Service for Procore document and document folder resources."""

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
        self._file_service = file_service

    def list_document_folders(
        self,
        project_id: int,
        parent_id: int | None = None,
        params: Mapping[str, Any] | None = None,
        company_id: int | None = None,
        **extra_params: Any,
    ) -> list[DocumentFolder]:
        """Return document folders for a Procore project.

        Args:
            project_id: Procore project ID.
            parent_id: Optional parent folder ID filter.
            params: Optional additional query parameters.
            company_id: Optional company ID sent as ``Procore-Company-Id``.
            **extra_params: Additional query parameters passed to Procore.

        Returns:
            A list of typed document folder models.
        """
        self._validate_positive_id(project_id, "project_id")
        if parent_id is not None:
            self._validate_positive_id(parent_id, "parent_id")

        query_params = build_query_params(
            params=params,
            extra_params=extra_params,
            project_id=project_id,
            **self._folder_filter(parent_id),
        )
        response = self._client.get_all(
            endpoints.document_folders(project_id),
            params=query_params,
            headers=self._company_headers(company_id),
        )
        return [DocumentFolder.model_validate(folder) for folder in self._extract_folders(response)]

    def get_document_folder(
        self,
        project_id: int,
        folder_id: int,
        *,
        company_id: int | None = None,
    ) -> DocumentFolder:
        """Return one document folder for a Procore project.

        Args:
            project_id: Procore project ID.
            folder_id: Procore document folder ID.
            company_id: Optional company ID sent as ``Procore-Company-Id``.

        Returns:
            The matching typed document folder model.
        """
        self._validate_positive_id(project_id, "project_id")
        self._validate_positive_id(folder_id, "folder_id")

        response = self._client.get(
            endpoints.document_folder(project_id, folder_id),
            params={"project_id": project_id},
            headers=self._company_headers(company_id),
        )
        if not isinstance(response, dict):
            raise ValidationError("Expected Procore document folder response to be an object.")
        return DocumentFolder.model_validate(response)

    def list_documents(
        self,
        project_id: int,
        folder_id: int | None = None,
        params: Mapping[str, Any] | None = None,
        recursive: bool = False,
        company_id: int | None = None,
        **extra_params: Any,
    ) -> list[Document]:
        """Return documents for a Procore project.

        Args:
            project_id: Procore project ID.
            folder_id: Optional document folder ID filter.
            params: Optional additional query parameters.
            recursive: Whether to traverse child folders discovered in the
                initial response.
            company_id: Optional company ID sent as ``Procore-Company-Id``.
            **extra_params: Additional query parameters passed to Procore.

        Returns:
            A list of typed document models.
        """
        self._validate_positive_id(project_id, "project_id")
        if folder_id is not None:
            self._validate_positive_id(folder_id, "folder_id")

        query_params = build_query_params(
            params=params,
            extra_params=extra_params,
            project_id=project_id,
            **self._folder_filter(folder_id),
        )
        response = self._client.get_all(
            endpoints.documents(project_id),
            params=query_params,
            headers=self._company_headers(company_id),
        )
        documents = [
            Document.model_validate(document) for document in self._extract_documents(response)
        ]
        if not recursive:
            return documents

        for folder in self._extract_folders(response):
            nested_folder_id = folder.get("id")
            if isinstance(nested_folder_id, int):
                documents.extend(
                    self.list_documents(
                        project_id,
                        folder_id=nested_folder_id,
                        params=params,
                        recursive=True,
                        company_id=company_id,
                        **extra_params,
                    )
                )
        return documents

    def get_document(
        self,
        project_id: int,
        document_id: int,
        *,
        company_id: int | None = None,
    ) -> Document:
        """Return one document for a Procore project.

        Args:
            project_id: Procore project ID.
            document_id: Procore document ID.
            company_id: Optional company ID sent as ``Procore-Company-Id``.

        Returns:
            The matching typed document model.
        """
        self._validate_positive_id(project_id, "project_id")
        self._validate_positive_id(document_id, "document_id")

        response = self._client.get(
            endpoints.document(project_id, document_id),
            params={"project_id": project_id},
            headers=self._company_headers(company_id),
        )
        if not isinstance(response, dict):
            raise ValidationError("Expected Procore document response to be an object.")
        return Document.model_validate(response)

    def download_document(
        self,
        project_id: int,
        document_id: int,
        output_dir: Path | str = DEFAULT_DOWNLOAD_DIR,
        filename: str | None = None,
        company_id: int | None = None,
        *,
        overwrite: bool = False,
    ) -> Path:
        """Download one Procore document.

        Args:
            project_id: Procore project ID.
            document_id: Procore document ID.
            output_dir: Local folder where the document should be saved.
            filename: Optional local filename. Defaults to document metadata.
            company_id: Optional company ID sent as ``Procore-Company-Id``.
            overwrite: Whether to overwrite an existing file.

        Returns:
            The saved document path.

        Raises:
            ValidationError: If the document payload does not include a
                downloadable URL.
        """
        document = self.get_document(project_id, document_id, company_id=company_id)
        url = self._document_download_url(document)
        if url is None:
            raise ValidationError(
                f"Document {document_id} does not include a download URL or URL. "
                "Procore may require a separate secure file access step before "
                "the SDK can download this file."
            )

        destination = Path(output_dir) / self._document_filename(document, filename)
        return self._download_service.download_url(url, destination, overwrite=overwrite)

    @property
    def _download_service(self) -> FileDownloadService:
        """Return a file service, creating it only when downloads are requested."""
        if self._file_service is None:
            self._file_service = FileDownloadService()
        return self._file_service

    @staticmethod
    def _document_download_url(document: Document) -> str | None:
        """Return the best available document download URL."""
        url = document.download_url or document.url
        if url is None:
            return None
        normalized = str(url).strip()
        return normalized or None

    @staticmethod
    def _document_filename(document: Document, filename: str | None) -> str:
        """Return a safe local filename for a document."""
        for candidate in (filename, document.filename, document.file_name, document.name):
            if candidate is not None and str(candidate).strip():
                return sanitize_filename(str(candidate))
        return sanitize_filename(f"document-{document.id or 'download'}")

    @staticmethod
    def _folder_filter(folder_id: int | None) -> dict[str, int]:
        """Return the Procore folder filter query parameter."""
        return {"filters[folder_id]": folder_id} if folder_id is not None else {}

    @staticmethod
    def _company_headers(company_id: int | None) -> dict[str, str] | None:
        """Return optional Procore company headers for Documents endpoints."""
        if company_id is None:
            return None
        return {"Procore-Company-Id": str(company_id)}

    @classmethod
    def _extract_folders(cls, payload: object) -> list[Mapping[str, Any]]:
        """Extract folder dictionaries from a Procore folders/files payload."""
        items = cls._payload_items(payload)
        explicit = [item for item in items if cls._is_folder_item(item)]
        if explicit:
            return explicit
        return [item for item in items if not cls._is_document_item(item)]

    @classmethod
    def _extract_documents(cls, payload: object) -> list[Mapping[str, Any]]:
        """Extract file/document dictionaries from a Procore folders/files payload."""
        return [item for item in cls._payload_items(payload) if cls._is_document_item(item)]

    @classmethod
    def _payload_items(cls, payload: object) -> list[Mapping[str, Any]]:
        """Flatten common folder/file response shapes into item dictionaries."""
        if isinstance(payload, Mapping):
            items: list[Mapping[str, Any]] = []
            for key in ("folders", "files", "documents", "children", "items"):
                value = payload.get(key)
                if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                    items.extend(item for item in value if isinstance(item, Mapping))
            return items or [payload]
        if isinstance(payload, Sequence) and not isinstance(payload, (str, bytes)):
            items = []
            for item in payload:
                if isinstance(item, Mapping):
                    items.extend(cls._payload_items(item))
            return items
        return []

    @staticmethod
    def _is_folder_item(item: Mapping[str, Any]) -> bool:
        """Return whether a mixed Documents item looks like a folder."""
        type_value = str(item.get("type") or item.get("item_type") or "").casefold()
        if type_value in {"folder", "folders", "document_folder"}:
            return True
        if item.get("is_folder") is True:
            return True
        return "folders" in item or "files" in item

    @staticmethod
    def _is_document_item(item: Mapping[str, Any]) -> bool:
        """Return whether a mixed Documents item looks like a file/document."""
        type_value = str(item.get("type") or item.get("item_type") or "").casefold()
        if type_value in {"file", "document", "documents"}:
            return True
        if item.get("is_file") is True:
            return True
        return any(
            key in item
            for key in (
                "filename",
                "file_name",
                "download_url",
                "url",
                "content_type",
                "file_size",
            )
        )

    @staticmethod
    def _validate_positive_id(value: int, name: str) -> None:
        """Validate Procore integer identifiers."""
        if value <= 0:
            raise ValidationError(f"{name} must be a positive integer.")


def list_document_folders(
    project_id: int,
    parent_id: int | None = None,
    client: ProcoreClient | None = None,
    *,
    params: Mapping[str, Any] | None = None,
    company_id: int | None = None,
    **extra_params: Any,
) -> list[DocumentFolder]:
    """Return document folders for a Procore project."""
    return DocumentsService(client=client).list_document_folders(
        project_id,
        parent_id=parent_id,
        params=params,
        company_id=company_id,
        **extra_params,
    )


def get_document_folder(
    project_id: int,
    folder_id: int,
    client: ProcoreClient | None = None,
    *,
    company_id: int | None = None,
) -> DocumentFolder:
    """Return one document folder for a Procore project."""
    return DocumentsService(client=client).get_document_folder(
        project_id,
        folder_id,
        company_id=company_id,
    )


def list_documents(
    project_id: int,
    folder_id: int | None = None,
    client: ProcoreClient | None = None,
    *,
    params: Mapping[str, Any] | None = None,
    recursive: bool = False,
    company_id: int | None = None,
    **extra_params: Any,
) -> list[Document]:
    """Return documents for a Procore project."""
    return DocumentsService(client=client).list_documents(
        project_id,
        folder_id=folder_id,
        params=params,
        recursive=recursive,
        company_id=company_id,
        **extra_params,
    )


def get_document(
    project_id: int,
    document_id: int,
    client: ProcoreClient | None = None,
    *,
    company_id: int | None = None,
) -> Document:
    """Return one document for a Procore project."""
    return DocumentsService(client=client).get_document(
        project_id,
        document_id,
        company_id=company_id,
    )


def download_document(
    project_id: int,
    document_id: int,
    output_dir: Path | str = DEFAULT_DOWNLOAD_DIR,
    filename: str | None = None,
    client: ProcoreClient | None = None,
    company_id: int | None = None,
    *,
    overwrite: bool = False,
) -> Path:
    """Download one Procore document."""
    return DocumentsService(client=client).download_document(
        project_id,
        document_id,
        output_dir=output_dir,
        filename=filename,
        company_id=company_id,
        overwrite=overwrite,
    )
