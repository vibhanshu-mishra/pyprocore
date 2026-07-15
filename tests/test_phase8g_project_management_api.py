"""Tests for Phase 8G read-only project-management extras coverage."""

from __future__ import annotations

import inspect
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pyprocore.agent import export_mcp_tools_json, list_agent_tools
from pyprocore.app import build_parser, run_command
from pyprocore.client import Procore
from pyprocore.core import endpoints
from pyprocore.models import (
    ActionPlan,
    ActionPlanChangeHistoryEvent,
    CalendarItem,
    CoordinationIssue,
    CoordinationIssueActivity,
    CoordinationIssueChangeHistoryEvent,
    CoordinationIssueFilterOption,
    Form,
    FormTemplate,
    ProjectSchedule,
    ScheduleImportStatus,
    ScheduleIntegration,
    ScheduleResourceAssignment,
    ScheduleSettings,
    ScheduleType,
    Task,
    TaskRequestedChange,
)
from pyprocore.services import project_management
from pyprocore.services.project_management import ProjectManagementService
from pyprocore.services.search import (
    find_action_plan,
    find_calendar_item,
    find_coordination_issue,
    find_form,
    find_task,
)
from pyprocore.workflows import exports as exports_module


class FakeClient:
    """Small fake Procore client that records calls without HTTP."""

    def __init__(self) -> None:
        """Initialize fake responses and call log."""
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


class Phase8GEndpointTestCase(unittest.TestCase):
    """Endpoint construction tests for Phase 8G resources."""

    def test_phase8g_endpoint_paths(self) -> None:
        """Endpoint helpers should return read-only project-management paths."""
        self.assertEqual(endpoints.project_schedule(123), "/rest/v1.0/projects/123/schedule")
        self.assertEqual(
            endpoints.schedule_resource_assignments(123),
            "/rest/v1.0/projects/123/schedule_resource_assignments",
        )
        self.assertEqual(endpoints.tasks(123), "/rest/v1.0/projects/123/tasks")
        self.assertEqual(
            endpoints.task_requested_changes(123, 7),
            "/rest/v1.0/projects/123/tasks/7/requested_changes",
        )
        self.assertEqual(
            endpoints.calendar_items(123),
            "/rest/v1.0/projects/123/calendar_items",
        )
        self.assertEqual(
            endpoints.coordination_issue_change_history(123, 8),
            "/rest/v1.0/projects/123/coordination_issues/8/change_history",
        )
        self.assertEqual(endpoints.forms(123), "/rest/v1.0/projects/123/forms")
        self.assertEqual(
            endpoints.action_plan_change_history_events(123, 9),
            "/rest/v1.0/projects/123/action_plans/9/change_history_events",
        )


