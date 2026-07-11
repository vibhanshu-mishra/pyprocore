"""Unit tests for the object-oriented Procore client interface."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from pyprocore import Procore
from pyprocore.automation import AutomationInput
from pyprocore.client import (
    AutomationClient,
    CompaniesClient,
    DailyLogsClient,
    DocumentsClient,
    DrawingsClient,
    PhotosClient,
    ProjectsClient,
    RFIsClient,
    SpecificationsClient,
    SubmittalsClient,
    WorkflowsClient,
)
from pyprocore.core.exceptions import ValidationError


class ProcoreObjectClientTestCase(unittest.TestCase):
    """Validate grouped service clients and delegation behavior."""

    def test_root_import_and_grouped_clients_exist(self) -> None:
        """The package root exports Procore with expected grouped clients."""
        client = Procore()

        self.assertIsInstance(client.companies, CompaniesClient)
        self.assertIsInstance(client.daily_logs, DailyLogsClient)
        self.assertIsInstance(client.projects, ProjectsClient)
        self.assertIsInstance(client.rfis, RFIsClient)
        self.assertIsInstance(client.submittals, SubmittalsClient)
        self.assertIsInstance(client.documents, DocumentsClient)
        self.assertIsInstance(client.drawings, DrawingsClient)
        self.assertIsInstance(client.specifications, SpecificationsClient)
        self.assertIsInstance(client.photos, PhotosClient)
        self.assertIsInstance(client.automation, AutomationClient)
        self.assertIsInstance(client.workflows, WorkflowsClient)

    @patch("pyprocore.client.list_companies")
    def test_companies_list_delegates_to_service(self, list_companies: Mock) -> None:
        """Company listing delegates to the existing service function."""
        list_companies.return_value = ["company"]

        result = Procore().companies.list()

        self.assertEqual(result, ["company"])
        list_companies.assert_called_once_with()

    @patch("pyprocore.client.find_company")
    def test_companies_find_delegates_to_resolver(self, find_company: Mock) -> None:
        """Company lookup delegates to the existing resolver."""
        find_company.return_value = "company"

        result = Procore().companies.find("Tracker")

        self.assertEqual(result, "company")
        find_company.assert_called_once_with("Tracker")

    @patch("pyprocore.client.list_projects")
    def test_projects_list_delegates_with_company_id(self, list_projects: Mock) -> None:
        """Project listing passes the company ID to the existing service."""
        list_projects.return_value = ["project"]

        result = Procore().projects.list(company_id=123)

        self.assertEqual(result, ["project"])
        list_projects.assert_called_once_with(company_id=123)

    @patch("pyprocore.client.get_settings")
    @patch("pyprocore.client.list_projects")
    def test_projects_list_uses_configured_company_id(
        self,
        list_projects: Mock,
        get_settings: Mock,
    ) -> None:
        """Project listing can default to PROCORE_COMPANY_ID."""
        get_settings.return_value.company_id = 456
        list_projects.return_value = ["project"]

        result = Procore().projects.list()

        self.assertEqual(result, ["project"])
        list_projects.assert_called_once_with(company_id=456)

    @patch("pyprocore.client.get_project")
    def test_projects_get_delegates_to_service(self, get_project: Mock) -> None:
        """Project retrieval delegates to the existing service."""
        get_project.return_value = "project"

        result = Procore().projects.get(project_id=99)

        self.assertEqual(result, "project")
        get_project.assert_called_once_with(project_id=99)

    @patch("pyprocore.client.find_project")
    def test_projects_find_delegates_to_resolver(self, find_project: Mock) -> None:
        """Project lookup passes name, number, and company ID to the resolver."""
        find_project.return_value = "project"

        result = Procore().projects.find(name="Hospital", number=None, company_id=123)

        self.assertEqual(result, "project")
        find_project.assert_called_once_with(name="Hospital", number=None, company_id=123)

    @patch("pyprocore.client.find_project_contains")
    def test_projects_find_contains_delegates_to_resolver(
        self,
        find_project_contains: Mock,
    ) -> None:
        """Project contains search delegates to the existing resolver."""
        find_project_contains.return_value = "project"

        result = Procore().projects.find_contains("Hospital", company_id=123)

        self.assertEqual(result, "project")
        find_project_contains.assert_called_once_with("Hospital", company_id=123)

    @patch("pyprocore.client.list_rfis")
    def test_rfis_list_delegates_to_service(self, list_rfis: Mock) -> None:
        """RFI listing delegates to the existing service."""
        list_rfis.return_value = ["rfi"]

        result = Procore().rfis.list(project_id=352338)

        self.assertEqual(result, ["rfi"])
        list_rfis.assert_called_once_with(
            project_id=352338,
            status=None,
            updated_after=None,
            updated_before=None,
            created_after=None,
            created_before=None,
            params=None,
        )

    @patch("pyprocore.client.list_rfis")
    def test_rfis_list_passes_filter_args(self, list_rfis: Mock) -> None:
        """RFI listing passes filter arguments to the service function."""
        list_rfis.return_value = ["rfi"]

        result = Procore().rfis.list(
            project_id=352338,
            status="open",
            updated_after="2026-07-01",
            params={"per_page": 100},
            sort="number",
        )

        self.assertEqual(result, ["rfi"])
        list_rfis.assert_called_once_with(
            project_id=352338,
            status="open",
            updated_after="2026-07-01",
            updated_before=None,
            created_after=None,
            created_before=None,
            params={"per_page": 100},
            sort="number",
        )

    @patch("pyprocore.client.get_rfi")
    def test_rfis_get_delegates_to_service(self, get_rfi: Mock) -> None:
        """RFI retrieval delegates to the existing service."""
        get_rfi.return_value = "rfi"

        result = Procore().rfis.get(project_id=352338, rfi_id=102784)

        self.assertEqual(result, "rfi")
        get_rfi.assert_called_once_with(project_id=352338, rfi_id=102784)

    @patch("pyprocore.client.find_rfi")
    def test_rfis_find_delegates_to_resolver(self, find_rfi: Mock) -> None:
        """RFI lookup delegates to the existing resolver."""
        find_rfi.return_value = "rfi"

        result = Procore().rfis.find(project_id=352338, number="15")

        self.assertEqual(result, "rfi")
        find_rfi.assert_called_once_with(project_id=352338, number="15")

    @patch("pyprocore.client.download_rfi_attachments")
    def test_rfis_download_attachments_delegates_to_service(
        self,
        download_rfi_attachments: Mock,
    ) -> None:
        """RFI attachment downloads pass output and overwrite options through."""
        download_rfi_attachments.return_value = [Path("rfi.pdf")]

        result = Procore().rfis.download_attachments(
            project_id=352338,
            rfi_id=102784,
            output_dir="downloads/rfis",
            overwrite=True,
        )

        self.assertEqual(result, [Path("rfi.pdf")])
        download_rfi_attachments.assert_called_once_with(
            project_id=352338,
            rfi_id=102784,
            destination_dir="downloads/rfis",
            overwrite=True,
        )

    @patch("pyprocore.client.list_submittals")
    def test_submittals_list_delegates_to_service(self, list_submittals: Mock) -> None:
        """Submittal listing delegates to the existing service."""
        list_submittals.return_value = ["submittal"]

        result = Procore().submittals.list(project_id=352338)

        self.assertEqual(result, ["submittal"])
        list_submittals.assert_called_once_with(
            project_id=352338,
            status=None,
            updated_after=None,
            updated_before=None,
            created_after=None,
            created_before=None,
            params=None,
        )

    @patch("pyprocore.client.list_submittals")
    def test_submittals_list_passes_filter_args(self, list_submittals: Mock) -> None:
        """Submittal listing passes filter arguments to the service function."""
        list_submittals.return_value = ["submittal"]

        result = Procore().submittals.list(
            project_id=352338,
            status="pending",
            updated_after="2026-07-01",
            params={"per_page": 100},
            sort="number",
        )

        self.assertEqual(result, ["submittal"])
        list_submittals.assert_called_once_with(
            project_id=352338,
            status="pending",
            updated_after="2026-07-01",
            updated_before=None,
            created_after=None,
            created_before=None,
            params={"per_page": 100},
            sort="number",
        )

    @patch("pyprocore.client.get_submittal")
    def test_submittals_get_delegates_to_service(self, get_submittal: Mock) -> None:
        """Submittal retrieval delegates to the existing service."""
        get_submittal.return_value = "submittal"

        result = Procore().submittals.get(project_id=352338, submittal_id=309641)

        self.assertEqual(result, "submittal")
        get_submittal.assert_called_once_with(project_id=352338, submittal_id=309641)

    @patch("pyprocore.client.find_submittal")
    def test_submittals_find_delegates_to_resolver(self, find_submittal: Mock) -> None:
        """Submittal lookup delegates to the existing resolver."""
        find_submittal.return_value = "submittal"

        result = Procore().submittals.find(project_id=352338, number="27")

        self.assertEqual(result, "submittal")
        find_submittal.assert_called_once_with(project_id=352338, number="27")

    @patch("pyprocore.client.download_submittal_attachments")
    def test_submittals_download_attachments_delegates_to_service(
        self,
        download_submittal_attachments: Mock,
    ) -> None:
        """Submittal downloads pass output and overwrite options through."""
        download_submittal_attachments.return_value = [Path("submittal.pdf")]

        result = Procore().submittals.download_attachments(
            project_id=352338,
            submittal_id=309641,
            output_dir="downloads/submittals",
            overwrite=True,
        )

        self.assertEqual(result, [Path("submittal.pdf")])
        download_submittal_attachments.assert_called_once_with(
            project_id=352338,
            submittal_id=309641,
            destination_dir="downloads/submittals",
            overwrite=True,
        )

    @patch("pyprocore.client.list_document_folders")
    def test_documents_list_folders_delegates_to_service(
        self,
        list_document_folders: Mock,
    ) -> None:
        """Document folder listing delegates to the document service."""
        list_document_folders.return_value = ["folder"]

        result = Procore().documents.list_folders(
            project_id=352338,
            parent_id=10,
            params={"per_page": 100},
            company_id=123,
            sort="name",
        )

        self.assertEqual(result, ["folder"])
        list_document_folders.assert_called_once_with(
            project_id=352338,
            parent_id=10,
            params={"per_page": 100},
            company_id=123,
            sort="name",
        )

    @patch("pyprocore.client.get_document_folder")
    def test_documents_get_folder_delegates_to_service(
        self,
        get_document_folder: Mock,
    ) -> None:
        """Document folder retrieval delegates to the document service."""
        get_document_folder.return_value = "folder"

        result = Procore().documents.get_folder(
            project_id=352338,
            folder_id=10,
            company_id=123,
        )

        self.assertEqual(result, "folder")
        get_document_folder.assert_called_once_with(
            project_id=352338,
            folder_id=10,
            company_id=123,
        )

    @patch("pyprocore.client.find_document_folder")
    def test_documents_find_folder_delegates_to_resolver(
        self,
        find_document_folder: Mock,
    ) -> None:
        """Document folder lookup delegates to the resolver."""
        find_document_folder.return_value = "folder"

        result = Procore().documents.find_folder(project_id=352338, name="Drawings")

        self.assertEqual(result, "folder")
        find_document_folder.assert_called_once_with(project_id=352338, name="Drawings")

    @patch("pyprocore.client.list_documents")
    def test_documents_list_delegates_to_service(self, list_documents: Mock) -> None:
        """Document listing delegates to the document service."""
        list_documents.return_value = ["document"]

        result = Procore().documents.list(
            project_id=352338,
            folder_id=10,
            params={"per_page": 100},
            recursive=True,
            company_id=123,
            sort="name",
        )

        self.assertEqual(result, ["document"])
        list_documents.assert_called_once_with(
            project_id=352338,
            folder_id=10,
            params={"per_page": 100},
            recursive=True,
            company_id=123,
            sort="name",
        )

    @patch("pyprocore.client.get_document")
    def test_documents_get_delegates_to_service(self, get_document: Mock) -> None:
        """Document retrieval delegates to the document service."""
        get_document.return_value = "document"

        result = Procore().documents.get(project_id=352338, document_id=99, company_id=123)

        self.assertEqual(result, "document")
        get_document.assert_called_once_with(
            project_id=352338,
            document_id=99,
            company_id=123,
        )

    @patch("pyprocore.client.find_document")
    def test_documents_find_delegates_to_resolver(self, find_document: Mock) -> None:
        """Document lookup delegates to the resolver."""
        find_document.return_value = "document"

        result = Procore().documents.find(project_id=352338, filename="plan.pdf")

        self.assertEqual(result, "document")
        find_document.assert_called_once_with(
            project_id=352338,
            name=None,
            filename="plan.pdf",
        )

    @patch("pyprocore.client.download_document")
    def test_documents_download_delegates_to_service(self, download_document: Mock) -> None:
        """Document downloads pass output and overwrite options through."""
        download_document.return_value = Path("document.pdf")

        result = Procore().documents.download(
            project_id=352338,
            document_id=99,
            output_dir="downloads/documents",
            filename="plan.pdf",
            company_id=123,
            overwrite=True,
        )

        self.assertEqual(result, Path("document.pdf"))
        download_document.assert_called_once_with(
            project_id=352338,
            document_id=99,
            output_dir="downloads/documents",
            filename="plan.pdf",
            company_id=123,
            overwrite=True,
        )

    @patch("pyprocore.client.list_drawing_areas")
    def test_drawings_list_areas_delegates_to_service(
        self,
        list_drawing_areas: Mock,
    ) -> None:
        """Drawing area listing delegates to the drawing service."""
        list_drawing_areas.return_value = ["area"]

        result = Procore().drawings.list_areas(352338, company_id=123, sort="name")

        self.assertEqual(result, ["area"])
        list_drawing_areas.assert_called_once_with(352338, company_id=123, sort="name")

    @patch("pyprocore.client.get_drawing_area")
    def test_drawings_get_area_delegates_to_service(self, get_drawing_area: Mock) -> None:
        """Drawing area retrieval delegates to the drawing service."""
        get_drawing_area.return_value = "area"

        result = Procore().drawings.get_area(352338, 10, company_id=123)

        self.assertEqual(result, "area")
        get_drawing_area.assert_called_once_with(352338, 10, company_id=123)

    @patch("pyprocore.client.list_drawing_disciplines")
    def test_drawings_list_disciplines_delegates_to_service(
        self,
        list_drawing_disciplines: Mock,
    ) -> None:
        """Drawing discipline listing delegates to the drawing service."""
        list_drawing_disciplines.return_value = ["discipline"]

        result = Procore().drawings.list_disciplines(352338, company_id=123)

        self.assertEqual(result, ["discipline"])
        list_drawing_disciplines.assert_called_once_with(352338, company_id=123)

    @patch("pyprocore.client.list_drawings")
    def test_drawings_list_delegates_to_service(self, list_drawings: Mock) -> None:
        """Drawing listing delegates to the drawing service."""
        list_drawings.return_value = ["drawing"]

        result = Procore().drawings.list(
            352338,
            company_id=123,
            drawing_area_id=5,
            discipline_id=6,
            current=True,
            sort="number",
        )

        self.assertEqual(result, ["drawing"])
        list_drawings.assert_called_once_with(
            352338,
            company_id=123,
            drawing_area_id=5,
            discipline_id=6,
            current=True,
            sort="number",
        )

    @patch("pyprocore.client.get_drawing")
    def test_drawings_get_delegates_to_service(self, get_drawing: Mock) -> None:
        """Drawing retrieval delegates to the drawing service."""
        get_drawing.return_value = "drawing"

        result = Procore().drawings.get(352338, 99, company_id=123, drawing_area_id=5)

        self.assertEqual(result, "drawing")
        get_drawing.assert_called_once_with(
            352338,
            99,
            company_id=123,
            drawing_area_id=5,
        )

    @patch("pyprocore.client.find_drawing")
    def test_drawings_find_delegates_to_resolver(self, find_drawing: Mock) -> None:
        """Drawing lookup delegates to the drawing resolver."""
        find_drawing.return_value = "drawing"

        result = Procore().drawings.find(352338, number="S-101", company_id=123)

        self.assertEqual(result, "drawing")
        find_drawing.assert_called_once_with(
            352338,
            number="S-101",
            title=None,
            company_id=123,
        )

    @patch("pyprocore.client.find_drawings_contains")
    def test_drawings_find_contains_delegates_to_resolver(
        self,
        find_drawings_contains: Mock,
    ) -> None:
        """Drawing contains search delegates to the drawing resolver."""
        find_drawings_contains.return_value = ["drawing"]

        result = Procore().drawings.find_contains(352338, "stair", company_id=123)

        self.assertEqual(result, ["drawing"])
        find_drawings_contains.assert_called_once_with(352338, "stair", company_id=123)

    @patch("pyprocore.client.download_drawing")
    def test_drawings_download_delegates_to_service(self, download_drawing: Mock) -> None:
        """Drawing downloads pass output and overwrite options through."""
        download_drawing.return_value = Path("drawing.pdf")

        result = Procore().drawings.download(
            352338,
            99,
            output_dir="downloads/drawings",
            filename="S-101.pdf",
            company_id=123,
            overwrite=True,
            drawing_area_id=5,
        )

        self.assertEqual(result, Path("drawing.pdf"))
        download_drawing.assert_called_once_with(
            352338,
            99,
            output_dir="downloads/drawings",
            filename="S-101.pdf",
            overwrite=True,
            company_id=123,
            drawing_area_id=5,
        )

    @patch("pyprocore.client.list_photo_albums")
    def test_photos_list_albums_delegates_to_service(self, list_photo_albums: Mock) -> None:
        """Photo album listing delegates to the service."""
        list_photo_albums.return_value = ["album"]

        result = Procore().photos.list_albums(352338, company_id=123, per_page=50)

        self.assertEqual(result, ["album"])
        list_photo_albums.assert_called_once_with(352338, company_id=123, per_page=50)

    @patch("pyprocore.client.get_photo_album")
    def test_photos_get_album_delegates_to_service(self, get_photo_album: Mock) -> None:
        """Photo album retrieval delegates to the service."""
        get_photo_album.return_value = "album"

        result = Procore().photos.get_album(352338, 7, company_id=123)

        self.assertEqual(result, "album")
        get_photo_album.assert_called_once_with(352338, 7, company_id=123)

    @patch("pyprocore.client.find_photo_album")
    def test_photos_find_album_delegates_to_service(self, find_photo_album: Mock) -> None:
        """Photo album lookup delegates to the service."""
        find_photo_album.return_value = "album"

        result = Procore().photos.find_album(352338, name="Progress", company_id=123)

        self.assertEqual(result, "album")
        find_photo_album.assert_called_once_with(352338, name="Progress", company_id=123)

    @patch("pyprocore.client.list_photos")
    def test_photos_list_delegates_to_service(self, list_photos: Mock) -> None:
        """Photo listing delegates to the service."""
        list_photos.return_value = ["photo"]

        result = Procore().photos.list(352338, company_id=123, album_id=7, sort="-created_at")

        self.assertEqual(result, ["photo"])
        list_photos.assert_called_once_with(
            352338,
            company_id=123,
            album_id=7,
            sort="-created_at",
        )

    @patch("pyprocore.client.get_photo")
    def test_photos_get_delegates_to_service(self, get_photo: Mock) -> None:
        """Photo retrieval delegates to the service."""
        get_photo.return_value = "photo"

        result = Procore().photos.get(352338, 9, company_id=123)

        self.assertEqual(result, "photo")
        get_photo.assert_called_once_with(352338, 9, company_id=123)

    @patch("pyprocore.client.find_photo")
    def test_photos_find_delegates_to_service(self, find_photo: Mock) -> None:
        """Photo lookup delegates to the service."""
        find_photo.return_value = "photo"

        result = Procore().photos.find(352338, filename="site.jpg", company_id=123)

        self.assertEqual(result, "photo")
        find_photo.assert_called_once_with(
            352338,
            photo_id=None,
            filename="site.jpg",
            description=None,
            query=None,
            company_id=123,
        )

    @patch("pyprocore.client.download_photo")
    def test_photos_download_delegates_to_service(self, download_photo: Mock) -> None:
        """Photo downloads delegate to the service."""
        download_photo.return_value = Path("photo.jpg")

        result = Procore().photos.download(
            352338,
            9,
            output_dir="downloads/photos",
            company_id=123,
            overwrite=True,
            filename="site.jpg",
        )

        self.assertEqual(result, Path("photo.jpg"))
        download_photo.assert_called_once_with(
            352338,
            9,
            output_dir="downloads/photos",
            company_id=123,
            overwrite=True,
            filename="site.jpg",
        )

    @patch("pyprocore.client.download_photo_album")
    def test_photos_download_album_delegates_to_service(
        self,
        download_photo_album: Mock,
    ) -> None:
        """Photo album downloads delegate to the service."""
        download_photo_album.return_value = "summary"

        result = Procore().photos.download_album(
            352338,
            7,
            output_dir="downloads/photos",
            company_id=123,
            overwrite=True,
            limit=10,
        )

        self.assertEqual(result, "summary")
        download_photo_album.assert_called_once_with(
            352338,
            7,
            output_dir="downloads/photos",
            company_id=123,
            overwrite=True,
            limit=10,
        )

    @patch("pyprocore.client.get_daily_log_counts")
    def test_daily_logs_counts_delegates_to_service(self, get_daily_log_counts: Mock) -> None:
        """Daily Log counts delegate to the service."""
        get_daily_log_counts.return_value = ["count"]

        result = Procore().daily_logs.counts(352338, company_id=123, log_date="2026-07-10")

        self.assertEqual(result, ["count"])
        get_daily_log_counts.assert_called_once_with(
            352338,
            company_id=123,
            log_date="2026-07-10",
        )

    @patch("pyprocore.client.list_daily_log_headers")
    def test_daily_logs_headers_delegates_to_service(self, list_daily_log_headers: Mock) -> None:
        """Daily Log headers delegate to the service."""
        list_daily_log_headers.return_value = ["header"]

        result = Procore().daily_logs.headers(352338, company_id=123)

        self.assertEqual(result, ["header"])
        list_daily_log_headers.assert_called_once_with(352338, company_id=123)

    @patch("pyprocore.client.list_daily_logs")
    def test_daily_logs_list_delegates_to_service(self, list_daily_logs: Mock) -> None:
        """Generic Daily Log listing delegates to the service."""
        list_daily_logs.return_value = ["entry"]

        result = Procore().daily_logs.list(352338, "manpower", company_id=123)

        self.assertEqual(result, ["entry"])
        list_daily_logs.assert_called_once_with(352338, "manpower", company_id=123)

    @patch("pyprocore.client.list_daily_logs_for_date")
    def test_daily_logs_list_for_date_delegates_to_service(
        self,
        list_daily_logs_for_date: Mock,
    ) -> None:
        """Daily Log date aggregate delegates to the service."""
        list_daily_logs_for_date.return_value = "summary"

        result = Procore().daily_logs.list_for_date(
            352338,
            company_id=123,
            log_date="2026-07-10",
            log_types=["manpower"],
        )

        self.assertEqual(result, "summary")
        list_daily_logs_for_date.assert_called_once_with(
            352338,
            company_id=123,
            log_date="2026-07-10",
            log_types=["manpower"],
        )

    @patch("pyprocore.client.list_manpower_logs")
    def test_daily_logs_manpower_delegates_to_service(self, list_manpower_logs: Mock) -> None:
        """Daily Log convenience methods delegate to the service."""
        list_manpower_logs.return_value = ["entry"]

        result = Procore().daily_logs.manpower(352338, company_id=123)

        self.assertEqual(result, ["entry"])
        list_manpower_logs.assert_called_once_with(352338, company_id=123)

    @patch("pyprocore.client.list_specification_sets")
    def test_specifications_list_sets_delegates_to_service(
        self,
        list_specification_sets: Mock,
    ) -> None:
        """Specification set listing delegates to the service."""
        list_specification_sets.return_value = ["set"]

        result = Procore().specifications.list_sets(352338, company_id=123, sort="name")

        self.assertEqual(result, ["set"])
        list_specification_sets.assert_called_once_with(352338, company_id=123, sort="name")

    @patch("pyprocore.client.list_specification_sections")
    def test_specifications_list_sections_delegates_to_service(
        self,
        list_specification_sections: Mock,
    ) -> None:
        """Specification section listing delegates to the service."""
        list_specification_sections.return_value = ["section"]

        result = Procore().specifications.list_sections(
            352338,
            company_id=123,
            specification_set_id=7,
            sort="number",
        )

        self.assertEqual(result, ["section"])
        list_specification_sections.assert_called_once_with(
            352338,
            company_id=123,
            specification_area_id=None,
            specification_set_id=7,
            division_id=None,
            sort="number",
        )

    @patch("pyprocore.client.get_specification_section")
    def test_specifications_get_section_delegates_to_service(
        self,
        get_specification_section: Mock,
    ) -> None:
        """Specification section retrieval delegates to the service."""
        get_specification_section.return_value = "section"

        result = Procore().specifications.get_section(352338, 10, company_id=123)

        self.assertEqual(result, "section")
        get_specification_section.assert_called_once_with(352338, 10, company_id=123)

    @patch("pyprocore.client.find_specification_section")
    def test_specifications_find_section_delegates_to_service(
        self,
        find_specification_section: Mock,
    ) -> None:
        """Specification section lookup delegates to the service."""
        find_specification_section.return_value = "section"

        result = Procore().specifications.find_section(
            352338,
            number="03 3000",
            company_id=123,
        )

        self.assertEqual(result, "section")
        find_specification_section.assert_called_once_with(
            352338,
            number="03 3000",
            title=None,
            query=None,
            company_id=123,
        )

    @patch("pyprocore.client.list_specification_section_revisions")
    def test_specifications_list_revisions_delegates_to_service(
        self,
        list_specification_section_revisions: Mock,
    ) -> None:
        """Specification revision listing delegates to the service."""
        list_specification_section_revisions.return_value = ["revision"]

        result = Procore().specifications.list_revisions(
            352338,
            company_id=123,
            specification_section_id=10,
            per_page=1000,
        )

        self.assertEqual(result, ["revision"])
        list_specification_section_revisions.assert_called_once_with(
            352338,
            company_id=123,
            specification_section_id=10,
            page=None,
            per_page=1000,
        )

    @patch("pyprocore.client.get_specification_section_revision")
    def test_specifications_get_revision_delegates_to_service(
        self,
        get_specification_section_revision: Mock,
    ) -> None:
        """Specification revision retrieval delegates to the service."""
        get_specification_section_revision.return_value = "revision"

        result = Procore().specifications.get_revision(352338, 20, company_id=123)

        self.assertEqual(result, "revision")
        get_specification_section_revision.assert_called_once_with(
            352338,
            20,
            company_id=123,
        )

    @patch("pyprocore.client.download_specification_section_revision")
    def test_specifications_download_revision_delegates_to_service(
        self,
        download_specification_section_revision: Mock,
    ) -> None:
        """Specification revision downloads delegate to the service."""
        download_specification_section_revision.return_value = Path("spec.pdf")

        result = Procore().specifications.download_revision(
            352338,
            20,
            output_dir="downloads/specifications",
            company_id=123,
            overwrite=True,
        )

        self.assertEqual(result, Path("spec.pdf"))
        download_specification_section_revision.assert_called_once_with(
            352338,
            20,
            output_dir="downloads/specifications",
            company_id=123,
            overwrite=True,
        )

    @patch("pyprocore.client.build_workflow_package")
    def test_automation_build_package_delegates_to_builder(
        self,
        build_workflow_package: Mock,
    ) -> None:
        """Automation package wrapper delegates to the existing builder."""
        input_data = AutomationInput(project_id=1, item_type="rfi", item_id=2)
        build_workflow_package.return_value = "package"

        result = Procore().automation.build_package(input_data)

        self.assertEqual(result, "package")
        build_workflow_package.assert_called_once_with(input_data)

    @patch("pyprocore.client.build_workflow_package")
    def test_automation_build_package_accepts_keyword_input(
        self,
        build_workflow_package: Mock,
    ) -> None:
        """Automation package wrapper can build input from keyword arguments."""
        build_workflow_package.return_value = "package"

        result = Procore().automation.build_package(
            project_id=1,
            item_type="rfi",
            item_id=2,
            download_attachments=False,
        )

        self.assertEqual(result, "package")
        input_data = build_workflow_package.call_args.args[0]
        self.assertEqual(input_data.project_id, 1)
        self.assertEqual(input_data.item_type, "rfi")
        self.assertEqual(input_data.item_id, 2)
        self.assertFalse(input_data.download_attachments)

    def test_automation_build_package_requires_item_type_for_keyword_input(self) -> None:
        """Keyword-style automation package input requires an item type."""
        with self.assertRaises(ValidationError):
            Procore().automation.build_package(project_id=1, item_id=2)

    @patch("pyprocore.client.build_rfi_package")
    def test_automation_build_rfi_package_delegates_to_builder(
        self,
        build_rfi_package: Mock,
    ) -> None:
        """RFI automation package wrapper passes options through."""
        build_rfi_package.return_value = "package"

        result = Procore().automation.build_rfi_package(
            project_id=1,
            number="15",
            output_dir=Path("out"),
            download_attachments=False,
        )

        self.assertEqual(result, "package")
        build_rfi_package.assert_called_once_with(
            company_id=None,
            project_id=1,
            project_name=None,
            project_number=None,
            rfi_id=None,
            number="15",
            download_attachments=False,
            output_dir=Path("out"),
        )

    @patch("pyprocore.client.build_submittal_package")
    def test_automation_build_submittal_package_delegates_to_builder(
        self,
        build_submittal_package: Mock,
    ) -> None:
        """Submittal automation package wrapper passes options through."""
        build_submittal_package.return_value = "package"

        result = Procore().automation.build_submittal_package(project_id=1, submittal_id=2)

        self.assertEqual(result, "package")
        build_submittal_package.assert_called_once_with(
            company_id=None,
            project_id=1,
            project_name=None,
            project_number=None,
            submittal_id=2,
            number=None,
            download_attachments=True,
            output_dir=None,
        )

    @patch("pyprocore.client.export_rfis_to_csv")
    def test_workflows_export_rfis_delegates_to_helper(self, export_rfis_to_csv: Mock) -> None:
        """Workflow RFI CSV exports delegate to the workflow helper."""
        export_rfis_to_csv.return_value = Path("rfis.csv")

        result = Procore().workflows.export_rfis_to_csv(
            1,
            "rfis.csv",
            status="open",
            params={"per_page": 100},
        )

        self.assertEqual(result, Path("rfis.csv"))
        export_rfis_to_csv.assert_called_once_with(
            1,
            "rfis.csv",
            status="open",
            updated_after=None,
            updated_before=None,
            created_after=None,
            created_before=None,
            params={"per_page": 100},
        )

    @patch("pyprocore.client.export_submittals_to_csv")
    def test_workflows_export_submittals_delegates_to_helper(
        self,
        export_submittals_to_csv: Mock,
    ) -> None:
        """Workflow submittal CSV exports delegate to the workflow helper."""
        export_submittals_to_csv.return_value = Path("submittals.csv")

        result = Procore().workflows.export_submittals_to_csv(1, "submittals.csv")

        self.assertEqual(result, Path("submittals.csv"))
        export_submittals_to_csv.assert_called_once()

    @patch("pyprocore.client.export_rfis_to_jsonl")
    def test_workflows_export_rfis_jsonl_delegates_to_helper(
        self,
        export_rfis_to_jsonl: Mock,
    ) -> None:
        """Workflow RFI JSONL exports delegate to the workflow helper."""
        export_rfis_to_jsonl.return_value = Path("rfis.jsonl")

        result = Procore().workflows.export_rfis_to_jsonl(1, "rfis.jsonl", status="open")

        self.assertEqual(result, Path("rfis.jsonl"))
        export_rfis_to_jsonl.assert_called_once_with(1, "rfis.jsonl", status="open")

    @patch("pyprocore.client.export_submittals_to_jsonl")
    def test_workflows_export_submittals_jsonl_delegates_to_helper(
        self,
        export_submittals_to_jsonl: Mock,
    ) -> None:
        """Workflow submittal JSONL exports delegate to the workflow helper."""
        export_submittals_to_jsonl.return_value = Path("submittals.jsonl")

        result = Procore().workflows.export_submittals_to_jsonl(
            1,
            "submittals.jsonl",
            status="pending",
        )

        self.assertEqual(result, Path("submittals.jsonl"))
        export_submittals_to_jsonl.assert_called_once_with(
            1,
            "submittals.jsonl",
            status="pending",
        )

    @patch("pyprocore.client.sync_rfis_to_folder")
    def test_workflows_sync_rfis_delegates_to_helper(self, sync_rfis_to_folder: Mock) -> None:
        """Workflow RFI sync delegates to the workflow helper."""
        sync_rfis_to_folder.return_value = "result"

        result = Procore().workflows.sync_rfis_to_folder(
            1,
            "out",
            status="open",
            download_attachments=False,
        )

        self.assertEqual(result, "result")
        sync_rfis_to_folder.assert_called_once_with(
            1,
            "out",
            status="open",
            download_attachments=False,
            overwrite=False,
            create_tracker=True,
            create_markdown=True,
            dry_run=False,
            incremental=False,
        )

    @patch("pyprocore.client.sync_submittals_to_folder")
    def test_workflows_sync_submittals_delegates_to_helper(
        self,
        sync_submittals_to_folder: Mock,
    ) -> None:
        """Workflow submittal sync delegates to the workflow helper."""
        sync_submittals_to_folder.return_value = "result"

        result = Procore().workflows.sync_submittals_to_folder(1, "out", overwrite=True)

        self.assertEqual(result, "result")
        sync_submittals_to_folder.assert_called_once_with(
            1,
            "out",
            status=None,
            download_attachments=True,
            overwrite=True,
            create_tracker=True,
            create_markdown=True,
            dry_run=False,
            incremental=False,
        )

    @patch("pyprocore.client.sync_documents_to_folder")
    def test_workflows_sync_documents_delegates_to_helper(
        self,
        sync_documents_to_folder: Mock,
    ) -> None:
        """Workflow document sync delegates to the workflow helper."""
        sync_documents_to_folder.return_value = "result"

        result = Procore().workflows.sync_documents_to_folder(
            1,
            "out",
            folder_id=5,
            recursive=True,
            overwrite=True,
            dry_run=True,
            incremental=True,
        )

        self.assertEqual(result, "result")
        sync_documents_to_folder.assert_called_once_with(
            1,
            "out",
            folder_id=5,
            recursive=True,
            overwrite=True,
            dry_run=True,
            incremental=True,
            create_tracker=True,
            create_markdown=True,
        )

    @patch("pyprocore.client.sync_project_to_folder")
    def test_workflows_sync_project_delegates_to_helper(
        self,
        sync_project_to_folder: Mock,
    ) -> None:
        """Workflow project sync delegates to the workflow helper."""
        sync_project_to_folder.return_value = "result"

        result = Procore().workflows.sync_project_to_folder(
            1,
            "out",
            include_submittals=False,
            incremental=True,
        )

        self.assertEqual(result, "result")
        sync_project_to_folder.assert_called_once_with(
            1,
            "out",
            include_rfis=True,
            include_submittals=False,
            status=None,
            download_attachments=True,
            overwrite=False,
            create_tracker=True,
            create_markdown=True,
            dry_run=False,
            incremental=True,
        )

    @patch("pyprocore.client.build_project_context_package")
    def test_workflows_project_context_delegates_to_helper(
        self,
        build_project_context_package: Mock,
    ) -> None:
        """Project context object client passes options through."""
        build_project_context_package.return_value = "context"

        result = Procore().workflows.build_project_context_package(
            1,
            "context",
            company_id=2,
            include=["rfis"],
            exclude=["photos"],
            start_date="2026-07-01",
            end_date="2026-07-10",
            log_date="2026-07-10",
            max_items=5,
            download_files=True,
            overwrite=True,
            continue_on_error=False,
        )

        self.assertEqual(result, "context")
        build_project_context_package.assert_called_once_with(
            1,
            company_id=2,
            output_dir="context",
            include=["rfis"],
            exclude=["photos"],
            start_date="2026-07-01",
            end_date="2026-07-10",
            log_date="2026-07-10",
            max_items=5,
            download_files=True,
            overwrite=True,
            continue_on_error=False,
        )


if __name__ == "__main__":
    unittest.main()
