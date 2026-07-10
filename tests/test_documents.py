"""Unit tests for Procore document services and resolvers."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from pyprocore.core.exceptions import MultipleResultsError, NotFoundError, ValidationError
from pyprocore.models import Document, DocumentFolder
from pyprocore.services.documents import (
    DocumentsService,
    download_document,
    get_document,
    get_document_folder,
    list_document_folders,
    list_documents,
)
from pyprocore.services.search import find_document, find_document_folder


class DocumentsServiceTestCase(unittest.TestCase):
    """Validate document services without live Procore access."""

    def test_list_document_folders_uses_endpoint_and_returns_models(self) -> None:
        """Folder listing calls the folders endpoint and returns typed models."""
        client = Mock()
        client.get_all.return_value = [
            {"id": 1, "name": "Drawings", "type": "folder"},
            {"id": 2, "name": "Plan", "type": "file", "filename": "plan.pdf"},
        ]

        result = DocumentsService(client=client).list_document_folders(
            10,
            parent_id=5,
            company_id=123,
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 1)
        self.assertEqual(result[0].name, "Drawings")
        client.get_all.assert_called_once_with(
            "/rest/v1.0/folders",
            params={"project_id": 10, "filters[folder_id]": 5},
            headers={"Procore-Company-Id": "123"},
        )

    def test_get_document_folder_returns_model(self) -> None:
        """Folder retrieval calls the folder endpoint and returns a typed model."""
        client = Mock()
        client.get.return_value = {"id": 5, "name": "Specs"}

        result = DocumentsService(client=client).get_document_folder(10, 5)

        self.assertEqual(result.id, 5)
        self.assertEqual(result.name, "Specs")
        client.get.assert_called_once_with(
            "/rest/v1.0/folders/5",
            params={"project_id": 10},
            headers=None,
        )

    def test_list_documents_uses_endpoint_filters_and_returns_models(self) -> None:
        """Document listing passes folder and extra params through."""
        client = Mock()
        client.get_all.return_value = [
            {
                "folders": [{"id": 8, "name": "Archive", "type": "folder"}],
                "files": [{"id": 7, "name": "Plan", "filename": "plan.pdf"}],
            }
        ]

        result = DocumentsService(client=client).list_documents(
            10,
            folder_id=3,
            params={"per_page": 50},
            sort="name",
        )

        self.assertEqual(result[0].id, 7)
        self.assertEqual(result[0].filename, "plan.pdf")
        client.get_all.assert_called_once_with(
            "/rest/v1.0/folders",
            params={
                "per_page": 50,
                "sort": "name",
                "project_id": 10,
                "filters[folder_id]": 3,
            },
            headers=None,
        )

    def test_get_document_returns_model(self) -> None:
        """Document retrieval calls the files endpoint and returns a typed model."""
        client = Mock()
        client.get.return_value = {"id": 7, "name": "Plan"}

        result = DocumentsService(client=client).get_document(10, 7)

        self.assertEqual(result, Document(id=7, name="Plan"))
        client.get.assert_called_once_with(
            "/rest/v1.0/files/7",
            params={"project_id": 10},
            headers=None,
        )

    def test_list_documents_can_traverse_child_folders_recursively(self) -> None:
        """Recursive document listing follows child folders discovered in payloads."""
        client = Mock()
        client.get_all.side_effect = [
            [{"id": 5, "name": "Drawings", "type": "folder"}],
            [{"id": 7, "name": "Plan", "type": "file", "filename": "plan.pdf"}],
        ]

        result = DocumentsService(client=client).list_documents(10, recursive=True)

        self.assertEqual([document.id for document in result], [7])
        self.assertEqual(client.get_all.call_count, 2)
        self.assertEqual(
            client.get_all.call_args_list[1].kwargs["params"],
            {"project_id": 10, "filters[folder_id]": 5},
        )

    def test_get_document_requires_object_response(self) -> None:
        """Unexpected document payloads fail clearly."""
        client = Mock()
        client.get.return_value = []

        with self.assertRaisesRegex(ValidationError, "document response"):
            DocumentsService(client=client).get_document(10, 7)

    def test_download_document_uses_existing_file_service(self) -> None:
        """Document downloads delegate URL streaming to the shared file service."""
        client = Mock()
        client.get.return_value = {
            "id": 7,
            "name": "Unsafe/Name.pdf",
            "download_url": "https://signed.example/plan.pdf",
        }
        file_service = Mock()
        file_service.download_url.return_value = Path("downloads/Unsafe_Name.pdf")

        result = DocumentsService(client=client, file_service=file_service).download_document(
            10,
            7,
            output_dir="downloads",
            overwrite=True,
        )

        self.assertEqual(result, Path("downloads/Unsafe_Name.pdf"))
        file_service.download_url.assert_called_once_with(
            "https://signed.example/plan.pdf",
            Path("downloads") / "Name.pdf",
            overwrite=True,
        )

    def test_download_document_prefers_explicit_filename(self) -> None:
        """A caller-provided filename overrides document metadata."""
        client = Mock()
        client.get.return_value = {"id": 7, "url": "https://signed.example/file"}
        file_service = Mock()
        file_service.download_url.return_value = Path("downloads/custom.pdf")

        DocumentsService(client=client, file_service=file_service).download_document(
            10,
            7,
            output_dir="downloads",
            filename="custom?.pdf",
        )

        file_service.download_url.assert_called_once_with(
            "https://signed.example/file",
            Path("downloads") / "custom_.pdf",
            overwrite=False,
        )

    def test_download_document_requires_url(self) -> None:
        """Documents without a URL fail before trying to download."""
        client = Mock()
        client.get.return_value = {"id": 7, "name": "Plan"}
        file_service = Mock()

        with self.assertRaisesRegex(ValidationError, "download URL"):
            DocumentsService(client=client, file_service=file_service).download_document(10, 7)

        file_service.download_url.assert_not_called()

    def test_service_functions_delegate_to_service(self) -> None:
        """Module-level helpers preserve the existing service style."""
        with patch("pyprocore.services.documents.DocumentsService") as service_cls:
            service = service_cls.return_value
            service.list_document_folders.return_value = ["folder"]
            service.get_document_folder.return_value = "folder"
            service.list_documents.return_value = ["document"]
            service.get_document.return_value = "document"
            service.download_document.return_value = Path("doc.pdf")

            self.assertEqual(list_document_folders(10, parent_id=1), ["folder"])
            self.assertEqual(get_document_folder(10, 1), "folder")
            self.assertEqual(list_documents(10, folder_id=1), ["document"])
            self.assertEqual(get_document(10, 2), "document")
            self.assertEqual(download_document(10, 2), Path("doc.pdf"))

        service.list_document_folders.assert_called_once_with(
            10,
            parent_id=1,
            params=None,
            company_id=None,
        )
        service.get_document_folder.assert_called_once_with(10, 1, company_id=None)
        service.list_documents.assert_called_once_with(
            10,
            folder_id=1,
            params=None,
            recursive=False,
            company_id=None,
        )
        service.get_document.assert_called_once_with(10, 2, company_id=None)
        service.download_document.assert_called_once()

    def test_positive_ids_are_validated(self) -> None:
        """Document services validate IDs before making requests."""
        service = DocumentsService(client=Mock())

        with self.assertRaises(ValidationError):
            service.list_documents(0)
        with self.assertRaises(ValidationError):
            service.get_document(10, 0)


class DocumentResolverTestCase(unittest.TestCase):
    """Validate human-friendly document resolvers."""

    @patch("pyprocore.services.search.list_document_folders")
    def test_find_document_folder_matches_case_insensitive_name(self, folders: Mock) -> None:
        """Folder resolver supports case-insensitive exact matching."""
        folders.return_value = [DocumentFolder(id=1, name="Drawings")]

        result = find_document_folder(10, "drawings")

        self.assertEqual(result.id, 1)
        folders.assert_called_once_with(10)

    @patch("pyprocore.services.search.list_documents")
    def test_find_document_matches_partial_filename(self, documents: Mock) -> None:
        """Document resolver supports partial filename matching."""
        documents.return_value = [Document(id=1, name="Spec Book", filename="specifications.pdf")]

        result = find_document(10, filename="spec")

        self.assertEqual(result.id, 1)

    @patch("pyprocore.services.search.list_documents")
    def test_find_document_raises_for_no_match(self, documents: Mock) -> None:
        """Document resolver raises the shared not-found exception."""
        documents.return_value = [Document(id=1, name="Plan")]

        with self.assertRaises(NotFoundError):
            find_document(10, name="missing")

    @patch("pyprocore.services.search.list_documents")
    def test_find_document_raises_for_multiple_partial_matches(self, documents: Mock) -> None:
        """Document resolver raises when partial matching is ambiguous."""
        documents.return_value = [
            Document(id=1, name="Plan A"),
            Document(id=2, name="Plan B"),
        ]

        with self.assertRaises(MultipleResultsError):
            find_document(10, name="plan")

    def test_find_document_requires_one_query(self) -> None:
        """Document resolver requires exactly one search field."""
        with self.assertRaises(ValueError):
            find_document(10)
        with self.assertRaises(ValueError):
            find_document(10, name="Plan", filename="plan.pdf")


if __name__ == "__main__":
    unittest.main()
