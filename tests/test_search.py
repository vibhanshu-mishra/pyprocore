"""Unit tests for human-friendly search resolvers."""

from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

import pyprocore
from pyprocore.core.config import ProcoreSettings
from pyprocore.core.exceptions import DuplicateMatchError, MultipleResultsError, NotFoundError
from pyprocore.models import RFI, Company, Project, Submittal
from pyprocore.services.search import (
    find_company,
    find_project,
    find_project_contains,
    find_rfi,
    find_submittal,
)


def settings(company_id: int = 123) -> ProcoreSettings:
    """Return test settings without reading environment variables."""
    return ProcoreSettings(
        client_id="client-id",
        client_secret="client-secret",
        redirect_uri="http://localhost/callback",
        login_url="https://login.example.com",
        api_base="https://api.example.com",
        company_id=company_id,
    )


class SearchServiceTestCase(unittest.TestCase):
    """Validate resource resolver behavior."""

    def test_find_company_matches_exact_case_insensitive_name(self) -> None:
        """Company search returns one exact match regardless of case."""
        with patch(
            "pyprocore.services.search.list_companies",
            return_value=[
                Company(id=1, name="Tracker Construction"),
                Company(id=2, name="Other"),
            ],
        ):
            company = find_company("tracker construction")

        self.assertEqual(company.id, 1)

    def test_find_company_falls_back_to_partial_match(self) -> None:
        """Company search supports partial matching."""
        with patch(
            "pyprocore.services.search.list_companies",
            return_value=[
                Company(id=1, name="Tracker Construction"),
                Company(id=2, name="Other"),
            ],
        ):
            company = find_company("Tracker")

        self.assertEqual(company.id, 1)

    def test_find_company_raises_for_missing_duplicate_and_ambiguous_matches(self) -> None:
        """Company search raises clear resolver exceptions."""
        with patch("pyprocore.services.search.list_companies", return_value=[]):
            with self.assertRaises(NotFoundError):
                find_company("missing")

        with patch(
            "pyprocore.services.search.list_companies",
            return_value=[Company(id=1, name="Tracker"), Company(id=2, name="tracker")],
        ):
            with self.assertRaises(DuplicateMatchError):
                find_company("TRACKER")

        with patch(
            "pyprocore.services.search.list_companies",
            return_value=[
                Company(id=1, name="Tracker North"),
                Company(id=2, name="Tracker South"),
            ],
        ):
            with self.assertRaises(MultipleResultsError):
                find_company("Tracker")

    def test_find_project_matches_name_or_number_with_configured_company(self) -> None:
        """Project search supports names, numbers, and configured company IDs."""
        projects = [
            Project(id=10, name="Sandbox Test Project", project_number="001"),
            Project(id=20, name="Hospital Expansion", project_number="002"),
        ]

        with patch("pyprocore.services.search.list_projects", return_value=projects) as projects_fn:
            by_name = find_project("sandbox test project", settings=settings(456))
            by_number = find_project(number="002", company_id=789)

        self.assertEqual(by_name.id, 10)
        self.assertEqual(by_number.id, 20)
        self.assertEqual(projects_fn.call_args_list[0].args, (456,))
        self.assertEqual(projects_fn.call_args_list[1].args, (789,))

    def test_find_project_contains_searches_name_and_number(self) -> None:
        """Project contains search returns one partial name or number match."""
        projects = [
            Project(id=10, name="Sandbox Test Project", project_number="001"),
            Project(id=20, name="Hospital Expansion", project_number="002"),
        ]

        with patch("pyprocore.services.search.list_projects", return_value=projects):
            project = find_project_contains("hospital", company_id=123)

        self.assertEqual(project.id, 20)

    def test_find_project_validates_query_shape(self) -> None:
        """Project search requires exactly one name or number query."""
        with self.assertRaises(ValueError):
            find_project(settings=settings())

        with self.assertRaises(ValueError):
            find_project("Project", number="001", settings=settings())

        with self.assertRaises(ValueError):
            find_project("   ", settings=settings())

    def test_find_rfi_matches_number_within_project(self) -> None:
        """RFI search resolves by number within a project."""
        with patch(
            "pyprocore.services.search.list_rfis",
            return_value=[RFI(id=1, number="14"), RFI(id=2, number=15)],
        ) as rfis_fn:
            rfi = find_rfi(352338, number="15")

        self.assertEqual(rfi.id, 2)
        rfis_fn.assert_called_once_with(352338)

    def test_find_submittal_matches_number_within_project(self) -> None:
        """Submittal search resolves by number within a project."""
        with patch(
            "pyprocore.services.search.list_submittals",
            return_value=[
                Submittal(id=1, number="26"),
                Submittal(id=2, number="27"),
            ],
        ) as submittals_fn:
            submittal = find_submittal(352338, number=27)

        self.assertEqual(submittal.id, 2)
        submittals_fn.assert_called_once_with(352338)

    def test_root_package_exports_search_functions_and_exceptions(self) -> None:
        """Package root exposes resolver helpers for convenient imports."""
        self.assertIs(pyprocore.find_company, find_company)
        self.assertIs(pyprocore.find_project, find_project)
        self.assertIs(pyprocore.find_project_contains, find_project_contains)
        self.assertIs(pyprocore.find_rfi, find_rfi)
        self.assertIs(pyprocore.find_submittal, find_submittal)
        self.assertIs(pyprocore.NotFoundError, NotFoundError)
        self.assertIs(pyprocore.DuplicateMatchError, DuplicateMatchError)
        self.assertIs(pyprocore.MultipleResultsError, MultipleResultsError)

    def test_blank_queries_are_rejected_before_api_calls(self) -> None:
        """Blank resolver queries fail locally."""
        with patch("pyprocore.services.search.list_companies") as companies_fn:
            with self.assertRaises(ValueError):
                find_company(" ")

        companies_fn.assert_not_called()

        with patch("pyprocore.services.search.list_rfis") as rfis_fn:
            with self.assertRaises(ValueError):
                find_rfi(1, number=" ")

        rfis_fn.assert_not_called()

        with self.assertRaises(ValueError):
            find_submittal(1, number=None)  # type: ignore[arg-type]

    def test_find_project_uses_default_settings_when_company_id_omitted(self) -> None:
        """Project search reads configured company ID when no override is supplied."""
        configured = Mock(company_id=321)

        with (
            patch("pyprocore.services.search.get_settings", return_value=configured),
            patch(
                "pyprocore.services.search.list_projects",
                return_value=[Project(id=10, name="Sandbox", project_number="001")],
            ) as projects_fn,
        ):
            project = find_project("Sandbox")

        self.assertEqual(project.id, 10)
        projects_fn.assert_called_once_with(321)


if __name__ == "__main__":
    unittest.main()
