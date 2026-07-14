"""Tests for Phase 8D read-only directory and location resources."""

from __future__ import annotations

import argparse
import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pyprocore.agent import export_mcp_tools_json, list_agent_tools
from pyprocore.app import build_parser, run_command
from pyprocore.client import Procore
from pyprocore.core import endpoints
from pyprocore.core.exceptions import MultipleResultsError
from pyprocore.models import (
    CompanyUser,
    Department,
    DistributionGroup,
    Location,
    ProjectUser,
    Vendor,
)
from pyprocore.services.directory import (
    DirectoryService,
)
from pyprocore.services.directory import get_company_user as get_company_user_wrapper
from pyprocore.services.directory import get_department as get_department_wrapper
from pyprocore.services.directory import get_location as get_location_wrapper
from pyprocore.services.directory import (
    get_project_distribution_group as get_project_distribution_group_wrapper,
)
from pyprocore.services.directory import get_project_user as get_project_user_wrapper
from pyprocore.services.directory import get_vendor as get_vendor_wrapper
from pyprocore.services.directory import (
    list_company_inactive_users as list_company_inactive_users_wrapper,
)
from pyprocore.services.directory import list_company_users as list_company_users_wrapper
from pyprocore.services.directory import list_departments as list_departments_wrapper
from pyprocore.services.directory import list_locations as list_locations_wrapper
from pyprocore.services.directory import (
    list_project_distribution_groups as list_project_distribution_groups_wrapper,
)
from pyprocore.services.directory import list_project_users as list_project_users_wrapper
from pyprocore.services.directory import list_project_vendors as list_project_vendors_wrapper
from pyprocore.services.directory import list_vendors as list_vendors_wrapper
from pyprocore.workflows.exports import (
    export_company_users_to_csv,
    export_company_users_to_jsonl,
    export_departments_to_csv,
    export_departments_to_jsonl,
    export_distribution_groups_to_csv,
    export_distribution_groups_to_jsonl,
    export_locations_to_jsonl,
    export_project_users_to_csv,
    export_project_users_to_jsonl,
    export_vendors_to_csv,
    export_vendors_to_jsonl,
    write_departments_csv,
    write_distribution_groups_csv,
    write_project_users_csv,
    write_vendors_csv,
)


class FakeClient:
    """Small fake Procore client that records calls without HTTP."""

    def __init__(self) -> None:
        """Initialize fake responses and recorded calls."""
        self.calls: list[tuple[str, str, dict[str, object] | None, dict[str, str] | None]] = []
        self.list_response: object = []
        self.get_response: object = {}

    def get_all(
        self,
        path: str,
        *,
        params: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
    ) -> object:
        """Return the configured list response."""
        self.calls.append(("get_all", path, params, headers))
        return self.list_response

    def get(
        self,
        path: str,
        *,
        params: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
    ) -> object:
        """Return the configured get response."""
        self.calls.append(("get", path, params, headers))
        return self.get_response


class Phase8DEndpointTestCase(unittest.TestCase):
    """Endpoint construction tests for Phase 8D resources."""

    def test_phase8d_endpoint_paths(self) -> None:
        """Endpoint helpers should return read-only collection/item paths."""
        self.assertEqual(endpoints.company_users(456), "/rest/v1.0/companies/456/users")
        self.assertEqual(endpoints.company_user(456, 7), "/rest/v1.0/companies/456/users/7")
        self.assertEqual(endpoints.project_users(123), "/rest/v1.0/projects/123/users")
        self.assertEqual(endpoints.project_user(123, 7), "/rest/v1.0/projects/123/users/7")
        self.assertEqual(endpoints.vendors(456), "/rest/v1.0/vendors")
        self.assertEqual(endpoints.vendor(456, 8), "/rest/v1.0/vendors/8")
        self.assertEqual(endpoints.departments(456), "/rest/v1.0/companies/456/departments")
        self.assertEqual(
            endpoints.department(456, 9),
            "/rest/v1.0/companies/456/departments/9",
        )
        self.assertEqual(
            endpoints.project_distribution_groups(123),
            "/rest/v1.0/projects/123/distribution_groups",
        )
        self.assertEqual(
            endpoints.project_distribution_group(123, 10),
            "/rest/v1.0/projects/123/distribution_groups/10",
        )
        self.assertEqual(endpoints.locations(123), "/rest/v1.0/projects/123/locations")
        self.assertEqual(endpoints.location(123, 11), "/rest/v1.0/projects/123/locations/11")


