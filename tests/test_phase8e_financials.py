"""Tests for Phase 8E read-only financial and change-management coverage."""

from __future__ import annotations

import csv
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
    BudgetDetailColumn,
    BudgetDetailRow,
    BudgetSummaryRow,
    BudgetView,
    ChangeEvent,
    ChangeEventSettings,
    ChangeEventStatus,
    ChangeEventType,
    ChangeOrderPackage,
    Commitment,
    CommitmentChangeOrder,
    CostCode,
    DirectCost,
    PrimeChangeOrder,
    WbsCode,
)
from pyprocore.services import financials
from pyprocore.services.financials import FinancialsService
from pyprocore.workflows.exports import (
    export_budget_details_to_csv,
    export_budget_summary_rows_to_csv,
    export_budget_views_to_csv,
    export_change_events_to_jsonl,
    export_change_order_packages_to_csv,
    export_commitment_change_orders_to_csv,
    export_commitments_to_csv,
    export_cost_codes_to_csv,
    export_direct_costs_to_csv,
    export_prime_change_orders_to_csv,
    write_budget_details_csv,
    write_change_events_csv,
)


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


class Phase8EEndpointTestCase(unittest.TestCase):
    """Endpoint construction tests for Phase 8E resources."""

    def test_phase8e_endpoint_paths(self) -> None:
        """Endpoint helpers should return read-only financial paths."""
        self.assertEqual(endpoints.change_events(123), "/rest/v1.0/projects/123/change_events")
        self.assertEqual(
            endpoints.change_event(123, 5),
            "/rest/v1.0/projects/123/change_events/5",
        )
        self.assertEqual(
            endpoints.prime_change_orders(123),
            "/rest/v1.0/projects/123/prime_change_orders",
        )
        self.assertEqual(
            endpoints.commitment_change_orders(123),
            "/rest/v1.0/projects/123/commitment_change_orders",
        )
        self.assertEqual(
            endpoints.change_order_packages(123),
            "/rest/v1.0/projects/123/change_order_packages",
        )
        self.assertEqual(endpoints.direct_costs(123), "/rest/v1.0/projects/123/direct_costs")
        self.assertEqual(endpoints.budget_views(123), "/rest/v1.0/projects/123/budget_views")
        self.assertEqual(
            endpoints.budget_details(123, 7),
            "/rest/v1.0/projects/123/budget_views/7/budget_details",
        )
        self.assertEqual(endpoints.cost_codes(456), "/rest/v1.0/companies/456/cost_codes")
        self.assertEqual(endpoints.wbs_codes(123), "/rest/v1.0/projects/123/wbs_codes")
        self.assertEqual(endpoints.commitments(123), "/rest/v1.0/projects/123/commitments")