class Phase8GServiceTestCase(unittest.TestCase):
    """Service tests with mocked HTTP client behavior."""

    def test_schedule_get_helpers_use_company_headers(self) -> None:
        """Schedule metadata helpers should parse typed models."""
        fake = FakeClient()
        fake.get_response = {"id": 1, "name": "Schedule"}
        service = ProjectManagementService(client=fake)

        cases = [
            (service.get_project_schedule, ProjectSchedule, "/rest/v1.0/projects/123/schedule"),
            (
                service.get_schedule_settings,
                ScheduleSettings,
                "/rest/v1.0/projects/123/schedule_settings",
            ),
            (service.get_schedule_type, ScheduleType, "/rest/v1.0/projects/123/schedule_type"),
            (
                service.get_schedule_integration,
                ScheduleIntegration,
                "/rest/v1.0/projects/123/schedule_integration",
            ),
            (
                service.get_schedule_import_status,
                ScheduleImportStatus,
                "/rest/v1.0/projects/123/schedule_imports/status",
            ),
        ]
        for method, model_type, path in cases:
            result = method(456, 123)
            self.assertIsInstance(result, model_type)
            self.assertEqual(fake.calls[-1][1], path)
            self.assertEqual(fake.calls[-1][3], {"Procore-Company-Id": "456"})

    def test_list_helpers_return_typed_models_and_query_params(self) -> None:
        """List helpers should parse common Procore collection shapes."""
        fake = FakeClient()
        service = ProjectManagementService(client=fake)
        cases: list[tuple[str, str, type[object], tuple[int, ...]]] = [
            (
                "list_schedule_resource_assignments",
                "schedule_resource_assignments",
                ScheduleResourceAssignment,
                (456, 123),
            ),
            ("list_tasks", "tasks", Task, (456, 123)),
            (
                "list_task_requested_changes",
                "requested_changes",
                TaskRequestedChange,
                (456, 123, 7),
            ),
            ("list_calendar_items", "calendar_items", CalendarItem, (456, 123)),
            ("list_coordination_issues", "coordination_issues", CoordinationIssue, (456, 123)),
            (
                "list_coordination_issue_change_history",
                "change_history",
                CoordinationIssueChangeHistoryEvent,
                (456, 123, 8),
            ),
            (
                "list_coordination_issue_activity_feed",
                "activity_feed",
                CoordinationIssueActivity,
                (456, 123, 8),
            ),
            (
                "list_coordination_issue_filter_options",
                "filter_options",
                CoordinationIssueFilterOption,
                (456, 123),
            ),
            ("list_forms", "forms", Form, (456, 123)),
            ("list_form_templates", "form_templates", FormTemplate, (456, 123)),
            ("list_action_plans", "action_plans", ActionPlan, (456, 123)),
            (
                "list_action_plan_change_history_events",
                "events",
                ActionPlanChangeHistoryEvent,
                (456, 123, 9),
            ),
        ]
        for method_name, response_key, model_type, args in cases:
            fake.list_response = {response_key: [{"id": 1, "number": "1", "name": "Item"}]}
            result = getattr(service, method_name)(*args, status="open")
            self.assertIsInstance(result[0], model_type)
            self.assertEqual(fake.calls[-1][2], {"status": "open"})

        fake.list_response = {"filter_options": [{"id": 2, "name": "Assignee"}]}
        service.list_coordination_issue_filter_options(456, 123, option_type="assignee")
        self.assertEqual(fake.calls[-1][2], {"option_type": "assignee"})

    def test_get_and_module_wrappers_return_typed_models(self) -> None:
        """Get helpers and module-level wrappers should stay typed."""
        fake = FakeClient()
        fake.get_response = {"id": 1, "number": "1", "name": "Item"}

        get_cases = [
            (
                project_management.get_schedule_resource_assignment,
                (456, 123, 1),
                ScheduleResourceAssignment,
            ),
            (project_management.get_task, (456, 123, 1), Task),
            (project_management.get_calendar_item, (456, 123, 1), CalendarItem),
            (project_management.get_coordination_issue, (456, 123, 1), CoordinationIssue),
            (project_management.get_form, (456, 123, 1), Form),
            (project_management.get_action_plan, (456, 123, 1), ActionPlan),
        ]
        for function, args, model_type in get_cases:
            self.assertIsInstance(function(*args, client=fake), model_type)

        fake.list_response = [{"id": 2, "name": "Item"}]
        self.assertIsInstance(project_management.list_tasks(456, 123, client=fake)[0], Task)
        self.assertIsInstance(
            project_management.list_action_plans(456, 123, client=fake)[0],
            ActionPlan,
        )


