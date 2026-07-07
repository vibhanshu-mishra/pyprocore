"""Unit tests for the object-oriented Procore client interface."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from pyprocore import Procore
from pyprocore.client import CompaniesClient, ProjectsClient, RFIsClient, SubmittalsClient


class ProcoreObjectClientTestCase(unittest.TestCase):
    """Validate grouped service clients and delegation behavior."""

    def test_root_import_and_grouped_clients_exist(self) -> None:
        """The package root exports Procore with expected grouped clients."""
        client = Procore()

        self.assertIsInstance(client.companies, CompaniesClient)
        self.assertIsInstance(client.projects, ProjectsClient)
        self.assertIsInstance(client.rfis, RFIsClient)
        self.assertIsInstance(client.submittals, SubmittalsClient)

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


if __name__ == "__main__":
    unittest.main()