class Phase8EServiceTestCase(unittest.TestCase):
    """Service tests with mocked HTTP client behavior."""

    def test_list_and_get_change_events(self) -> None:
        """Change events should use project paths and company headers."""
        fake = FakeClient()
        fake.list_response = {"change_events": [{"id": 1, "number": "CE-1", "title": "Scope"}]}
        service = FinancialsService(client=fake)

        events = service.list_change_events(456, 123, status="open")

        self.assertIsInstance(events[0], ChangeEvent)
        self.assertEqual(fake.calls[0][1], "/rest/v1.0/projects/123/change_events")
        self.assertEqual(fake.calls[0][2], {"status": "open"})
        self.assertEqual(fake.calls[0][3], {"Procore-Company-Id": "456"})

        fake.get_response = {"id": 1, "number": "CE-1"}
        event = service.get_change_event(456, 123, 1)
        self.assertEqual(event.number, "CE-1")
        self.assertEqual(fake.calls[-1][1], "/rest/v1.0/projects/123/change_events/1")

    def test_financial_list_helpers_return_typed_models(self) -> None:
        """Phase 8E list helpers should parse typed models."""
        fake = FakeClient()
        service = FinancialsService(client=fake)

        cases: list[tuple[str, str, type[object], object]] = [
            ("list_change_event_statuses", "change_event_statuses", ChangeEventStatus, None),
            ("list_change_event_types", "change_event_types", ChangeEventType, None),
            ("list_prime_change_orders", "prime_change_orders", PrimeChangeOrder, None),
            (
                "list_commitment_change_orders",
                "commitment_change_orders",
                CommitmentChangeOrder,
                None,
            ),
            ("list_change_order_packages", "change_order_packages", ChangeOrderPackage, None),
            ("list_direct_costs", "direct_costs", DirectCost, None),
            ("list_budget_views", "budget_views", BudgetView, None),
            ("list_wbs_codes", "wbs_codes", WbsCode, None),
            ("list_commitments", "commitments", Commitment, None),
        ]
        for method_name, response_key, model_type, _unused in cases:
            fake.list_response = {response_key: [{"id": 1, "name": "Item"}]}
            result = getattr(service, method_name)(456, 123)
            self.assertIsInstance(result[0], model_type)

        fake.list_response = {"budget_detail_columns": [{"id": 2, "name": "Column"}]}
        self.assertIsInstance(
            service.list_budget_detail_columns(456, 123, 7)[0], BudgetDetailColumn
        )

        fake.list_response = {"budget_details": [{"id": 3, "name": "Row"}]}
        self.assertIsInstance(service.list_budget_details(456, 123, 7)[0], BudgetDetailRow)

        fake.list_response = {"summary_rows": [{"id": 4, "name": "Summary"}]}
        self.assertIsInstance(
            service.list_budget_view_summary_rows(456, 123, 7)[0], BudgetSummaryRow
        )

        fake.list_response = {"cost_codes": [{"id": 5, "code": "01"}]}
        self.assertIsInstance(service.list_cost_codes(456)[0], CostCode)
        self.assertEqual(fake.calls[-1][1], "/rest/v1.0/companies/456/cost_codes")

    def test_settings_and_module_wrappers(self) -> None:
        """Settings and module wrappers should preserve typed responses."""
        fake = FakeClient()
        fake.get_response = {"id": 1, "project_id": 123, "enabled": True}
        settings = financials.get_change_event_settings(456, 123, client=fake)
        self.assertIsInstance(settings, ChangeEventSettings)

        fake.list_response = [{"id": 9, "number": "C-1"}]
        commitment = financials.list_commitments(456, 123, client=fake)[0]
        self.assertIsInstance(commitment, Commitment)

    def test_get_helpers_and_standard_cost_codes(self) -> None:
        """Remaining get helpers should use typed read-only responses."""
        fake = FakeClient()
        service = FinancialsService(client=fake)

        get_cases = [
            (service.get_prime_change_order, PrimeChangeOrder, (456, 123, 1)),
            (service.get_commitment_change_order, CommitmentChangeOrder, (456, 123, 2)),
            (service.get_change_order_package, ChangeOrderPackage, (456, 123, 3)),
            (service.get_direct_cost, DirectCost, (456, 123, 4)),
            (service.get_budget_view, BudgetView, (456, 123, 5)),
            (service.get_commitment, Commitment, (456, 123, 6)),
        ]
        for method, model_type, args in get_cases:
            fake.get_response = {"id": args[-1], "number": "1", "name": "Item"}
            self.assertIsInstance(method(*args), model_type)

        fake.list_response = {"cost_codes": [{"id": 7, "code": "01"}]}
        self.assertIsInstance(service.list_standard_cost_codes(456, 8)[0], CostCode)
        self.assertEqual(
            fake.calls[-1][1],
            "/rest/v1.0/companies/456/standard_cost_code_lists/8/cost_codes",
        )


