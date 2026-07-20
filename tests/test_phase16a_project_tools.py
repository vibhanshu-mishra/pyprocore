"""Tests for Phase 16A read-only Project Tools coverage."""

from __future__ import annotations

import argparse
import unittest
from unittest.mock import patch

from pyprocore.agent import get_agent_tool
from pyprocore.app import run_command
from pyprocore.client import Procore
from pyprocore.core import endpoints
from pyprocore.core.exceptions import DuplicateMatchError, NotFoundError, ValidationError
from pyprocore.models import ProjectTool
from pyprocore.services.project_tools import (
    ProjectToolsService,
    find_project_tool,
    get_project_tool,
    list_project_tools,
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


class Phase16AProjectToolsTestCase(unittest.TestCase):
    """Project Tools endpoint and service tests."""

    def test_project_tools_endpoint_paths(self) -> None:
        """Endpoint helpers should return project-scoped read-only paths."""
        self.assertEqual(endpoints.project_tools(123), "/rest/v1.0/projects/123/tools")
        self.assertEqual(endpoints.project_tool(123, 7), "/rest/v1.0/projects/123/tools/7")

    def test_list_project_tools_uses_headers_filters_and_typed_models(self) -> None:
        """Project Tools listing should use GET-only client behavior."""
        fake = FakeClient()
        fake.list_response = {
            "tools": [
                {
                    "id": 1,
                    "name": "RFIs",
                    "slug": "rfis",
                    "active": True,
                    "mobile": True,
                }
            ]
        }

        tools = ProjectToolsService(client=fake).list_project_tools(
            123,
            company_id=456,
            active=True,
            mobile=True,
            configurable=True,
        )

        self.assertIsInstance(tools[0], ProjectTool)
        self.assertEqual(tools[0].name, "RFIs")
        self.assertEqual(fake.calls[0][0], "get_all")
        self.assertEqual(fake.calls[0][1], "/rest/v1.0/projects/123/tools")
        self.assertEqual(
            fake.calls[0][2],
            {"active": True, "mobile": True, "configurable": True},
        )
        self.assertEqual(fake.calls[0][3], {"Procore-Company-Id": "456"})

    def test_get_project_tool_returns_typed_model(self) -> None:
        """Project Tool get should use the project-scoped show path."""
        fake = FakeClient()
        fake.get_response = {"id": 7, "name": "Drawings", "slug": "drawings"}

        tool = ProjectToolsService(client=fake).get_project_tool(123, 7, company_id=456)

        self.assertIsInstance(tool, ProjectTool)
        self.assertEqual(tool.slug, "drawings")
        self.assertEqual(fake.calls[0][0], "get")
        self.assertEqual(fake.calls[0][1], "/rest/v1.0/projects/123/tools/7")
        self.assertEqual(fake.calls[0][3], {"Procore-Company-Id": "456"})

    def test_find_project_tool_matches_case_insensitive_names(self) -> None:
        """Project Tool find should match common label fields case-insensitively."""
        fake = FakeClient()
        fake.list_response = [
            {"id": 1, "name": "RFIs", "slug": "rfis"},
            {"id": 2, "title": "Submittals", "slug": "submittals"},
        ]

        tool = ProjectToolsService(client=fake).find_project_tool(123, "submittals", 456)

        self.assertEqual(tool.id, 2)

    def test_find_project_tool_raises_custom_errors(self) -> None:
        """Project Tool find should report missing and duplicate matches clearly."""
        fake = FakeClient()
        fake.list_response = [{"id": 1, "name": "RFIs"}, {"id": 2, "title": "RFIs"}]
        service = ProjectToolsService(client=fake)

        with self.assertRaises(DuplicateMatchError):
            service.find_project_tool(123, "RFIs", 456)

        fake.list_response = [{"id": 1, "name": "RFIs"}]
        with self.assertRaises(NotFoundError):
            service.find_project_tool(123, "Drawings", 456)

        with self.assertRaises(ValidationError):
            service.find_project_tool(123, " ", 456)

    def test_module_wrappers_accept_injected_clients(self) -> None:
        """Module-level wrappers should preserve injected-client behavior."""
        fake = FakeClient()
        fake.list_response = [{"id": 1, "name": "RFIs"}]
        self.assertEqual(list_project_tools(123, company_id=456, client=fake)[0].name, "RFIs")

        fake.get_response = {"id": 2, "name": "Drawings"}
        self.assertEqual(get_project_tool(123, 2, company_id=456, client=fake).name, "Drawings")

        fake.list_response = [{"id": 3, "label": "Submittals"}]
        self.assertEqual(
            find_project_tool(123, "Submittals", company_id=456, client=fake).id,
            3,
        )

    def test_object_client_exposes_project_tools_group(self) -> None:
        """The object client should expose Project Tools under project_tools."""
        with patch("pyprocore.client.list_project_tools") as list_mock:
            list_mock.return_value = [ProjectTool(id=1, name="RFIs")]
            tools = Procore().project_tools.list(123, company_id=456, active=True)

        self.assertEqual(tools[0].name, "RFIs")
        list_mock.assert_called_once_with(
            123,
            company_id=456,
            active=True,
            mobile=None,
            configurable=None,
        )

    def test_cli_project_tools_dispatches_without_traceback(self) -> None:
        """The CLI command should dispatch to the read-only list helper."""
        args = argparse.Namespace(
            command="project-tools",
            project_id=123,
            company_id=456,
            active=True,
            mobile=False,
            configurable=False,
        )
        with patch("pyprocore.app.list_project_tools") as list_mock:
            list_mock.return_value = [ProjectTool(id=1, name="RFIs")]
            result = run_command(args)

        self.assertEqual(result[0].name, "RFIs")
        list_mock.assert_called_once_with(
            123,
            company_id=456,
            active=True,
            mobile=None,
            configurable=None,
        )

    def test_cli_project_tool_dispatches_without_traceback(self) -> None:
        """The CLI command should dispatch to the read-only get helper."""
        args = argparse.Namespace(command="project-tool", project_id=123, company_id=456, tool_id=7)
        with patch("pyprocore.app.get_project_tool") as get_mock:
            get_mock.return_value = ProjectTool(id=7, name="Drawings")
            result = run_command(args)

        self.assertEqual(result.name, "Drawings")
        get_mock.assert_called_once_with(123, 7, company_id=456)

    def test_agent_registry_project_tools_metadata_is_read_only(self) -> None:
        """Agent registry should expose Project Tools as metadata-only read coverage."""
        tool = get_agent_tool("procore.list_project_tools")

        self.assertEqual(tool.operation_path, "pyprocore.services.project_tools.list_project_tools")
        self.assertEqual(tool.safety_level.value, "read_only")
        self.assertEqual(tool.side_effects, [])
