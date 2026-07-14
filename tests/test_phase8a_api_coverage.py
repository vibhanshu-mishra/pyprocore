"""Tests for Phase 8A read-only API coverage."""

from __future__ import annotations

import argparse
import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pyprocore.agent import list_agent_tools
from pyprocore.app import build_parser, run_command
from pyprocore.client import Procore
from pyprocore.core import endpoints
from pyprocore.core.exceptions import MultipleResultsError
from pyprocore.models import Correspondence, GenericTool, Observation, PunchItem
from pyprocore.services.correspondence import CorrespondenceService
from pyprocore.services.observations import ObservationsService
from pyprocore.services.punch_items import PunchItemsService
from pyprocore.workflows.exports import (
    export_observations_to_csv,
    write_correspondences_csv,
    write_punch_items_csv,
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


class Phase8AEndpointTestCase(unittest.TestCase):
    """Endpoint construction tests for Phase 8A resources."""

    def test_phase8a_endpoint_paths(self) -> None:
        """Endpoint helpers should return read-only collection/item paths."""
        self.assertEqual(endpoints.observations(123), "/rest/v1.0/observations/items")
        self.assertEqual(endpoints.observation(123, 44), "/rest/v1.0/observations/items/44")
        self.assertEqual(endpoints.punch_items(123), "/rest/v1.0/punch_items")
        self.assertEqual(endpoints.punch_item(123, 55), "/rest/v1.0/punch_items/55")
        self.assertEqual(endpoints.generic_tools(123), "/rest/v1.0/generic_tools")
        self.assertEqual(endpoints.generic_tool(123, 66), "/rest/v1.0/generic_tools/66")
        self.assertEqual(
            endpoints.generic_tool_items(123, 66),
            "/rest/v1.0/generic_tools/66/generic_tool_items",
        )
        self.assertEqual(
            endpoints.generic_tool_item(123, 77),
            "/rest/v1.0/generic_tool_items/77",
        )


class Phase8AServiceTestCase(unittest.TestCase):
    """Service tests with mocked HTTP client behavior."""

    def test_list_observations_uses_project_query_and_company_header(self) -> None:
        """Observation list should send project context and company header."""
        fake = FakeClient()
        fake.list_response = [{"id": 1, "number": "OBS-1", "title": "Open ceiling"}]

        observations = ObservationsService(client=fake).list_observations(
            456,
            123,
            status="open",
        )

        self.assertEqual(observations[0].title, "Open ceiling")
        method, path, params, headers = fake.calls[0]
        self.assertEqual(method, "get_all")
        self.assertEqual(path, "/rest/v1.0/observations/items")
        self.assertEqual(params, {"status": "open", "project_id": 123})
        self.assertEqual(headers, {"Procore-Company-Id": "456"})

    def test_get_observation_returns_typed_model(self) -> None:
        """Observation get should parse a typed model."""
        fake = FakeClient()
        fake.get_response = {"id": 2, "number": "OBS-2", "title": "Door issue"}

        observation = ObservationsService(client=fake).get_observation(456, 123, 2)

        self.assertIsInstance(observation, Observation)
        self.assertEqual(fake.calls[0][1], "/rest/v1.0/observations/items/2")

    def test_punch_items_list_and_get(self) -> None:
        """Punch item service should list and get typed models."""
        fake = FakeClient()
        fake.list_response = {"punch_items": [{"id": 3, "number": "P-3", "title": "Paint"}]}
        punch_items = PunchItemsService(client=fake).list_punch_items(456, 123)
        self.assertIsInstance(punch_items[0], PunchItem)
        self.assertEqual(fake.calls[0][1], "/rest/v1.0/punch_items")

        fake.get_response = {"id": 3, "title": "Paint"}
        punch_item = PunchItemsService(client=fake).get_punch_item(456, 123, 3)
        self.assertEqual(punch_item.title, "Paint")
        self.assertEqual(fake.calls[1][1], "/rest/v1.0/punch_items/3")

    def test_correspondence_service_list_and_get_paths(self) -> None:
        """Correspondence service should use Generic Tool read endpoints."""
        fake = FakeClient()
        fake.list_response = [{"id": 7, "name": "Correspondence"}]
        tools = CorrespondenceService(client=fake).list_generic_tools(456, 123)
        self.assertIsInstance(tools[0], GenericTool)
        self.assertEqual(fake.calls[0][1], "/rest/v1.0/generic_tools")

        fake.list_response = {"generic_tool_items": [{"id": 8, "subject": "Question"}]}
        items = CorrespondenceService(client=fake).list_correspondences(456, 123, 7)
        self.assertIsInstance(items[0], Correspondence)
        self.assertEqual(fake.calls[1][1], "/rest/v1.0/generic_tools/7/generic_tool_items")

        fake.get_response = {"id": 8, "subject": "Question"}
        item = CorrespondenceService(client=fake).get_correspondence(456, 123, 8)
        self.assertEqual(item.subject, "Question")
        self.assertEqual(fake.calls[2][1], "/rest/v1.0/generic_tool_items/8")


class Phase8ASearchExportClientTestCase(unittest.TestCase):
    """Search, export, object-client, and agent metadata tests."""

    def test_search_helpers_resolve_matches(self) -> None:
        """Search helpers should resolve typed models from mocked lists."""
        with patch(
            "pyprocore.services.search.list_observations",
            return_value=[Observation(id=1, number="15", title="Wall issue")],
        ):
            from pyprocore.services.search import find_observation

            self.assertEqual(find_observation(456, 123, number="15").id, 1)

        with patch(
            "pyprocore.services.search.list_punch_items",
            return_value=[
                PunchItem(id=1, title="Door hardware"),
                PunchItem(id=2, title="Door frame"),
            ],
        ):
            from pyprocore.services.search import find_punch_item

            with self.assertRaises(MultipleResultsError):
                find_punch_item(456, 123, query="door")

        with patch(
            "pyprocore.services.search.list_correspondences",
            return_value=[Correspondence(id=3, subject="Window question")],
        ):
            from pyprocore.services.search import find_correspondence

            self.assertEqual(find_correspondence(456, 123, 77, title="window").id, 3)

    def test_exports_write_csv_files(self) -> None:
        """Phase 8A export helpers should write local CSV files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "observations.csv"
            with patch(
                "pyprocore.workflows.exports.list_observations",
                return_value=[Observation(id=1, number="OBS-1", title="Ceiling")],
            ):
                saved_path = export_observations_to_csv(456, 123, output_path)

            with saved_path.open(newline="", encoding="utf-8") as file_handle:
                rows = list(csv.DictReader(file_handle))
            self.assertEqual(rows[0]["title"], "Ceiling")

            punch_path = write_punch_items_csv(
                [PunchItem(id=2, number="P-2", title="Paint")],
                Path(temp_dir) / "punch.csv",
            )
            self.assertTrue(punch_path.exists())

            correspondence_path = write_correspondences_csv(
                [Correspondence(id=3, subject="Question")],
                Path(temp_dir) / "correspondences.csv",
            )
            self.assertTrue(correspondence_path.exists())

    def test_object_client_exposes_phase8a_clients(self) -> None:
        """The object client should expose grouped Phase 8A clients."""
        client = Procore()
        self.assertTrue(hasattr(client, "observations"))
        self.assertTrue(hasattr(client, "punch_items"))
        self.assertTrue(hasattr(client, "correspondence"))

    def test_agent_registry_includes_phase8a_metadata(self) -> None:
        """Agent registry should include metadata-only Phase 8A tools."""
        names = {tool.name for tool in list_agent_tools()}
        self.assertIn("procore.list_observations", names)
        self.assertIn("procore.find_punch_item", names)
        self.assertIn("procore.list_correspondences", names)
        self.assertIn("procore.find_correspondence", names)


class Phase8ACliTestCase(unittest.TestCase):
    """CLI parser and routing tests for Phase 8A commands."""

    def test_parser_accepts_phase8a_commands(self) -> None:
        """CLI parser should accept new read-only commands."""
        parser = build_parser()
        args = parser.parse_args(
            [
                "find-correspondence",
                "--project",
                "123",
                "--company",
                "456",
                "--generic-tool-id",
                "77",
                "--query",
                "window",
            ]
        )
        self.assertEqual(args.command, "find-correspondence")
        self.assertEqual(args.company_id, 456)
        self.assertEqual(args.generic_tool_id, 77)

    def test_run_command_routes_observations(self) -> None:
        """run_command should route observation listing without live HTTP in tests."""
        args = argparse.Namespace(
            command="observations",
            company_id=456,
            project_id=123,
            status=None,
            updated_after=None,
            updated_before=None,
            created_after=None,
            created_before=None,
        )
        with patch("pyprocore.app.list_observations", return_value=[Observation(id=1)]):
            result = run_command(args)
        self.assertEqual(result[0].id, 1)

    def test_run_command_routes_correspondence_export(self) -> None:
        """run_command should route correspondence CSV export."""
        output_path = Path("exports/correspondences.csv")
        args = argparse.Namespace(
            command="export-correspondences",
            company_id=456,
            project_id=123,
            generic_tool_id=77,
            output_path=output_path,
            status=None,
            updated_after=None,
            updated_before=None,
            created_after=None,
            created_before=None,
        )
        with patch("pyprocore.app.export_correspondences_to_csv", return_value=output_path):
            result = run_command(args)
        self.assertEqual(result, output_path)


if __name__ == "__main__":
    unittest.main()