class Phase8ESearchExportClientTestCase(unittest.TestCase):
    """Search, export, object-client, and agent metadata tests."""

    def test_search_helpers_resolve_matches(self) -> None:
        """Search helpers should resolve typed models from mocked lists."""
        with patch(
            "pyprocore.services.search.list_change_events",
            return_value=[ChangeEvent(id=1, number="CE-1", title="Scope")],
        ):
            from pyprocore.services.search import find_change_event

            self.assertEqual(find_change_event(123, number="CE-1").id, 1)

        with patch(
            "pyprocore.services.search.list_prime_change_orders",
            return_value=[PrimeChangeOrder(id=2, number="PCO-1")],
        ):
            from pyprocore.services.search import find_prime_change_order

            self.assertEqual(find_prime_change_order(123, number="PCO-1").id, 2)

    def test_exports_write_csv_and_jsonl(self) -> None:
        """Export helpers should write local files without live API calls."""
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "change-events.csv"
            jsonl_path = Path(temp_dir) / "change-events.jsonl"
            write_change_events_csv([ChangeEvent(id=1, number="CE-1")], csv_path)
            with csv_path.open() as file_handle:
                export_rows = list(csv.DictReader(file_handle))
            self.assertEqual(export_rows[0]["number"], "CE-1")

            with patch(
                "pyprocore.workflows.exports.list_change_events",
                return_value=[ChangeEvent(id=2, number="CE-2")],
            ):
                export_change_events_to_jsonl(456, 123, jsonl_path)
            self.assertIn("CE-2", jsonl_path.read_text())

            budget_path = Path(temp_dir) / "budget.csv"
            write_budget_details_csv([BudgetDetailRow(id=3, name="Row")], budget_path)
            self.assertIn("Row", budget_path.read_text())

            with patch(
                "pyprocore.workflows.exports.list_budget_details",
                return_value=[BudgetDetailRow(id=4, name="Budget")],
            ):
                export_budget_details_to_csv(456, 123, 7, Path(temp_dir) / "budget-export.csv")

            export_cases = [
                (
                    "pyprocore.workflows.exports.list_prime_change_orders",
                    [PrimeChangeOrder(id=5)],
                    export_prime_change_orders_to_csv,
                    (456, 123, Path(temp_dir) / "pco.csv"),
                ),
                (
                    "pyprocore.workflows.exports.list_commitment_change_orders",
                    [CommitmentChangeOrder(id=6)],
                    export_commitment_change_orders_to_csv,
                    (456, 123, Path(temp_dir) / "cco.csv"),
                ),
                (
                    "pyprocore.workflows.exports.list_change_order_packages",
                    [ChangeOrderPackage(id=7)],
                    export_change_order_packages_to_csv,
                    (456, 123, Path(temp_dir) / "cop.csv"),
                ),
                (
                    "pyprocore.workflows.exports.list_direct_costs",
                    [DirectCost(id=8)],
                    export_direct_costs_to_csv,
                    (456, 123, Path(temp_dir) / "direct.csv"),
                ),
                (
                    "pyprocore.workflows.exports.list_budget_views",
                    [BudgetView(id=9)],
                    export_budget_views_to_csv,
                    (456, 123, Path(temp_dir) / "views.csv"),
                ),
                (
                    "pyprocore.workflows.exports.list_budget_view_summary_rows",
                    [BudgetSummaryRow(id=10)],
                    export_budget_summary_rows_to_csv,
                    (456, 123, 7, Path(temp_dir) / "summary.csv"),
                ),
                (
                    "pyprocore.workflows.exports.list_cost_codes",
                    [CostCode(id=11)],
                    export_cost_codes_to_csv,
                    (456, Path(temp_dir) / "codes.csv"),
                ),
                (
                    "pyprocore.workflows.exports.list_commitments",
                    [Commitment(id=12)],
                    export_commitments_to_csv,
                    (456, 123, Path(temp_dir) / "commitments.csv"),
                ),
            ]
            for patch_path, return_value, export_func, args in export_cases:
                with patch(patch_path, return_value=return_value):
                    self.assertTrue(export_func(*args).exists())

    def test_object_client_groups_delegate(self) -> None:
        """Object client groups should delegate to Phase 8E services."""
        client = Procore()
        with patch("pyprocore.client.list_change_events", return_value=[ChangeEvent(id=1)]):
            self.assertEqual(client.change_events.list(123, company_id=456)[0].id, 1)
        with patch("pyprocore.client.get_change_event", return_value=ChangeEvent(id=1)):
            self.assertEqual(client.change_events.get(123, 1, company_id=456).id, 1)
        with patch(
            "pyprocore.client.list_change_event_statuses", return_value=[ChangeEventStatus(id=1)]
        ):
            self.assertEqual(client.change_events.statuses(123, company_id=456)[0].id, 1)
        with patch(
            "pyprocore.client.list_change_event_types", return_value=[ChangeEventType(id=1)]
        ):
            self.assertEqual(client.change_events.types(123, company_id=456)[0].id, 1)
        with patch(
            "pyprocore.client.get_change_event_settings",
            return_value=ChangeEventSettings(id=1),
        ):
            self.assertEqual(client.change_events.settings(123, company_id=456).id, 1)
        with patch(
            "pyprocore.client.list_prime_change_orders",
            return_value=[PrimeChangeOrder(id=4)],
        ):
            self.assertEqual(client.prime_change_orders.list(123, company_id=456)[0].id, 4)
        with patch("pyprocore.client.list_budget_views", return_value=[BudgetView(id=2)]):
            self.assertEqual(client.budget.views(123, company_id=456)[0].id, 2)
        with patch("pyprocore.client.list_budget_details", return_value=[BudgetDetailRow(id=5)]):
            self.assertEqual(client.budget.details(123, 7, company_id=456)[0].id, 5)
        with patch("pyprocore.client.list_cost_codes", return_value=[CostCode(id=6)]):
            self.assertEqual(client.cost_codes.list(456)[0].id, 6)
        with patch("pyprocore.client.list_wbs_codes", return_value=[WbsCode(id=7)]):
            self.assertEqual(client.cost_codes.wbs(123, company_id=456)[0].id, 7)
        with patch("pyprocore.client.list_commitments", return_value=[Commitment(id=3)]):
            self.assertEqual(client.commitments.list(123, company_id=456)[0].id, 3)

    def test_cli_parser_and_routes(self) -> None:
        """CLI parser should include Phase 8E commands and route them."""
        parser = build_parser()
        args = parser.parse_args(["change-events", "--project", "123", "--company-id", "456"])
        with patch("pyprocore.app.list_change_events", return_value=[ChangeEvent(id=1)]):
            self.assertEqual(run_command(args)[0].id, 1)

        export_args = parser.parse_args(
            [
                "export-budget-details",
                "--project",
                "123",
                "--company-id",
                "456",
                "--budget-view",
                "7",
                "--output",
                "out.csv",
            ]
        )
        with patch(
            "pyprocore.app.export_budget_details_to_csv",
            return_value=Path("out.csv"),
        ):
            self.assertEqual(run_command(export_args), Path("out.csv"))

    def test_cli_routes_for_phase8e_commands(self) -> None:
        """CLI dispatcher should route remaining Phase 8E commands."""
        parser = build_parser()
        route_cases = [
            (
                "change-event-statuses --project 123 --company-id 456",
                "list_change_event_statuses",
                [ChangeEventStatus(id=1)],
            ),
            (
                "change-event-types --project 123 --company-id 456",
                "list_change_event_types",
                [ChangeEventType(id=1)],
            ),
            (
                "change-event-settings --project 123 --company-id 456",
                "get_change_event_settings",
                ChangeEventSettings(id=1),
            ),
            (
                "prime-change-orders --project 123 --company-id 456",
                "list_prime_change_orders",
                [PrimeChangeOrder(id=1)],
            ),
            (
                "commitment-change-orders --project 123 --company-id 456",
                "list_commitment_change_orders",
                [CommitmentChangeOrder(id=1)],
            ),
            (
                "change-order-packages --project 123 --company-id 456",
                "list_change_order_packages",
                [ChangeOrderPackage(id=1)],
            ),
            (
                "direct-costs --project 123 --company-id 456",
                "list_direct_costs",
                [DirectCost(id=1)],
            ),
            (
                "budget-views --project 123 --company-id 456",
                "list_budget_views",
                [BudgetView(id=1)],
            ),
            (
                "budget-detail-columns --project 123 --company-id 456 --budget-view 7",
                "list_budget_detail_columns",
                [BudgetDetailColumn(id=1)],
            ),
            (
                "budget-details --project 123 --company-id 456 --budget-view 7",
                "list_budget_details",
                [BudgetDetailRow(id=1)],
            ),
            (
                "budget-summary-rows --project 123 --company-id 456 --budget-view 7",
                "list_budget_view_summary_rows",
                [BudgetSummaryRow(id=1)],
            ),
            ("cost-codes --company-id 456", "list_cost_codes", [CostCode(id=1)]),
            ("wbs-codes --project 123 --company-id 456", "list_wbs_codes", [WbsCode(id=1)]),
            ("commitments --project 123 --company-id 456", "list_commitments", [Commitment(id=1)]),
        ]
        for command, function_name, return_value in route_cases:
            with patch(f"pyprocore.app.{function_name}", return_value=return_value):
                result = run_command(parser.parse_args(command.split()))
                self.assertIsNotNone(result)

    def test_agent_registry_and_mcp_include_phase8e_tools(self) -> None:
        """Agent and MCP discovery should include Phase 8E metadata only."""
        tool_names = {tool.name for tool in list_agent_tools()}
        self.assertIn("procore.list_change_events", tool_names)
        self.assertIn("procore.list_budget_details", tool_names)
        self.assertIn("procore.list_commitments", tool_names)

        mcp_json = export_mcp_tools_json()
        self.assertIn("procore.list_direct_costs", mcp_json)
        self.assertIn("procore.list_cost_codes", mcp_json)

    def test_financial_modules_remain_read_only(self) -> None:
        """Financial service should not expose write, approval, or mutation verbs."""
        forbidden = (
            "create",
            "update",
            "delete",
            "approve",
            "reject",
            "void",
            "modify",
            "invoice",
            "payment",
        )
        public_functions = [
            name
            for name, value in inspect.getmembers(financials)
            if inspect.isfunction(value) and not name.startswith("_")
        ]
        for name in public_functions:
            self.assertFalse(any(word in name for word in forbidden), name)

        parser_help = build_parser().format_help()
        self.assertNotIn("create-change", parser_help)
        self.assertNotIn("approve", parser_help)


if __name__ == "__main__":
    unittest.main()
