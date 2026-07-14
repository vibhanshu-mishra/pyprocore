"""Tests for Phase 8C read-only meetings, inspections, and incidents."""

from __future__ import annotations

import argparse
import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pyprocore.agent import (
    export_agent_openapi_json,
    export_agent_tool_schemas_json,
    export_mcp_tools_json,
    list_agent_tools,
)
from pyprocore.app import build_parser, run_command
from pyprocore.client import Procore
from pyprocore.core import endpoints
from pyprocore.core.exceptions import MultipleResultsError
from pyprocore.models import Incident, IncidentConfiguration, Inspection, Meeting
from pyprocore.services.operations import OperationsService
from pyprocore.services.operations import get_incident as get_incident_wrapper
from pyprocore.services.operations import get_inspection as get_inspection_wrapper
from pyprocore.services.operations import get_meeting as get_meeting_wrapper
from pyprocore.services.operations import list_incidents as list_incidents_wrapper
from pyprocore.services.operations import list_inspections as list_inspections_wrapper
from pyprocore.services.operations import list_meetings as list_meetings_wrapper
from pyprocore.workflows.exports import (
    export_incidents_to_jsonl,
    export_inspections_to_jsonl,
    export_meetings_to_csv,
    export_meetings_to_jsonl,
    write_incidents_csv,
    write_inspections_csv,
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


class Phase8CEndpointTestCase(unittest.TestCase):
    """Endpoint construction tests for Phase 8C resources."""

    def test_phase8c_endpoint_paths(self) -> None:
        """Endpoint helpers should return read-only collection/item paths."""
        self.assertEqual(endpoints.meetings(123), "/rest/v1.0/meetings")
        self.assertEqual(endpoints.meeting(123, 44), "/rest/v1.0/meetings/44")
        self.assertEqual(endpoints.inspections(123), "/rest/v1.0/checklists")
        self.assertEqual(endpoints.inspection(123, 55), "/rest/v1.0/checklists/55")
        self.assertEqual(endpoints.incidents(123), "/rest/v1.0/incidents")
        self.assertEqual(endpoints.incident(123, 66), "/rest/v1.0/incidents/66")
        self.assertEqual(
            endpoints.project_incident_configuration(123),
            "/rest/v1.0/projects/123/incident_configuration",
        )


class Phase8CServiceTestCase(unittest.TestCase):
    """Service tests with mocked HTTP client behavior."""

    def test_list_meetings_uses_project_query_and_company_header(self) -> None:
        """Meeting list should send project context and company header."""
        fake = FakeClient()
        fake.list_response = {"meetings": [{"id": 1, "number": "M-1", "title": "OAC"}]}

        meetings = OperationsService(client=fake).list_meetings(456, 123, status="open")

        self.assertIsInstance(meetings[0], Meeting)
        self.assertEqual(meetings[0].title, "OAC")
        method, path, params, headers = fake.calls[0]
        self.assertEqual(method, "get_all")
        self.assertEqual(path, "/rest/v1.0/meetings")
        self.assertEqual(params, {"status": "open", "project_id": 123})
        self.assertEqual(headers, {"Procore-Company-Id": "456"})

    def test_get_meeting_returns_typed_model(self) -> None:
        """Meeting get should parse a typed model."""
        fake = FakeClient()
        fake.get_response = {"id": 2, "number": "M-2", "title": "Safety"}

        meeting = OperationsService(client=fake).get_meeting(456, 123, 2)

        self.assertIsInstance(meeting, Meeting)
        self.assertEqual(fake.calls[0][1], "/rest/v1.0/meetings/2")

    def test_inspections_list_and_get_use_checklist_paths(self) -> None:
        """Inspection helpers should use checklist-backed read paths."""
        fake = FakeClient()
        fake.list_response = {"checklists": [{"id": 3, "title": "Pre-pour"}]}
        inspections = OperationsService(client=fake).list_inspections(456, 123)
        self.assertIsInstance(inspections[0], Inspection)
        self.assertEqual(fake.calls[0][1], "/rest/v1.0/checklists")
        self.assertEqual(fake.calls[0][2], {"project_id": 123})

        fake.get_response = {"id": 3, "title": "Pre-pour"}
        inspection = OperationsService(client=fake).get_inspection(456, 123, 3)
        self.assertEqual(inspection.title, "Pre-pour")
        self.assertEqual(fake.calls[1][1], "/rest/v1.0/checklists/3")

    def test_incidents_list_get_and_configuration_paths(self) -> None:
        """Incident helpers should use read-only incident paths."""
        fake = FakeClient()
        fake.list_response = [{"id": 4, "number": "I-4", "title": "Near miss"}]
        incidents = OperationsService(client=fake).list_incidents(456, 123)
        self.assertIsInstance(incidents[0], Incident)
        self.assertEqual(fake.calls[0][1], "/rest/v1.0/incidents")

        fake.get_response = {"id": 4, "title": "Near miss"}
        incident = OperationsService(client=fake).get_incident(456, 123, 4)
        self.assertEqual(incident.title, "Near miss")
        self.assertEqual(fake.calls[1][1], "/rest/v1.0/incidents/4")

        fake.get_response = {"id": 5, "project_id": 123, "enabled": True}
        configuration = OperationsService(client=fake).get_project_incident_configuration(456, 123)
        self.assertIsInstance(configuration, IncidentConfiguration)
        self.assertEqual(fake.calls[2][1], "/rest/v1.0/projects/123/incident_configuration")

    def test_module_level_wrappers_accept_injected_clients(self) -> None:
        """Module-level service wrappers should preserve injected-client behavior."""
        fake = FakeClient()
        fake.list_response = [{"id": 1, "title": "Weekly"}]
        self.assertEqual(list_meetings_wrapper(456, 123, client=fake)[0].title, "Weekly")

        fake.list_response = [{"id": 2, "title": "Safety"}]
        self.assertEqual(list_inspections_wrapper(456, 123, client=fake)[0].title, "Safety")

        fake.list_response = [{"id": 3, "title": "Near miss"}]
        self.assertEqual(list_incidents_wrapper(456, 123, client=fake)[0].title, "Near miss")

        fake.get_response = {"id": 4, "title": "Meeting"}
        self.assertEqual(get_meeting_wrapper(456, 123, 4, client=fake).title, "Meeting")

        fake.get_response = {"id": 5, "title": "Inspection"}
        self.assertEqual(get_inspection_wrapper(456, 123, 5, client=fake).title, "Inspection")

        fake.get_response = {"id": 6, "title": "Incident"}
        self.assertEqual(get_incident_wrapper(456, 123, 6, client=fake).title, "Incident")


class Phase8CSearchExportClientTestCase(unittest.TestCase):
    """Search, export, object-client, and agent metadata tests."""

    def test_search_helpers_resolve_matches(self) -> None:
        """Search helpers should resolve typed models from mocked lists."""
        with patch(
            "pyprocore.services.search.list_meetings",
            return_value=[Meeting(id=1, number="1", title="Weekly")],
        ):
            from pyprocore.services.search import find_meeting

            self.assertEqual(find_meeting(456, 123, number="1").id, 1)

        with patch(
            "pyprocore.services.search.list_inspections",
            return_value=[
                Inspection(id=1, title="Safety check"),
                Inspection(id=2, title="Safety walk"),
            ],
        ):
            from pyprocore.services.search import find_inspection

            with self.assertRaises(MultipleResultsError):
                find_inspection(456, 123, query="safety")

        with patch(
            "pyprocore.services.search.list_incidents",
            return_value=[Incident(id=3, number="INC-3", title="Near miss")],
        ):
            from pyprocore.services.search import find_incident

            self.assertEqual(find_incident(456, 123, query="near").id, 3)

    def test_exports_write_csv_files(self) -> None:
        """Phase 8C export helpers should write local CSV files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "meetings.csv"
            with patch(
                "pyprocore.workflows.exports.list_meetings",
                return_value=[Meeting(id=1, number="M-1", title="OAC")],
            ):
                saved_path = export_meetings_to_csv(456, 123, output_path)

            with saved_path.open(newline="", encoding="utf-8") as file_handle:
                rows = list(csv.DictReader(file_handle))
            self.assertEqual(rows[0]["title"], "OAC")

            inspection_path = write_inspections_csv(
                [Inspection(id=2, number="CHK-2", title="Safety")],
                Path(temp_dir) / "inspections.csv",
            )
            self.assertTrue(inspection_path.exists())

            incident_path = write_incidents_csv(
                [Incident(id=3, number="INC-3", title="Near miss")],
                Path(temp_dir) / "incidents.csv",
            )
            self.assertTrue(incident_path.exists())

    def test_jsonl_exports_write_files(self) -> None:
        """Phase 8C JSONL export helpers should write local files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch(
                "pyprocore.workflows.exports.list_meetings",
                return_value=[Meeting(id=1, title="Weekly")],
            ):
                meetings_path = export_meetings_to_jsonl(
                    456,
                    123,
                    Path(temp_dir) / "meetings.jsonl",
                )
            self.assertIn('"title": "Weekly"', meetings_path.read_text(encoding="utf-8"))

            with patch(
                "pyprocore.workflows.exports.list_inspections",
                return_value=[Inspection(id=2, title="Safety")],
            ):
                inspections_path = export_inspections_to_jsonl(
                    456,
                    123,
                    Path(temp_dir) / "inspections.jsonl",
                )
            self.assertIn('"title": "Safety"', inspections_path.read_text(encoding="utf-8"))

            with patch(
                "pyprocore.workflows.exports.list_incidents",
                return_value=[Incident(id=3, title="Near miss")],
            ):
                incidents_path = export_incidents_to_jsonl(
                    456,
                    123,
                    Path(temp_dir) / "incidents.jsonl",
                )
            self.assertIn('"title": "Near miss"', incidents_path.read_text(encoding="utf-8"))

    def test_object_client_exposes_phase8c_clients(self) -> None:
        """The object client should expose grouped Phase 8C clients."""
        client = Procore()
        self.assertTrue(hasattr(client, "meetings"))
        self.assertTrue(hasattr(client, "inspections"))
        self.assertTrue(hasattr(client, "incidents"))

    def test_object_client_phase8c_methods_delegate_to_services(self) -> None:
        """Object client groups should delegate to Phase 8C service helpers."""
        client = Procore()
        configuration = IncidentConfiguration(id=1, project_id=123, enabled=True)
        with (
            patch("pyprocore.client.list_meetings", return_value=[Meeting(id=1)]) as list_meetings,
            patch("pyprocore.client.get_meeting", return_value=Meeting(id=2)) as get_meeting,
            patch("pyprocore.client.find_meeting", return_value=Meeting(id=3)) as find_meeting,
            patch(
                "pyprocore.client.list_inspections",
                return_value=[Inspection(id=4)],
            ) as list_inspections,
            patch(
                "pyprocore.client.get_inspection",
                return_value=Inspection(id=5),
            ) as get_inspection,
            patch(
                "pyprocore.client.find_inspection",
                return_value=Inspection(id=6),
            ) as find_inspection,
            patch(
                "pyprocore.client.list_incidents", return_value=[Incident(id=7)]
            ) as list_incidents,
            patch("pyprocore.client.get_incident", return_value=Incident(id=8)) as get_incident,
            patch(
                "pyprocore.client.get_project_incident_configuration",
                return_value=configuration,
            ) as get_configuration,
            patch("pyprocore.client.find_incident", return_value=Incident(id=9)) as find_incident,
        ):
            self.assertEqual(client.meetings.list(456, 123)[0].id, 1)
            self.assertEqual(client.meetings.get(456, 123, 2).id, 2)
            self.assertEqual(client.meetings.find(456, 123, query="weekly").id, 3)
            self.assertEqual(client.inspections.list(456, 123)[0].id, 4)
            self.assertEqual(client.inspections.get(456, 123, 5).id, 5)
            self.assertEqual(client.inspections.find(456, 123, query="safety").id, 6)
            self.assertEqual(client.incidents.list(456, 123)[0].id, 7)
            self.assertEqual(client.incidents.get(456, 123, 8).id, 8)
            self.assertEqual(client.incidents.configuration(456, 123).project_id, 123)
            self.assertEqual(client.incidents.find(456, 123, query="near").id, 9)

        list_meetings.assert_called_once()
        get_meeting.assert_called_once()
        find_meeting.assert_called_once()
        list_inspections.assert_called_once()
        get_inspection.assert_called_once()
        find_inspection.assert_called_once()
        list_incidents.assert_called_once()
        get_incident.assert_called_once()
        get_configuration.assert_called_once()
        find_incident.assert_called_once()

    def test_agent_registry_and_schema_exports_include_phase8c_metadata(self) -> None:
        """Agent registry exports should include metadata-only Phase 8C tools."""
        names = {tool.name for tool in list_agent_tools()}
        self.assertIn("procore.list_meetings", names)
        self.assertIn("procore.find_inspection", names)
        self.assertIn("procore.get_project_incident_configuration", names)
        self.assertIn("procore.find_incident", names)

        openapi = json.loads(export_agent_openapi_json())
        self.assertIn("/agent/tools/{tool_name}", openapi["paths"])
        self.assertIn("AgentTool", openapi["components"]["schemas"])

        schemas = json.loads(export_agent_tool_schemas_json())
        self.assertIn("procore.list_inspections", schemas["tools"])

        mcp_tools = json.loads(export_mcp_tools_json())
        mcp_names = {tool["name"] for tool in mcp_tools}
        self.assertIn("procore.list_incidents", mcp_names)


class Phase8CCliTestCase(unittest.TestCase):
    """CLI parser and routing tests for Phase 8C commands."""

    def test_parser_accepts_phase8c_commands(self) -> None:
        """CLI parser should accept new read-only commands."""
        parser = build_parser()
        args = parser.parse_args(
            [
                "find-inspection",
                "--project",
                "123",
                "--company",
                "456",
                "--query",
                "safety",
            ]
        )
        self.assertEqual(args.command, "find-inspection")
        self.assertEqual(args.company_id, 456)
        self.assertEqual(args.query, "safety")

    def test_run_command_routes_meetings(self) -> None:
        """run_command should route meeting listing without live HTTP in tests."""
        args = argparse.Namespace(
            command="meetings",
            company_id=456,
            project_id=123,
            status=None,
            updated_after=None,
            updated_before=None,
            created_after=None,
            created_before=None,
        )
        with patch("pyprocore.app.list_meetings", return_value=[Meeting(id=1)]):
            result = run_command(args)
        self.assertEqual(result[0].id, 1)

    def test_run_command_routes_incident_configuration(self) -> None:
        """run_command should route incident configuration lookups."""
        args = argparse.Namespace(
            command="incident-configuration",
            company_id=456,
            project_id=123,
        )
        configuration = IncidentConfiguration(id=1, project_id=123, enabled=True)
        with patch(
            "pyprocore.app.get_project_incident_configuration",
            return_value=configuration,
        ):
            result = run_command(args)
        self.assertEqual(result.project_id, 123)

    def test_run_command_routes_incident_export(self) -> None:
        """run_command should route incident CSV export."""
        output_path = Path("exports/incidents.csv")
        args = argparse.Namespace(
            command="export-incidents",
            company_id=456,
            project_id=123,
            output_path=output_path,
            status=None,
            updated_after=None,
            updated_before=None,
            created_after=None,
            created_before=None,
        )
        with patch("pyprocore.app.export_incidents_to_csv", return_value=output_path):
            result = run_command(args)
        self.assertEqual(result, output_path)


if __name__ == "__main__":
    unittest.main()
