"""Tests for Phase 10D async field, operations, and directory coverage."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

import pyprocore
from pyprocore import AsyncProcore, MockAsyncTransport
from pyprocore.core.async_transport import AsyncResponse
from pyprocore.core.config import ProcoreSettings
from pyprocore.core.exceptions import MultipleResultsError, NotFoundError
from pyprocore.models import (
    CompanyUser,
    Correspondence,
    DailyLogEntry,
    Department,
    DistributionGroup,
    GenericTool,
    Incident,
    IncidentConfiguration,
    Inspection,
    Location,
    Meeting,
    Observation,
    PhotoAlbum,
    PhotoImage,
    ProjectUser,
    PunchItem,
    Vendor,
)
from pyprocore.workflows import async_batch as async_batch_module
from pyprocore.workflows.async_batch import (
    SUPPORTED_ASYNC_BATCH_RESOURCES,
    async_collect_project_resources,
)
from pyprocore.workflows.async_exports import (
    async_export_company_users,
    async_export_correspondences,
    async_export_daily_logs,
    async_export_locations,
    async_export_meetings,
    async_export_observations,
    async_export_photo_albums,
    async_export_photos,
    async_export_punch_items,
    async_export_vendors,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class FakeTokenManager:
    """Token manager test double that never calls Procore."""

    def get_access_token(self, force_refresh: bool = False) -> str:
        """Return a placeholder token."""
        return "placeholder-access-token"


def settings() -> ProcoreSettings:
    """Return local async test settings."""
    return ProcoreSettings(
        client_id="client-id",
        client_secret="client-secret",
        redirect_uri="http://localhost/callback",
        login_url="https://login.example.com",
        api_base="https://api.example.com",
        company_id=123,
    )


def json_response(payload: Any) -> AsyncResponse:
    """Build a successful JSON async response."""
    return AsyncResponse(
        status_code=200,
        url="https://api.example.com/rest/v1.0/example",
        headers={"Content-Type": "application/json"},
        json_data=payload,
        content=b"{}",
    )


def async_client(responses: list[AsyncResponse]) -> tuple[AsyncProcore, MockAsyncTransport]:
    """Build an async client backed by mock responses."""
    transport = MockAsyncTransport(responses)
    return (
        AsyncProcore(
            settings=settings(),
            token_manager=FakeTokenManager(),  # type: ignore[arg-type]
            transport=transport,
            retry_sleep_seconds=0,
        ),
        transport,
    )


class Phase10DAsyncClientCoverageTests(unittest.IsolatedAsyncioTestCase):
    """Validate Phase 10D async resources with mock transports only."""

    async def test_async_photos_and_daily_logs_use_typed_models(self) -> None:
        """Photo and Daily Log async methods should return typed models."""
        client, transport = async_client(
            [
                json_response([{"id": 1, "name": "Album"}]),
                json_response({"id": 1, "name": "Album"}),
                json_response([{"id": 2, "filename": "site.jpg"}]),
                json_response({"id": 2, "filename": "site.jpg"}),
                json_response([{"id": 3, "log_type": "manpower", "comments": "Crew"}]),
            ]
        )

        albums = await client.list_photo_albums(123, 456)
        album = await client.get_photo_album(123, 456, 1)
        photos = await client.list_photos(123, 456, album_id=1)
        photo = await client.get_photo(123, 456, 2)
        logs = await client.list_daily_logs(123, 456, "manpower")

        self.assertIsInstance(albums[0], PhotoAlbum)
        self.assertIsInstance(album, PhotoAlbum)
        self.assertIsInstance(photos[0], PhotoImage)
        self.assertIsInstance(photo, PhotoImage)
        self.assertIsInstance(logs[0], DailyLogEntry)
        self.assertEqual(
            transport.requests[0].url, "https://api.example.com/rest/v1.0/image_categories"
        )
        self.assertEqual(transport.requests[0].params["project_id"], 456)
        self.assertEqual(transport.requests[0].headers["Procore-Company-Id"], "123")

    async def test_async_observations_and_punch_items_list_get_find(self) -> None:
        """Observation and punch item async methods should list, get, and find."""
        client, _ = async_client(
            [
                json_response({"observations": [{"id": 10, "number": "OBS-1", "title": "Door"}]}),
                json_response({"id": 10, "number": "OBS-1", "title": "Door"}),
                json_response([{"id": 10, "number": "OBS-1", "title": "Door"}]),
                json_response({"punch_items": [{"id": 20, "number": "P-1", "title": "Wall"}]}),
                json_response({"id": 20, "number": "P-1", "title": "Wall"}),
                json_response([{"id": 20, "number": "P-1", "title": "Wall"}]),
            ]
        )

        observations = await client.list_observations(123, 456)
        observation = await client.get_observation(123, 456, 10)
        found_observation = await client.find_observation(123, 456, number="OBS-1")
        punch_items = await client.list_punch_items(123, 456)
        punch_item = await client.get_punch_item(123, 456, 20)
        found_punch_item = await client.find_punch_item(123, 456, query="wall")

        self.assertIsInstance(observations[0], Observation)
        self.assertIsInstance(observation, Observation)
        self.assertEqual(found_observation.id, 10)
        self.assertIsInstance(punch_items[0], PunchItem)
        self.assertIsInstance(punch_item, PunchItem)
        self.assertEqual(found_punch_item.id, 20)

    async def test_async_find_raises_clear_errors(self) -> None:
        """Async find helpers should raise custom not-found and multiple-results errors."""
        missing, _ = async_client([json_response([])])
        duplicate, _ = async_client(
            [
                json_response(
                    [
                        {"id": 1, "number": "OBS-1", "title": "Door"},
                        {"id": 2, "number": "OBS-1", "title": "Door"},
                    ]
                )
            ]
        )

        with self.assertRaises(NotFoundError):
            await missing.find_observation(123, 456, number="missing")
        with self.assertRaises(MultipleResultsError):
            await duplicate.find_observation(123, 456, number="OBS-1")

    async def test_async_correspondence_and_operations(self) -> None:
        """Generic Tools, correspondence, and operations should use typed models."""
        client, _ = async_client(
            [
                json_response([{"id": 31, "name": "Notice"}]),
                json_response({"id": 31, "name": "Notice"}),
                json_response({"generic_tool_items": [{"id": 32, "number": "C-1"}]}),
                json_response({"id": 32, "number": "C-1"}),
                json_response([{"id": 32, "number": "C-1"}]),
                json_response({"meetings": [{"id": 41, "title": "OAC"}]}),
                json_response({"id": 41, "title": "OAC"}),
                json_response([{"id": 41, "title": "OAC"}]),
                json_response({"checklists": [{"id": 42, "title": "Safety"}]}),
                json_response({"id": 42, "title": "Safety"}),
                json_response([{"id": 42, "title": "Safety"}]),
                json_response({"incidents": [{"id": 43, "title": "Near Miss"}]}),
                json_response({"id": 43, "title": "Near Miss"}),
                json_response([{"id": 43, "title": "Near Miss"}]),
                json_response({"project_id": 456, "enabled": True}),
            ]
        )

        tools = await client.list_generic_tools(123, 456)
        tool = await client.get_generic_tool(123, 456, 31)
        correspondences = await client.list_correspondences(123, 456, 31)
        correspondence = await client.get_correspondence(123, 456, 31, 32)
        found_correspondence = await client.find_correspondence(123, 456, 31, number="C-1")
        meetings = await client.list_meetings(123, 456)
        meeting = await client.get_meeting(123, 456, 41)
        found_meeting = await client.find_meeting(123, 456, title="OAC")
        inspections = await client.list_inspections(123, 456)
        inspection = await client.get_inspection(123, 456, 42)
        found_inspection = await client.find_inspection(123, 456, query="safety")
        incidents = await client.list_incidents(123, 456)
        incident = await client.get_incident(123, 456, 43)
        found_incident = await client.find_incident(123, 456, title="Near Miss")
        configuration = await client.get_project_incident_configuration(123, 456)

        self.assertIsInstance(tools[0], GenericTool)
        self.assertIsInstance(tool, GenericTool)
        self.assertIsInstance(correspondences[0], Correspondence)
        self.assertIsInstance(correspondence, Correspondence)
        self.assertEqual(found_correspondence.id, 32)
        self.assertIsInstance(meetings[0], Meeting)
        self.assertIsInstance(meeting, Meeting)
        self.assertEqual(found_meeting.id, 41)
        self.assertIsInstance(inspections[0], Inspection)
        self.assertIsInstance(inspection, Inspection)
        self.assertEqual(found_inspection.id, 42)
        self.assertIsInstance(incidents[0], Incident)
        self.assertIsInstance(incident, Incident)
        self.assertEqual(found_incident.id, 43)
        self.assertIsInstance(configuration, IncidentConfiguration)

    async def test_async_directory_resources_list_get_find(self) -> None:
        """Directory async methods should return typed directory models."""
        client, _ = async_client(
            [
                json_response(
                    {"users": [{"id": 51, "name": "Casey", "email": "casey@example.com"}]}
                ),
                json_response({"id": 51, "name": "Casey"}),
                json_response([{"id": 51, "name": "Casey"}]),
                json_response({"project_users": [{"id": 52, "name": "Jordan"}]}),
                json_response({"id": 52, "name": "Jordan"}),
                json_response([{"id": 52, "name": "Jordan"}]),
                json_response([{"id": 53, "name": "Vendor One"}]),
                json_response({"id": 53, "name": "Vendor One"}),
                json_response([{"id": 53, "name": "Vendor One"}]),
                json_response([{"id": 54, "name": "Operations"}]),
                json_response({"id": 54, "name": "Operations"}),
                json_response([{"id": 54, "name": "Operations"}]),
                json_response({"distribution_groups": [{"id": 55, "name": "Field Team"}]}),
                json_response({"id": 55, "name": "Field Team"}),
                json_response([{"id": 55, "name": "Field Team"}]),
                json_response([{"id": 56, "name": "Level 1"}]),
                json_response({"id": 56, "name": "Level 1"}),
                json_response([{"id": 56, "name": "Level 1"}]),
            ]
        )

        company_users = await client.list_company_users(123)
        company_user = await client.get_company_user(123, 51)
        found_company_user = await client.find_company_user(123, name="Casey")
        project_users = await client.list_project_users(123, 456)
        project_user = await client.get_project_user(123, 456, 52)
        found_project_user = await client.find_project_user(123, 456, query="Jordan")
        vendors = await client.list_vendors(123)
        vendor = await client.get_vendor(123, 53)
        found_vendor = await client.find_vendor(123, name="Vendor One")
        departments = await client.list_departments(123)
        department = await client.get_department(123, 54)
        found_department = await client.find_department(123, name="Operations")
        groups = await client.list_project_distribution_groups(123, 456)
        group = await client.get_project_distribution_group(123, 456, 55)
        found_group = await client.find_project_distribution_group(123, 456, name="Field Team")
        locations = await client.list_locations(123, 456)
        location = await client.get_location(123, 456, 56)
        found_location = await client.find_location(123, 456, name="Level 1")

        self.assertIsInstance(company_users[0], CompanyUser)
        self.assertIsInstance(company_user, CompanyUser)
        self.assertEqual(found_company_user.id, 51)
        self.assertIsInstance(project_users[0], ProjectUser)
        self.assertIsInstance(project_user, ProjectUser)
        self.assertEqual(found_project_user.id, 52)
        self.assertIsInstance(vendors[0], Vendor)
        self.assertIsInstance(vendor, Vendor)
        self.assertEqual(found_vendor.id, 53)
        self.assertIsInstance(departments[0], Department)
        self.assertIsInstance(department, Department)
        self.assertEqual(found_department.id, 54)
        self.assertIsInstance(groups[0], DistributionGroup)
        self.assertIsInstance(group, DistributionGroup)
        self.assertEqual(found_group.id, 55)
        self.assertIsInstance(locations[0], Location)
        self.assertIsInstance(location, Location)
        self.assertEqual(found_location.id, 56)

    async def test_async_grouped_clients_delegate_to_owner_methods(self) -> None:
        """Grouped async clients should expose beginner-friendly namespaces."""
        client, _ = async_client(
            [
                json_response([{"id": 1, "name": "Album"}]),
                json_response([{"id": 2, "number": "OBS-1"}]),
                json_response([{"id": 3, "number": "P-1"}]),
                json_response([{"id": 4, "name": "Notice"}]),
                json_response([{"id": 5, "title": "OAC"}]),
                json_response([{"id": 6, "name": "Vendor"}]),
            ]
        )

        self.assertEqual((await client.photos.list_albums(123, 456))[0].id, 1)
        self.assertEqual((await client.observations.list(123, 456))[0].id, 2)
        self.assertEqual((await client.punch_items.list(123, 456))[0].id, 3)
        self.assertEqual((await client.correspondence.list_generic_tools(123, 456))[0].id, 4)
        self.assertEqual((await client.operations.list_meetings(123, 456))[0].id, 5)
        self.assertEqual((await client.directory.list_vendors(123))[0].id, 6)


class Phase10DAsyncWorkflowTests(unittest.IsolatedAsyncioTestCase):
    """Validate Phase 10D async exports and batch support."""

    async def test_phase10d_async_exports_write_local_jsonl(self) -> None:
        """New async export helpers should write local files from mock responses."""
        client, _ = async_client(
            [
                json_response([{"id": 1, "name": "Album"}]),
                json_response([{"id": 2, "filename": "site.jpg"}]),
                json_response([{"id": 3, "comments": "Crew"}]),
                json_response([{"id": 4, "number": "OBS-1"}]),
                json_response([{"id": 5, "number": "P-1"}]),
                json_response([{"id": 6, "title": "Meeting"}]),
                json_response([{"id": 7, "name": "User"}]),
                json_response([{"id": 8, "name": "Vendor"}]),
                json_response([{"id": 9, "name": "Location"}]),
                json_response([{"id": 10, "number": "C-1"}]),
            ]
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            results = [
                await async_export_photo_albums(client, 123, 456, root / "albums.jsonl"),
                await async_export_photos(client, 123, 456, root / "photos.jsonl"),
                await async_export_daily_logs(client, 123, 456, root / "logs.jsonl"),
                await async_export_observations(client, 123, 456, root / "observations.jsonl"),
                await async_export_punch_items(client, 123, 456, root / "punch.jsonl"),
                await async_export_meetings(client, 123, 456, root / "meetings.jsonl"),
                await async_export_company_users(client, 123, root / "users.jsonl"),
                await async_export_vendors(client, 123, root / "vendors.jsonl"),
                await async_export_locations(client, 123, 456, root / "locations.jsonl"),
                await async_export_correspondences(client, 123, 456, 31, root / "corr.jsonl"),
            ]

            self.assertEqual([result.record_count for result in results], [1] * 10)
            self.assertEqual(
                json.loads((root / "observations.jsonl").read_text().splitlines()[0])["id"], 4
            )

    async def test_phase10d_async_batch_supported_resources_fetch(self) -> None:
        """Async batch should support the Phase 10D resource names."""

        class FakeAsyncClient:
            async def list_observations(
                self, company_id: int, project_id: int
            ) -> list[dict[str, int]]:
                return [{"company_id": company_id, "project_id": project_id, "id": 1}]

            async def list_punch_items(
                self, company_id: int, project_id: int
            ) -> list[dict[str, int]]:
                return [{"company_id": company_id, "project_id": project_id, "id": 2}]

            async def list_meetings(self, company_id: int, project_id: int) -> list[dict[str, int]]:
                return [{"company_id": company_id, "project_id": project_id, "id": 3}]

            async def list_inspections(
                self, company_id: int, project_id: int
            ) -> list[dict[str, int]]:
                return [{"company_id": company_id, "project_id": project_id, "id": 4}]

            async def list_incidents(
                self, company_id: int, project_id: int
            ) -> list[dict[str, int]]:
                return [{"company_id": company_id, "project_id": project_id, "id": 5}]

            async def list_locations(
                self, company_id: int, project_id: int
            ) -> list[dict[str, int]]:
                return [{"company_id": company_id, "project_id": project_id, "id": 6}]

            async def list_project_users(
                self,
                company_id: int,
                project_id: int,
            ) -> list[dict[str, int]]:
                return [{"company_id": company_id, "project_id": project_id, "id": 7}]

            async def list_vendors(self, company_id: int) -> list[dict[str, int]]:
                return [{"company_id": company_id, "id": 8}]

        resources = [
            "observations",
            "punch_items",
            "meetings",
            "inspections",
            "incidents",
            "locations",
            "project_users",
            "vendors",
        ]

        manifest = await async_collect_project_resources(
            FakeAsyncClient(),  # type: ignore[arg-type]
            123,
            456,
            resources,
        )

        self.assertTrue(set(resources).issubset(SUPPORTED_ASYNC_BATCH_RESOURCES))
        self.assertEqual(len(manifest), 8)
        self.assertEqual({result.resource for result in manifest}, set(resources))

    def test_safety_boundaries_remain_read_only(self) -> None:
        """Phase 10D should not expose write helpers or enable agent/MCP execution."""
        forbidden_prefixes = ("create_", "update_", "delete_", "upload_", "approve_")
        self.assertFalse(
            [name for name in pyprocore.async_client.__all__ if name.startswith(forbidden_prefixes)]
        )
        self.assertFalse(
            [
                name
                for name in async_batch_module.__all__
                if name.startswith(forbidden_prefixes) and name != "write_async_batch_manifest"
            ]
        )
        response = pyprocore.build_mcp_tool_execution_disabled_response("list_observations")
        self.assertIn("disabled", json.dumps(response).lower())

    def test_phase10d_docs_and_exports_are_discoverable(self) -> None:
        """Docs and root exports should mention the Phase 10D async surface."""
        examples_readme = (PROJECT_ROOT / "examples" / "README.md").read_text(encoding="utf-8")
        async_docs = (PROJECT_ROOT / "docs" / "async-client.md").read_text(encoding="utf-8")

        self.assertIn("161_async_observations_and_punch_items.py", examples_readme)
        self.assertIn("168_phase10d_async_coverage_summary.py", examples_readme)
        self.assertIn("Phase 10D", async_docs)
        self.assertIn("async_export_observations", async_docs)
        self.assertTrue(hasattr(pyprocore, "async_export_observations"))
        self.assertTrue(hasattr(pyprocore, "AsyncDirectoryClient"))


if __name__ == "__main__":
    unittest.main()
