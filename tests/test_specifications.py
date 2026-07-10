"""Unit tests for Procore specification services."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from pyprocore.core.exceptions import MultipleResultsError, NotFoundError, ValidationError
from pyprocore.services.specifications import (
    SpecificationsService,
    download_specification_section_revision,
    find_specification_section,
    get_specification_section,
    get_specification_section_revision,
    list_specification_section_revisions,
    list_specification_sections,
    list_specification_sets,
)


class SpecificationsServiceTestCase(unittest.TestCase):
    """Validate specification services without live Procore access."""

    def test_list_specification_sets_uses_v2_path_and_company_header(self) -> None:
        """Set listing sends company ID in the path and header."""
        client = Mock()
        client.get_all.return_value = [{"id": 1, "name": "Issued for Construction"}]

        result = SpecificationsService(client=client).list_specification_sets(
            456,
            company_id=123,
            params={"per_page": 100},
        )

        self.assertEqual(result[0].name, "Issued for Construction")
        client.get_all.assert_called_once_with(
            "/rest/v2.0/companies/123/projects/456/specification_sets",
            params={"per_page": 100},
            headers={"Procore-Company-Id": "123"},
        )

    @patch("pyprocore.services.specifications.get_settings")
    def test_company_id_defaults_to_settings(self, get_settings: Mock) -> None:
        """Specification calls default to PROCORE_COMPANY_ID when omitted."""
        get_settings.return_value.company_id = 321
        client = Mock()
        client.get_all.return_value = [{"id": 1, "name": "Set"}]

        SpecificationsService(client=client).list_specification_sets(456)

        client.get_all.assert_called_once_with(
            "/rest/v2.0/companies/321/projects/456/specification_sets",
            params=None,
            headers={"Procore-Company-Id": "321"},
        )

    def test_list_specification_sections_maps_filters(self) -> None:
        """Section listing maps friendly filters to Procore query params."""
        client = Mock()
        client.get_all.return_value = {
            "data": [{"id": 10, "number": "03 3000", "title": "Cast-in-Place Concrete"}]
        }

        result = SpecificationsService(client=client).list_specification_sections(
            456,
            company_id=123,
            specification_area_id=7,
            specification_set_id=8,
            division_id=3,
            sort="-number",
            page=2,
        )

        self.assertEqual(result[0].number, "03 3000")
        client.get_all.assert_called_once_with(
            "/rest/v2.1/companies/123/projects/456/specification_sections",
            params={
                "page": 2,
                "specification_area_id": 7,
                "filter_set_id": 8,
                "filter_division_id": 3,
                "sort": "-number",
            },
            headers={"Procore-Company-Id": "123"},
        )

    def test_get_specification_section_searches_list(self) -> None:
        """Section retrieval uses the verified list endpoint and local matching."""
        client = Mock()
        client.get_all.return_value = [
            {"id": 10, "number": "03 3000"},
            {"id": 11, "number": "05 1200"},
        ]

        result = SpecificationsService(client=client).get_specification_section(
            456,
            11,
            company_id=123,
        )

        self.assertEqual(result.number, "05 1200")
        client.get_all.assert_called_once()

    def test_get_specification_section_raises_not_found(self) -> None:
        """Missing sections raise a clear resolver error."""
        client = Mock()
        client.get_all.return_value = [{"id": 10, "number": "03 3000"}]

        with self.assertRaisesRegex(NotFoundError, "Specification section 99"):
            SpecificationsService(client=client).get_specification_section(
                456,
                99,
                company_id=123,
            )

    def test_find_specification_section_supports_exact_and_partial(self) -> None:
        """Section lookup supports number, title, and query matching."""
        client = Mock()
        client.get_all.return_value = [
            {"id": 10, "number": "03 3000", "title": "Cast-in-Place Concrete"},
            {"id": 11, "number": "05 1200", "title": "Structural Steel"},
        ]
        service = SpecificationsService(client=client)

        self.assertEqual(
            service.find_specification_section(456, number="03 3000", company_id=123).id,
            10,
        )
        self.assertEqual(
            service.find_specification_section(456, query="steel", company_id=123).id,
            11,
        )

    def test_find_specification_section_raises_for_ambiguous_matches(self) -> None:
        """Ambiguous section lookup raises MultipleResultsError."""
        client = Mock()
        client.get_all.return_value = [
            {"id": 10, "number": "03 3000", "title": "Concrete"},
            {"id": 11, "number": "03 3000", "title": "Concrete Addendum"},
        ]

        with self.assertRaises(MultipleResultsError):
            SpecificationsService(client=client).find_specification_section(
                456,
                number="03 3000",
                company_id=123,
            )

    def test_find_specification_section_requires_criteria(self) -> None:
        """Lookup requires at least one search criterion."""
        with self.assertRaisesRegex(ValidationError, "Provide number"):
            SpecificationsService(client=Mock()).find_specification_section(456, company_id=123)

    def test_list_specification_section_revisions_uses_v2_path(self) -> None:
        """Revision listing sends supported pagination and section filters."""
        client = Mock()
        client.get_all.return_value = {
            "data": [{"id": 20, "revision_number": "1", "specification_section_id": 10}]
        }

        result = SpecificationsService(client=client).list_specification_section_revisions(
            456,
            company_id=123,
            specification_section_id=10,
            page=1,
            per_page=1000,
        )

        self.assertEqual(result[0].id, 20)
        client.get_all.assert_called_once_with(
            "/rest/v2.1/companies/123/projects/456/specification_section_revisions",
            params={"specification_section_id": 10, "page": 1, "per_page": 1000},
            headers={"Procore-Company-Id": "123"},
        )

    def test_get_specification_section_revision_accepts_data_envelope(self) -> None:
        """Revision retrieval accepts a V2 data envelope."""
        client = Mock()
        client.get.return_value = {"data": {"id": 20, "revision_number": "2"}}

        result = SpecificationsService(client=client).get_specification_section_revision(
            456,
            20,
            company_id=123,
        )

        self.assertEqual(result.revision_number, "2")
        client.get.assert_called_once_with(
            "/rest/v2.1/companies/123/projects/456/specification_section_revisions/20",
            headers={"Procore-Company-Id": "123"},
        )

    def test_download_specification_section_revision_uses_download_url(self) -> None:
        """Revision downloads use the download-info endpoint then file service."""
        client = Mock()
        client.get.return_value = {
            "data": {
                "download_url": "https://signed.example/spec.pdf",
                "filename": "03 3000?.pdf",
            }
        }
        file_service = Mock()
        file_service.download_url.return_value = Path("specs/03 3000_.pdf")

        result = SpecificationsService(
            client=client,
            file_service=file_service,
        ).download_specification_section_revision(
            456,
            20,
            output_dir="specs",
            company_id=123,
            overwrite=True,
        )

        self.assertEqual(result, Path("specs/03 3000_.pdf"))
        client.get.assert_called_once_with(
            "/rest/v2.1/companies/123/projects/456/specification_section_revisions/20/download",
            headers={"Procore-Company-Id": "123"},
        )
        file_service.download_url.assert_called_once_with(
            "https://signed.example/spec.pdf",
            Path("specs") / "03 3000_.pdf",
            overwrite=True,
        )

    def test_download_specification_section_revision_requires_url(self) -> None:
        """Download metadata without a URL fails clearly."""
        client = Mock()
        client.get.return_value = {"data": {"filename": "spec.pdf"}}
        file_service = Mock()

        with self.assertRaisesRegex(ValidationError, "does not include a download URL"):
            SpecificationsService(
                client=client,
                file_service=file_service,
            ).download_specification_section_revision(456, 20, company_id=123)

        file_service.download_url.assert_not_called()

    def test_module_level_helpers_delegate_to_service(self) -> None:
        """Module helpers preserve the existing service style."""
        with patch("pyprocore.services.specifications.SpecificationsService") as service_cls:
            service = service_cls.return_value
            service.list_specification_sets.return_value = ["set"]
            service.list_specification_sections.return_value = ["section"]
            service.get_specification_section.return_value = "section"
            service.find_specification_section.return_value = "section"
            service.list_specification_section_revisions.return_value = ["revision"]
            service.get_specification_section_revision.return_value = "revision"
            service.download_specification_section_revision.return_value = Path("spec.pdf")

            self.assertEqual(list_specification_sets(456), ["set"])
            self.assertEqual(list_specification_sections(456), ["section"])
            self.assertEqual(get_specification_section(456, 10), "section")
            self.assertEqual(find_specification_section(456, number="03 3000"), "section")
            self.assertEqual(list_specification_section_revisions(456), ["revision"])
            self.assertEqual(get_specification_section_revision(456, 20), "revision")
            self.assertEqual(
                download_specification_section_revision(456, 20),
                Path("spec.pdf"),
            )


if __name__ == "__main__":
    unittest.main()
