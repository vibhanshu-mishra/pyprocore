"""Tests for verified Procore endpoint path builders."""

from __future__ import annotations

import unittest

from pyprocore.core import endpoints


class EndpointsTestCase(unittest.TestCase):
    """Validate endpoint paths against known working Procore routes."""

    def test_companies_endpoint(self) -> None:
        """Companies endpoint uses the verified v1.0 route."""
        self.assertEqual(endpoints.companies(), "/rest/v1.0/companies")

    def test_projects_endpoint(self) -> None:
        """Projects endpoint includes the company ID."""
        self.assertEqual(
            endpoints.projects(company_id=123),
            "/rest/v1.0/companies/123/projects",
        )

    def test_rfi_endpoints(self) -> None:
        """RFI endpoints use the verified v1.1 routes."""
        self.assertEqual(endpoints.rfis(project_id=456), "/rest/v1.1/projects/456/rfis")
        self.assertEqual(
            endpoints.rfi(project_id=456, rfi_id=789),
            "/rest/v1.1/projects/456/rfis/789",
        )

    def test_submittal_endpoints(self) -> None:
        """Submittal endpoints use the verified v1.1 routes."""
        self.assertEqual(
            endpoints.submittals(project_id=456),
            "/rest/v1.1/projects/456/submittals",
        )
        self.assertEqual(
            endpoints.submittal(project_id=456, submittal_id=789),
            "/rest/v1.1/projects/456/submittals/789",
        )

    def test_drawing_endpoints(self) -> None:
        """Drawing endpoints use project and drawing-area scoped routes."""
        self.assertEqual(
            endpoints.drawing_areas(project_id=456),
            "/rest/v1.0/projects/456/drawing_areas",
        )
        self.assertEqual(
            endpoints.drawing_area(project_id=456, drawing_area_id=12),
            "/rest/v1.0/projects/456/drawing_areas/12",
        )
        self.assertEqual(
            endpoints.drawing_disciplines(project_id=456),
            "/rest/v1.0/projects/456/drawing_disciplines",
        )
        self.assertEqual(
            endpoints.drawings(project_id=456, drawing_area_id=12),
            "/rest/v1.0/drawing_areas/12/drawings",
        )
        self.assertEqual(
            endpoints.drawing(project_id=456, drawing_area_id=12, drawing_id=789),
            "/rest/v1.0/drawing_areas/12/drawings/789",
        )
        self.assertEqual(
            endpoints.drawing_revisions(project_id=456),
            "/rest/v1.0/projects/456/drawing_revisions",
        )

    def test_photo_endpoints(self) -> None:
        """Photo endpoints use query-scoped image category and image routes."""
        self.assertEqual(endpoints.image_categories(), "/rest/v1.0/image_categories")
        self.assertEqual(
            endpoints.image_category(image_category_id=123),
            "/rest/v1.0/image_categories/123",
        )
        self.assertEqual(endpoints.images(), "/rest/v1.0/images")
        self.assertEqual(endpoints.image(image_id=456), "/rest/v1.0/images/456")

    def test_specification_endpoints(self) -> None:
        """Specification endpoints use verified company/project scoped routes."""
        self.assertEqual(
            endpoints.specification_sets(company_id=123, project_id=456),
            "/rest/v2.0/companies/123/projects/456/specification_sets",
        )
        self.assertEqual(
            endpoints.specification_set_v1(project_id=456, specification_set_id=789),
            "/rest/v1.0/projects/456/specification_sets/789",
        )
        self.assertEqual(
            endpoints.specification_sections(company_id=123, project_id=456),
            "/rest/v2.1/companies/123/projects/456/specification_sections",
        )
        self.assertEqual(
            endpoints.specification_section_revisions(company_id=123, project_id=456),
            "/rest/v2.1/companies/123/projects/456/specification_section_revisions",
        )
        self.assertEqual(
            endpoints.specification_section_revision(
                company_id=123,
                project_id=456,
                revision_id=789,
            ),
            "/rest/v2.1/companies/123/projects/456/specification_section_revisions/789",
        )
        self.assertEqual(
            endpoints.specification_section_revision_download(
                company_id=123,
                project_id=456,
                revision_id=789,
            ),
            "/rest/v2.1/companies/123/projects/456/specification_section_revisions/789/download",
        )


if __name__ == "__main__":
    unittest.main()
