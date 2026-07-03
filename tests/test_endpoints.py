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


if __name__ == "__main__":
    unittest.main()