class Phase8DServiceTestCase(unittest.TestCase):
    """Service tests with mocked HTTP client behavior."""

    def test_company_users_list_and_get_paths(self) -> None:
        """Company users should use company-scoped paths and headers."""
        fake = FakeClient()
        fake.list_response = {"users": [{"id": 1, "name": "Alex", "email": "a@example.com"}]}

        users = DirectoryService(client=fake).list_company_users(456, active=True)

        self.assertIsInstance(users[0], CompanyUser)
        self.assertEqual(users[0].name, "Alex")
        self.assertEqual(fake.calls[0][1], "/rest/v1.0/companies/456/users")
        self.assertEqual(fake.calls[0][2], {"active": True})
        self.assertEqual(fake.calls[0][3], {"Procore-Company-Id": "456"})

        fake.get_response = {"id": 1, "name": "Alex"}
        user = DirectoryService(client=fake).get_company_user(456, 1)
        self.assertEqual(user.id, 1)
        self.assertEqual(fake.calls[1][1], "/rest/v1.0/companies/456/users/1")

    def test_project_users_vendors_departments_groups_and_locations(self) -> None:
        """Phase 8D list helpers should use read-only paths and typed models."""
        fake = FakeClient()
        service = DirectoryService(client=fake)

        fake.list_response = {"users": [{"id": 2, "name": "Jordan", "project_id": 123}]}
        self.assertIsInstance(service.list_project_users(456, 123)[0], ProjectUser)
        self.assertEqual(fake.calls[-1][1], "/rest/v1.0/projects/123/users")

        fake.list_response = {"vendors": [{"id": 3, "name": "Concrete Co"}]}
        self.assertIsInstance(service.list_vendors(456)[0], Vendor)
        self.assertEqual(fake.calls[-1][1], "/rest/v1.0/vendors")
        self.assertEqual(fake.calls[-1][2], {"company_id": 456})

        fake.list_response = {"departments": [{"id": 4, "name": "Operations"}]}
        self.assertIsInstance(service.list_departments(456)[0], Department)
        self.assertEqual(fake.calls[-1][1], "/rest/v1.0/companies/456/departments")

        fake.list_response = {"distribution_groups": [{"id": 5, "name": "Reviewers"}]}
        self.assertIsInstance(
            service.list_project_distribution_groups(456, 123)[0],
            DistributionGroup,
        )
        self.assertEqual(fake.calls[-1][1], "/rest/v1.0/projects/123/distribution_groups")

        fake.list_response = {"locations": [{"id": 6, "name": "Level 1"}]}
        self.assertIsInstance(service.list_locations(456, 123)[0], Location)
        self.assertEqual(fake.calls[-1][1], "/rest/v1.0/projects/123/locations")

    def test_get_helpers_return_typed_models(self) -> None:
        """Phase 8D get helpers should parse typed models."""
        fake = FakeClient()
        service = DirectoryService(client=fake)

        fake.get_response = {"id": 2, "name": "Jordan", "project_id": 123}
        self.assertIsInstance(service.get_project_user(456, 123, 2), ProjectUser)
        self.assertEqual(fake.calls[-1][1], "/rest/v1.0/projects/123/users/2")

        fake.get_response = {"id": 3, "name": "Concrete Co"}
        self.assertIsInstance(service.get_vendor(456, 3), Vendor)
        self.assertEqual(fake.calls[-1][1], "/rest/v1.0/vendors/3")

        fake.get_response = {"id": 4, "name": "Operations"}
        self.assertIsInstance(service.get_department(456, 4), Department)
        self.assertEqual(fake.calls[-1][1], "/rest/v1.0/companies/456/departments/4")

        fake.get_response = {"id": 5, "name": "Reviewers"}
        self.assertIsInstance(
            service.get_project_distribution_group(456, 123, 5), DistributionGroup
        )
        self.assertEqual(fake.calls[-1][1], "/rest/v1.0/projects/123/distribution_groups/5")

        fake.get_response = {"id": 6, "name": "Level 1"}
        self.assertIsInstance(service.get_location(456, 123, 6), Location)
        self.assertEqual(fake.calls[-1][1], "/rest/v1.0/projects/123/locations/6")

    def test_module_level_wrappers_accept_injected_clients(self) -> None:
        """Module-level service wrappers should preserve injected-client behavior."""
        fake = FakeClient()
        fake.list_response = [{"id": 1, "name": "Alex"}]
        self.assertEqual(list_company_users_wrapper(456, client=fake)[0].name, "Alex")
        self.assertEqual(list_company_inactive_users_wrapper(456, client=fake)[0].name, "Alex")

        fake.list_response = [{"id": 8, "name": "Jordan"}]
        self.assertEqual(list_project_users_wrapper(456, 123, client=fake)[0].name, "Jordan")

        fake.list_response = [{"id": 9, "name": "Vendor"}]
        self.assertEqual(list_vendors_wrapper(456, client=fake)[0].name, "Vendor")
        self.assertEqual(list_project_vendors_wrapper(456, 123, client=fake)[0].name, "Vendor")

        fake.list_response = [{"id": 10, "name": "Department"}]
        self.assertEqual(list_departments_wrapper(456, client=fake)[0].name, "Department")

        fake.list_response = [{"id": 11, "name": "Group"}]
        self.assertEqual(
            list_project_distribution_groups_wrapper(456, 123, client=fake)[0].name,
            "Group",
        )

        fake.list_response = [{"id": 2, "name": "Level 1"}]
        self.assertEqual(list_locations_wrapper(456, 123, client=fake)[0].name, "Level 1")

        fake.get_response = {"id": 3, "name": "Casey"}
        self.assertEqual(get_company_user_wrapper(456, 3, client=fake).name, "Casey")

        fake.get_response = {"id": 4, "name": "Jordan"}
        self.assertEqual(get_project_user_wrapper(456, 123, 4, client=fake).name, "Jordan")

        fake.get_response = {"id": 5, "name": "Vendor"}
        self.assertEqual(get_vendor_wrapper(456, 5, client=fake).name, "Vendor")

        fake.get_response = {"id": 6, "name": "Department"}
        self.assertEqual(get_department_wrapper(456, 6, client=fake).name, "Department")

        fake.get_response = {"id": 12, "name": "Group"}
        self.assertEqual(
            get_project_distribution_group_wrapper(456, 123, 12, client=fake).name,
            "Group",
        )

        fake.get_response = {"id": 7, "name": "Location"}
        self.assertEqual(get_location_wrapper(456, 123, 7, client=fake).name, "Location")