class Phase8GSearchExportClientCliTestCase(unittest.TestCase):
    """Tests for search helpers, exports, object client groups, and CLI routes."""

    def test_search_helpers_delegate_to_list_functions(self) -> None:
        """Search helpers should resolve typed Phase 8G models."""
        cases = [
            ("pyprocore.services.search.list_tasks", find_task, Task(id=1, title="Pre task")),
            (
                "pyprocore.services.search.list_calendar_items",
                find_calendar_item,
                CalendarItem(id=2, title="Pre pour"),
            ),
            (
                "pyprocore.services.search.list_coordination_issues",
                find_coordination_issue,
                CoordinationIssue(id=3, title="Pre coordination"),
            ),
            ("pyprocore.services.search.list_forms", find_form, Form(id=4, name="Pre checklist")),
            (
                "pyprocore.services.search.list_action_plans",
                find_action_plan,
                ActionPlan(id=5, title="Pre-pour"),
            ),
        ]
        for patch_path, function, item in cases:
            with patch(patch_path, return_value=[item]):
                self.assertEqual(function(123, query="pre", company_id=456).id, item.id)

    def test_exports_write_csv_and_jsonl(self) -> None:
        """Phase 8G exports should write local files without live HTTP."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "tasks.csv"
            jsonl_path = Path(tmpdir) / "tasks.jsonl"
            with patch("pyprocore.workflows.exports.list_tasks", return_value=[Task(id=1)]):
                self.assertEqual(exports_module.export_tasks_to_csv(456, 123, csv_path), csv_path)
                self.assertEqual(
                    exports_module.export_tasks_to_jsonl(456, 123, jsonl_path),
                    jsonl_path,
                )
            self.assertIn("id", csv_path.read_text(encoding="utf-8"))
            self.assertIn('"id": 1', jsonl_path.read_text(encoding="utf-8"))

            write_cases = [
                (
                    exports_module.write_schedule_resource_assignments_csv,
                    [ScheduleResourceAssignment(id=1)],
                ),
                (exports_module.write_task_requested_changes_csv, [TaskRequestedChange(id=2)]),
                (exports_module.write_calendar_items_csv, [CalendarItem(id=3)]),
                (exports_module.write_coordination_issues_csv, [CoordinationIssue(id=4)]),
                (
                    exports_module.write_coordination_issue_change_history_csv,
                    [CoordinationIssueChangeHistoryEvent(id=5)],
                ),
                (
                    exports_module.write_coordination_issue_activity_feed_csv,
                    [CoordinationIssueActivity(id=6)],
                ),
                (
                    exports_module.write_coordination_issue_filter_options_csv,
                    [CoordinationIssueFilterOption(id=7)],
                ),
                (exports_module.write_forms_csv, [Form(id=8)]),
                (exports_module.write_form_templates_csv, [FormTemplate(id=9)]),
                (exports_module.write_action_plans_csv, [ActionPlan(id=10)]),
                (
                    exports_module.write_action_plan_change_history_csv,
                    [ActionPlanChangeHistoryEvent(id=11)],
                ),
            ]
            for index, (function, items) in enumerate(write_cases):
                self.assertTrue(function(items, Path(tmpdir) / f"phase8g-{index}.csv").exists())

    def test_object_client_groups_delegate_to_services(self) -> None:
        """Object client groups should expose Phase 8G resources."""
        client = Procore()
        with patch("pyprocore.client.get_project_schedule", return_value=ProjectSchedule(id=1)):
            self.assertEqual(client.schedule.get(123, company_id=456).id, 1)
        with patch("pyprocore.client.list_tasks", return_value=[Task(id=2)]):
            self.assertEqual(client.tasks.list(123, company_id=456)[0].id, 2)
        with patch("pyprocore.client.find_task", return_value=Task(id=3)):
            self.assertEqual(client.tasks.find(123, company_id=456, number="3").id, 3)
        with patch("pyprocore.client.list_calendar_items", return_value=[CalendarItem(id=4)]):
            self.assertEqual(client.calendar_items.list(123, company_id=456)[0].id, 4)
        with patch(
            "pyprocore.client.list_coordination_issues", return_value=[CoordinationIssue(id=5)]
        ):
            self.assertEqual(client.coordination_issues.list(123, company_id=456)[0].id, 5)
        with patch("pyprocore.client.list_forms", return_value=[Form(id=6)]):
            self.assertEqual(client.forms.list(123, company_id=456)[0].id, 6)
        with patch("pyprocore.client.list_action_plans", return_value=[ActionPlan(id=7)]):
            self.assertEqual(client.action_plans.list(123, company_id=456)[0].id, 7)

    def test_cli_routes_phase8g_commands(self) -> None:
        """CLI parser should include and route representative Phase 8G commands."""
        parser = build_parser()
        command_cases = [
            (
                "project-schedule --project 123 --company-id 456",
                "get_project_schedule",
                ProjectSchedule(id=1),
            ),
            ("tasks --project 123 --company-id 456", "list_tasks", [Task(id=1)]),
            ("task --project 123 --company-id 456 --id 7", "get_task", Task(id=7)),
            ("find-task --project 123 --company-id 456 --number 15", "find_task", Task(id=15)),
            (
                "coordination-issue-filter-options --project 123 --company-id 456 "
                "--option-type assignee",
                "list_coordination_issue_filter_options",
                [CoordinationIssueFilterOption(id=1)],
            ),
            (
                "action-plan-change-history --project 123 --company-id 456 --action-plan 9",
                "list_action_plan_change_history_events",
                [ActionPlanChangeHistoryEvent(id=1)],
            ),
        ]
        for command, function_name, return_value in command_cases:
            with patch(f"pyprocore.app.{function_name}", return_value=return_value):
                result = run_command(parser.parse_args(command.split()))
            self.assertEqual(result, return_value)

    def test_cli_routes_phase8g_exports(self) -> None:
        """CLI export commands should route to Phase 8G CSV helpers."""
        parser = build_parser()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "out.csv"
            export_cases = [
                ("export-tasks --project 123 --company-id 456", "export_tasks_to_csv"),
                (
                    "export-task-requested-changes --project 123 --company-id 456 --task 7",
                    "export_task_requested_changes_to_csv",
                ),
                (
                    "export-coordination-issue-change-history --project 123 --company-id 456 "
                    "--coordination-issue 8",
                    "export_coordination_issue_change_history_to_csv",
                ),
                (
                    "export-action-plan-change-history --project 123 --company-id 456 "
                    "--action-plan 9",
                    "export_action_plan_change_history_to_csv",
                ),
            ]
            for command, function_name in export_cases:
                with patch(f"pyprocore.app.{function_name}", return_value=output_path):
                    result = run_command(
                        parser.parse_args(f"{command} --output {output_path}".split())
                    )
                self.assertEqual(result, output_path)


class Phase8GAgentSafetyTestCase(unittest.TestCase):
    """Agent registry and read-only safety checks."""

    def test_agent_and_mcp_discovery_include_phase8g_tools(self) -> None:
        """Agent and MCP discovery should include Phase 8G metadata only."""
        tool_names = {tool.name for tool in list_agent_tools()}
        expected = {
            "procore.get_project_schedule",
            "procore.list_tasks",
            "procore.find_task",
            "procore.list_coordination_issues",
            "procore.list_forms",
            "procore.list_action_plans",
        }
        self.assertTrue(expected.issubset(tool_names))
        mcp_json = export_mcp_tools_json()
        self.assertIn("procore.list_tasks", mcp_json)
        self.assertIn("procore.list_action_plans", mcp_json)

    def test_phase8g_service_and_cli_are_read_only(self) -> None:
        """Phase 8G should not expose project-management mutation helpers."""
        forbidden_fragments = (
            "create_",
            "update_",
            "delete_",
            "submit_",
            "approve_",
            "complete_",
            "closeout_",
            "upload_",
            "assign_",
        )
        names = [
            name
            for name, value in inspect.getmembers(project_management)
            if inspect.isfunction(value) or inspect.isclass(value)
        ]
        for name in names:
            self.assertFalse(
                any(fragment in name for fragment in forbidden_fragments),
                msg=f"Unexpected mutation-looking helper found: {name}",
            )
        help_text = build_parser().format_help()
        for command in (
            "create-task",
            "update-task",
            "delete-task",
            "submit-form",
            "complete-action-plan",
            "upload-schedule",
        ):
            self.assertNotIn(command, help_text)


if __name__ == "__main__":
    unittest.main()
