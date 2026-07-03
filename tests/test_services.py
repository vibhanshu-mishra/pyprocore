"""Unit tests for Procore service modules."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from pydantic import SecretStr

from core.config import ProcoreSettings
from core.exceptions import ResourceNotFoundError, ValidationError
from services.companies import CompaniesService, list_companies
from services.projects import ProjectsService, get_project, list_projects
from services.rfis import RFIsService
from services.submittals import SubmittalsService


def settings() -> ProcoreSettings:
    """Return test settings without reading environment variables."""
    return ProcoreSettings(
        client_id="client-id",
        client_secret=SecretStr("client-secret"),
        redirect_uri="http://localhost/callback",
        login_url="https://login.example.com",
        api_base="https://api.example.com",
        company_id=123,
    )


class CompaniesServiceTestCase(unittest.TestCase):
    """Validate company service behavior."""

    def test_list_companies_returns_list_response(self) -> None:
        """Company lists are returned unchanged."""
        client = Mock()
        client.get_all.return_value = [{"id": 1}]

        result = CompaniesService(client).list_companies()

        self.assertEqual(result[0].id, 1)
        client.get_all.assert_called_once_with("/rest/v1.0/companies")

    def test_list_companies_wraps_single_object_response(self) -> None:
        """Unexpected single-object responses are normalized to a list."""
        client = Mock()
        client.get_all.return_value = {"id": 1}

        self.assertEqual(list_companies(client)[0].id, 1)


class ProjectsServiceTestCase(unittest.TestCase):
    """Validate project service behavior."""

    def test_list_projects_calls_verified_endpoint(self) -> None:
        """Project listing uses the company projects endpoint."""
        client = Mock()
        client.get_all.return_value = [{"id": 10}]

        result = ProjectsService(client=client, settings=settings()).list_projects(456)

        self.assertEqual(result[0].id, 10)
        client.get_all.assert_called_once_with("/rest/v1.0/companies/456/projects")

    def test_list_projects_wraps_single_object_response(self) -> None:
        """Single-object project responses are normalized to a list."""
        client = Mock()
        client.get_all.return_value = {"id": 10}

        result = ProjectsService(client=client, settings=settings()).list_projects(456)

        self.assertEqual(result[0].id, 10)

    def test_list_projects_validates_company_id(self) -> None:
        """Invalid company IDs fail before HTTP calls."""
        client = Mock()

        with self.assertRaises(ValidationError):
            ProjectsService(client=client, settings=settings()).list_projects(0)

        client.get_all.assert_not_called()

    def test_get_project_returns_match_from_configured_company(self) -> None:
        """Single project lookup filters the configured company project list."""
        client = Mock()
        client.get_all.return_value = [{"id": 10}, {"id": 20, "name": "Target"}]

        result = ProjectsService(client=client, settings=settings()).get_project(20)

        self.assertEqual(result.id, 20)
        self.assertEqual(result.name, "Target")
        client.get_all.assert_called_once_with("/rest/v1.0/companies/123/projects")

    def test_get_project_raises_when_missing(self) -> None:
        """Missing projects raise ResourceNotFoundError."""
        client = Mock()
        client.get_all.return_value = [{"id": 10}]

        with self.assertRaises(ResourceNotFoundError):
            ProjectsService(client=client, settings=settings()).get_project(20)

    def test_get_project_validates_project_id(self) -> None:
        """Invalid project IDs fail before HTTP calls."""
        client = Mock()

        with self.assertRaises(ValidationError):
            ProjectsService(client=client, settings=settings()).get_project(-1)

        client.get_all.assert_not_called()

    def test_project_convenience_functions_delegate_to_service(self) -> None:
        """Module-level helpers delegate to ProjectsService."""
        with patch("services.projects.ProjectsService") as service_class:
            service = Mock()
            service.list_projects.return_value = [{"id": 1}]
            service.get_project.return_value = {"id": 2}
            service_class.return_value = service

            self.assertEqual(list_projects(123, client=Mock()), [{"id": 1}])
            self.assertEqual(get_project(2, client=Mock()), {"id": 2})


class RFIsServiceTestCase(unittest.TestCase):
    """Validate RFI service behavior."""

    def test_list_and_get_rfis_use_verified_endpoints(self) -> None:
        """RFI service uses verified list and detail routes."""
        client = Mock()
        client.get_all.return_value = [{"id": 1}]
        client.get.return_value = {"id": 2}
        service = RFIsService(client=client, file_service=Mock())

        self.assertEqual(service.list_rfis(99)[0].id, 1)
        self.assertEqual(service.get_rfi(99, 2).id, 2)
        client.get_all.assert_called_once_with("/rest/v1.1/projects/99/rfis")
        client.get.assert_called_once_with("/rest/v1.1/projects/99/rfis/2")

    def test_rfi_validation_and_bad_response(self) -> None:
        """RFI service validates IDs and response shape."""
        client = Mock()
        client.get.return_value = []
        service = RFIsService(client=client, file_service=Mock())

        with self.assertRaises(ValidationError):
            service.list_rfis(0)
        with self.assertRaises(ValidationError):
            service.get_rfi(1, 0)
        with self.assertRaises(ValidationError):
            service.get_rfi(1, 2)

    def test_download_rfi_attachments_extracts_question_attachments(self) -> None:
        """RFI attachment downloads read questions[].attachments[].url."""
        client = Mock()
        client.get.return_value = {
            "id": 7,
            "questions": [
                {"attachments": [{"url": "https://signed/one.pdf"}]},
                {"attachments": [{"url": "https://signed/two.pdf"}, {"name": "skip"}]},
            ],
        }
        file_service = Mock()
        file_service.download_attachments.return_value = [
            Path("one.pdf"),
            Path("two.pdf"),
        ]

        with TemporaryDirectory() as temporary_directory:
            result = RFIsService(
                client=client, file_service=file_service
            ).download_rfi_attachments(
                99,
                7,
                temporary_directory,
            )

        self.assertEqual(result, [Path("one.pdf"), Path("two.pdf")])
        file_service.download_attachments.assert_called_once()
        self.assertEqual(
            file_service.download_attachments.call_args.kwargs["fallback_prefix"],
            "rfi-7",
        )

    def test_extract_question_attachments_handles_invalid_questions(self) -> None:
        """Invalid question payloads produce no attachments."""
        self.assertEqual(
            RFIsService._extract_question_attachments({"questions": "bad"}), []
        )


class SubmittalsServiceTestCase(unittest.TestCase):
    """Validate submittal service behavior."""

    def test_list_and_get_submittals_use_verified_endpoints(self) -> None:
        """Submittal service uses verified list and detail routes."""
        client = Mock()
        client.get_all.return_value = [{"id": 1}]
        client.get.return_value = {"id": 2}
        service = SubmittalsService(client=client, file_service=Mock())

        self.assertEqual(service.list_submittals(99)[0].id, 1)
        self.assertEqual(service.get_submittal(99, 2).id, 2)
        client.get_all.assert_called_once_with("/rest/v1.1/projects/99/submittals")
        client.get.assert_called_once_with("/rest/v1.1/projects/99/submittals/2")

    def test_submittal_validation_and_bad_response(self) -> None:
        """Submittal service validates IDs and response shape."""
        client = Mock()
        client.get.return_value = []
        service = SubmittalsService(client=client, file_service=Mock())

        with self.assertRaises(ValidationError):
            service.list_submittals(0)
        with self.assertRaises(ValidationError):
            service.get_submittal(1, 0)
        with self.assertRaises(ValidationError):
            service.get_submittal(1, 2)

    def test_download_submittal_attachments_extracts_attachments(self) -> None:
        """Submittal downloads read attachments[].url."""
        client = Mock()
        client.get.return_value = {
            "id": 8,
            "attachments": [
                {"url": "https://signed/spec.pdf"},
                {"url": "https://signed/shop.pdf"},
                {"name": "skip"},
            ],
        }
        file_service = Mock()
        file_service.download_attachments.return_value = [
            Path("spec.pdf"),
            Path("shop.pdf"),
        ]

        with TemporaryDirectory() as temporary_directory:
            result = SubmittalsService(
                client=client,
                file_service=file_service,
            ).download_submittal_attachments(99, 8, temporary_directory)

        self.assertEqual(result, [Path("spec.pdf"), Path("shop.pdf")])
        file_service.download_attachments.assert_called_once()
        self.assertEqual(
            file_service.download_attachments.call_args.kwargs["fallback_prefix"],
            "submittal-8",
        )

    def test_extract_attachments_handles_invalid_payloads(self) -> None:
        """Invalid attachment payloads produce no attachments."""
        self.assertEqual(
            SubmittalsService._extract_attachments({"attachments": "bad"}), []
        )
        self.assertEqual(
            SubmittalsService._extract_attachments({"attachments": [1]}), []
        )


if __name__ == "__main__":
    unittest.main()