class Phase8DSearchExportClientTestCase(unittest.TestCase):
    """Search, export, object-client, and agent metadata tests."""

    def test_search_helpers_resolve_matches(self) -> None:
        """Search helpers should resolve typed models from mocked lists."""
        with patch(
            "pyprocore.services.search.list_company_users",
            return_value=[CompanyUser(id=1, name="Alex", email="a@example.com")],
        ):
            from pyprocore.services.search import find_company_user

            self.assertEqual(find_company_user(456, email="a@example.com").id, 1)

        with patch(
            "pyprocore.services.search.list_vendors",
            return_value=[Vendor(id=2, name="Concrete Co"), Vendor(id=3, name="Concrete LLC")],
        ):
            from pyprocore.services.search import find_vendor

            with self.assertRaises(MultipleResultsError):
                find_vendor(456, query="concrete")

        with patch(
            "pyprocore.services.search.list_locations",
            return_value=[Location(id=4, name="Level 1", code="L1")],
        ):
            from pyprocore.services.search import find_location

            self.assertEqual(find_location(456, 123, code="L1").id, 4)

        with patch(
            "pyprocore.services.search.list_project_users",
            return_value=[ProjectUser(id=5, name="Casey", email="casey@example.com")],
        ):
            from pyprocore.services.search import find_project_user

            self.assertEqual(find_project_user(456, 123, name="Casey").id, 5)

        with patch(
            "pyprocore.services.search.list_departments",
            return_value=[Department(id=6, name="Operations", code="OPS")],
        ):
            from pyprocore.services.search import find_department

            self.assertEqual(find_department(456, code="OPS").id, 6)

        with patch(
            "pyprocore.services.search.list_project_distribution_groups",
            return_value=[DistributionGroup(id=7, name="Reviewers")],
        ):
            from pyprocore.services.search import find_project_distribution_group

            self.assertEqual(find_project_distribution_group(456, 123, name="Reviewers").id, 7)

    def test_exports_write_local_files(self) -> None:
        """Phase 8D export helpers should write local CSV and JSONL files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "company-users.csv"
            with patch(
                "pyprocore.workflows.exports.list_company_users",
                return_value=[CompanyUser(id=1, name="Alex", email="a@example.com")],
            ):
                saved_path = export_company_users_to_csv(456, output_path)
                self.assertTrue(
                    export_company_users_to_jsonl(
                        456,
                        Path(temp_dir) / "company-users.jsonl",
                    ).exists()
                )

            with saved_path.open(newline="", encoding="utf-8") as file_handle:
                rows = list(csv.DictReader(file_handle))
            self.assertEqual(rows[0]["name"], "Alex")

            self.assertTrue(
                write_project_users_csv(
                    [ProjectUser(id=2, name="Jordan")],
                    Path(temp_dir) / "project-users.csv",
                ).exists()
            )
            self.assertTrue(
                write_vendors_csv(
                    [Vendor(id=3, name="Vendor")],
                    Path(temp_dir) / "vendors.csv",
                ).exists()
            )
            self.assertTrue(
                write_departments_csv(
                    [Department(id=4, name="Department")],
                    Path(temp_dir) / "departments.csv",
                ).exists()
            )
            self.assertTrue(
                write_distribution_groups_csv(
                    [DistributionGroup(id=5, name="Group", users=[{"id": 1}])],
                    Path(temp_dir) / "groups.csv",
                ).exists()
            )

            with patch(
                "pyprocore.workflows.exports.list_locations",
                return_value=[Location(id=6, name="Level 1")],
            ):
                jsonl_path = export_locations_to_jsonl(456, 123, Path(temp_dir) / "locations.jsonl")
            self.assertIn('"name": "Level 1"', jsonl_path.read_text(encoding="utf-8"))

            with patch(
                "pyprocore.workflows.exports.list_project_users",
                return_value=[ProjectUser(id=7, name="Project User")],
            ):
                self.assertTrue(
                    export_project_users_to_csv(
                        456,
                        123,
                        Path(temp_dir) / "project-users-export.csv",
                    ).exists()
                )
                self.assertTrue(
                    export_project_users_to_jsonl(
                        456,
                        123,
                        Path(temp_dir) / "project-users.jsonl",
                    ).exists()
                )

            with patch(
                "pyprocore.workflows.exports.list_vendors",
                return_value=[Vendor(id=8, name="Vendor")],
            ):
                self.assertTrue(export_vendors_to_csv(456, Path(temp_dir) / "vendors.csv").exists())
                self.assertTrue(
                    export_vendors_to_jsonl(456, Path(temp_dir) / "vendors.jsonl").exists()
                )

            with patch(
                "pyprocore.workflows.exports.list_departments",
                return_value=[Department(id=9, name="Department")],
            ):
                self.assertTrue(
                    export_departments_to_csv(456, Path(temp_dir) / "departments.csv").exists()
                )
                self.assertTrue(
                    export_departments_to_jsonl(
                        456,
                        Path(temp_dir) / "departments.jsonl",
                    ).exists()
                )

            with patch(
                "pyprocore.workflows.exports.list_project_distribution_groups",
                return_value=[DistributionGroup(id=10, name="Group")],
            ):
                self.assertTrue(
                    export_distribution_groups_to_csv(
                        456,
                        123,
                        Path(temp_dir) / "groups-export.csv",
                    ).exists()
                )
                self.assertTrue(
                    export_distribution_groups_to_jsonl(
                        456,
                        123,
                        Path(temp_dir) / "groups.jsonl",
                    ).exists()
                )

    def test_object_client_exposes_phase8d_clients(self) -> None:
        """The object client should expose grouped Phase 8D clients."""
        client = Procore()
        self.assertTrue(hasattr(client, "company_users"))
        self.assertTrue(hasattr(client, "project_users"))
        self.assertTrue(hasattr(client, "vendors"))
        self.assertTrue(hasattr(client, "departments"))
        self.assertTrue(hasattr(client, "distribution_groups"))
        self.assertTrue(hasattr(client, "locations"))

    def test_object_client_delegates_phase8d_methods(self) -> None:
        """Object-client methods should delegate to Phase 8D service functions."""
        client = Procore()
        with patch("pyprocore.client.list_company_users", return_value=[CompanyUser(id=1)]):
            self.assertEqual(client.company_users.list(456)[0].id, 1)
        with patch(
            "pyprocore.client.list_company_inactive_users", return_value=[CompanyUser(id=2)]
        ):
            self.assertEqual(client.company_users.inactive(456)[0].id, 2)
        with patch("pyprocore.client.get_company_user", return_value=CompanyUser(id=3)):
            self.assertEqual(client.company_users.get(3, company_id=456).id, 3)
        with patch("pyprocore.client.find_company_user", return_value=CompanyUser(id=4)):
            self.assertEqual(client.company_users.find(456, name="Alex").id, 4)

        with patch("pyprocore.client.list_project_users", return_value=[ProjectUser(id=5)]):
            self.assertEqual(client.project_users.list(123, company_id=456)[0].id, 5)
        with patch("pyprocore.client.get_project_user", return_value=ProjectUser(id=6)):
            self.assertEqual(client.project_users.get(123, 6, company_id=456).id, 6)
        with patch("pyprocore.client.find_project_user", return_value=ProjectUser(id=7)):
            self.assertEqual(client.project_users.find(123, company_id=456, name="Alex").id, 7)

        with patch("pyprocore.client.list_vendors", return_value=[Vendor(id=8)]):
            self.assertEqual(client.vendors.list(456)[0].id, 8)
        with patch("pyprocore.client.list_project_vendors", return_value=[Vendor(id=9)]):
            self.assertEqual(client.vendors.list_project(123, company_id=456)[0].id, 9)
        with patch("pyprocore.client.get_vendor", return_value=Vendor(id=10)):
            self.assertEqual(client.vendors.get(10, company_id=456).id, 10)
        with patch("pyprocore.client.find_vendor", return_value=Vendor(id=11)):
            self.assertEqual(client.vendors.find(456, name="Vendor").id, 11)

        with patch("pyprocore.client.list_departments", return_value=[Department(id=12)]):
            self.assertEqual(client.departments.list(456)[0].id, 12)
        with patch("pyprocore.client.get_department", return_value=Department(id=13)):
            self.assertEqual(client.departments.get(13, company_id=456).id, 13)
        with patch("pyprocore.client.find_department", return_value=Department(id=14)):
            self.assertEqual(client.departments.find(456, code="OPS").id, 14)

        with patch(
            "pyprocore.client.list_project_distribution_groups",
            return_value=[DistributionGroup(id=15)],
        ):
            self.assertEqual(client.distribution_groups.list(123, company_id=456)[0].id, 15)
        with patch(
            "pyprocore.client.get_project_distribution_group",
            return_value=DistributionGroup(id=16),
        ):
            self.assertEqual(client.distribution_groups.get(123, 16, company_id=456).id, 16)
        with patch(
            "pyprocore.client.find_project_distribution_group",
            return_value=DistributionGroup(id=17),
        ):
            self.assertEqual(
                client.distribution_groups.find(123, company_id=456, name="Team").id,
                17,
            )

        with patch("pyprocore.client.list_locations", return_value=[Location(id=18)]):
            self.assertEqual(client.locations.list(123, company_id=456)[0].id, 18)
        with patch("pyprocore.client.get_location", return_value=Location(id=19)):
            self.assertEqual(client.locations.get(123, 19, company_id=456).id, 19)
        with patch("pyprocore.client.find_location", return_value=Location(id=20)):
            self.assertEqual(client.locations.find(123, company_id=456, code="L1").id, 20)

    def test_workflows_client_delegates_phase8d_exports(self) -> None:
        """Workflows object-client should delegate to Phase 8D export functions."""
        workflows = Procore().workflows
        output = Path("exports/out.csv")
        with patch("pyprocore.client.export_company_users_to_csv", return_value=output):
            self.assertEqual(workflows.export_company_users_to_csv(456, output), output)
        with patch("pyprocore.client.export_company_users_to_jsonl", return_value=output):
            self.assertEqual(workflows.export_company_users_to_jsonl(456, output), output)
        with patch("pyprocore.client.export_project_users_to_csv", return_value=output):
            self.assertEqual(workflows.export_project_users_to_csv(456, 123, output), output)
        with patch("pyprocore.client.export_project_users_to_jsonl", return_value=output):
            self.assertEqual(workflows.export_project_users_to_jsonl(456, 123, output), output)
        with patch("pyprocore.client.export_vendors_to_csv", return_value=output):
            self.assertEqual(workflows.export_vendors_to_csv(456, output), output)
        with patch("pyprocore.client.export_vendors_to_jsonl", return_value=output):
            self.assertEqual(workflows.export_vendors_to_jsonl(456, output), output)
        with patch("pyprocore.client.export_departments_to_csv", return_value=output):
            self.assertEqual(workflows.export_departments_to_csv(456, output), output)
        with patch("pyprocore.client.export_departments_to_jsonl", return_value=output):
            self.assertEqual(workflows.export_departments_to_jsonl(456, output), output)
        with patch("pyprocore.client.export_distribution_groups_to_csv", return_value=output):
            self.assertEqual(workflows.export_distribution_groups_to_csv(456, 123, output), output)
        with patch("pyprocore.client.export_distribution_groups_to_jsonl", return_value=output):
            self.assertEqual(
                workflows.export_distribution_groups_to_jsonl(456, 123, output),
                output,
            )
        with patch("pyprocore.client.export_locations_to_csv", return_value=output):
            self.assertEqual(workflows.export_locations_to_csv(456, 123, output), output)
        with patch("pyprocore.client.export_locations_to_jsonl", return_value=output):
            self.assertEqual(workflows.export_locations_to_jsonl(456, 123, output), output)

    def test_agent_registry_includes_phase8d_metadata(self) -> None:
        """Agent registry should include metadata-only Phase 8D tools."""
        names = {tool.name for tool in list_agent_tools()}
        self.assertIn("procore.list_company_users", names)
        self.assertIn("procore.find_vendor", names)
        self.assertIn("procore.list_project_distribution_groups", names)
        self.assertIn("procore.find_location", names)
        self.assertIn("procore.list_company_users", export_mcp_tools_json())


class Phase8DCliDocsExamplesTestCase(unittest.TestCase):
    """CLI parser, routing, docs, and example tests for Phase 8D."""

    def test_parser_accepts_phase8d_commands(self) -> None:
        """CLI parser should accept new read-only commands."""
        parser = build_parser()
        args = parser.parse_args(
            [
                "find-location",
                "--project",
                "123",
                "--company",
                "456",
                "--name",
                "Level 1",
            ]
        )
        self.assertEqual(args.command, "find-location")
        self.assertEqual(args.company_id, 456)
        self.assertEqual(args.name, "Level 1")

        export_args = parser.parse_args(
            [
                "export-company-users",
                "--company",
                "456",
                "--output",
                "exports/company-users.csv",
            ]
        )
        self.assertEqual(export_args.command, "export-company-users")
        self.assertEqual(export_args.output_path, Path("exports/company-users.csv"))

    def test_run_command_routes_phase8d_commands(self) -> None:
        """run_command should route Phase 8D commands without live HTTP in tests."""
        args = argparse.Namespace(command="locations", company_id=456, project_id=123)
        with patch("pyprocore.app.list_locations", return_value=[Location(id=1)]):
            result = run_command(args)
        self.assertEqual(result[0].id, 1)

        export_args = argparse.Namespace(
            command="export-vendors",
            company_id=456,
            output_path=Path("exports/vendors.csv"),
        )
        with patch("pyprocore.app.export_vendors_to_csv", return_value=Path("exports/vendors.csv")):
            export_result = run_command(export_args)
        self.assertEqual(export_result, Path("exports/vendors.csv"))

    def test_run_command_routes_all_phase8d_service_commands(self) -> None:
        """Each Phase 8D service command should delegate at the CLI boundary."""
        service_cases = [
            (
                argparse.Namespace(command="company-users", company_id=456, inactive=False),
                "list_company_users",
                [CompanyUser(id=1)],
            ),
            (
                argparse.Namespace(command="company-users", company_id=456, inactive=True),
                "list_company_inactive_users",
                [CompanyUser(id=2)],
            ),
            (
                argparse.Namespace(command="company-user", company_id=456, user_id=3),
                "get_company_user",
                CompanyUser(id=3),
            ),
            (
                argparse.Namespace(
                    command="find-company-user",
                    company_id=456,
                    name="Alex",
                    email=None,
                    query=None,
                ),
                "find_company_user",
                CompanyUser(id=4),
            ),
            (
                argparse.Namespace(
                    command="project-users", company_id=456, project_id=123, inactive=False
                ),
                "list_project_users",
                [ProjectUser(id=5)],
            ),
            (
                argparse.Namespace(
                    command="project-user", company_id=456, project_id=123, user_id=6
                ),
                "get_project_user",
                ProjectUser(id=6),
            ),
            (
                argparse.Namespace(
                    command="find-project-user",
                    company_id=456,
                    project_id=123,
                    name="Jordan",
                    email=None,
                    query=None,
                ),
                "find_project_user",
                ProjectUser(id=7),
            ),
            (
                argparse.Namespace(command="vendors", company_id=456, project_id=None),
                "list_vendors",
                [Vendor(id=8)],
            ),
            (
                argparse.Namespace(command="vendors", company_id=456, project_id=123),
                "list_project_vendors",
                [Vendor(id=9)],
            ),
            (
                argparse.Namespace(command="vendor", company_id=456, vendor_id=10),
                "get_vendor",
                Vendor(id=10),
            ),
            (
                argparse.Namespace(
                    command="find-vendor",
                    company_id=456,
                    name="Vendor",
                    number=None,
                    query=None,
                ),
                "find_vendor",
                Vendor(id=11),
            ),
            (
                argparse.Namespace(command="departments", company_id=456),
                "list_departments",
                [Department(id=12)],
            ),
            (
                argparse.Namespace(command="department", company_id=456, department_id=13),
                "get_department",
                Department(id=13),
            ),
            (
                argparse.Namespace(
                    command="find-department",
                    company_id=456,
                    name=None,
                    code="OPS",
                    query=None,
                ),
                "find_department",
                Department(id=14),
            ),
            (
                argparse.Namespace(command="distribution-groups", company_id=456, project_id=123),
                "list_project_distribution_groups",
                [DistributionGroup(id=15)],
            ),
            (
                argparse.Namespace(
                    command="distribution-group",
                    company_id=456,
                    project_id=123,
                    distribution_group_id=16,
                ),
                "get_project_distribution_group",
                DistributionGroup(id=16),
            ),
            (
                argparse.Namespace(
                    command="find-distribution-group",
                    company_id=456,
                    project_id=123,
                    name="Team",
                    query=None,
                ),
                "find_project_distribution_group",
                DistributionGroup(id=17),
            ),
            (
                argparse.Namespace(
                    command="location", company_id=456, project_id=123, location_id=18
                ),
                "get_location",
                Location(id=18),
            ),
            (
                argparse.Namespace(
                    command="find-location",
                    company_id=456,
                    project_id=123,
                    name="Level 1",
                    code=None,
                    query=None,
                ),
                "find_location",
                Location(id=19),
            ),
        ]
        for args, function_name, return_value in service_cases:
            with self.subTest(command=args.command, function_name=function_name):
                with patch(f"pyprocore.app.{function_name}", return_value=return_value):
                    self.assertEqual(run_command(args), return_value)

    def test_run_command_routes_all_phase8d_export_commands(self) -> None:
        """Each Phase 8D export command should delegate at the CLI boundary."""
        output_path = Path("exports/out.csv")
        export_cases = [
            (
                argparse.Namespace(
                    command="export-company-users",
                    company_id=456,
                    output_path=output_path,
                ),
                "export_company_users_to_csv",
            ),
            (
                argparse.Namespace(
                    command="export-project-users",
                    company_id=456,
                    project_id=123,
                    output_path=output_path,
                ),
                "export_project_users_to_csv",
            ),
            (
                argparse.Namespace(
                    command="export-departments",
                    company_id=456,
                    output_path=output_path,
                ),
                "export_departments_to_csv",
            ),
            (
                argparse.Namespace(
                    command="export-distribution-groups",
                    company_id=456,
                    project_id=123,
                    output_path=output_path,
                ),
                "export_distribution_groups_to_csv",
            ),
            (
                argparse.Namespace(
                    command="export-locations",
                    company_id=456,
                    project_id=123,
                    output_path=output_path,
                ),
                "export_locations_to_csv",
            ),
        ]
        for args, function_name in export_cases:
            with self.subTest(command=args.command):
                with patch(f"pyprocore.app.{function_name}", return_value=output_path):
                    self.assertEqual(run_command(args), output_path)

    def test_examples_and_docs_reference_phase8d(self) -> None:
        """Phase 8D examples and docs should be discoverable."""
        project_root = Path(__file__).resolve().parents[1]
        for relative_path in (
            "examples/80_list_company_users.py",
            "examples/81_export_company_users.py",
            "examples/82_list_project_users.py",
            "examples/83_list_vendors.py",
            "examples/84_list_departments.py",
            "examples/85_list_distribution_groups.py",
            "examples/86_list_locations.py",
            "examples/87_agent_registry_phase8d.py",
        ):
            self.assertTrue((project_root / relative_path).exists(), relative_path)

        readme = (project_root / "examples/README.md").read_text(encoding="utf-8")
        roadmap = (project_root / "docs/roadmap.md").read_text(encoding="utf-8")
        cli_docs = (project_root / "docs/cli.md").read_text(encoding="utf-8")
        self.assertIn("87_agent_registry_phase8d.py", readme)
        self.assertIn("Phase 8D", roadmap)
        self.assertIn("company-users", cli_docs)


if __name__ == "__main__":
    unittest.main()
