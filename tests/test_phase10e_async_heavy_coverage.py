"""Tests for Phase 10E async financial, contract, and project-management coverage."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Any

import pyprocore
from pyprocore import AsyncProcore, MockAsyncTransport
from pyprocore.core.async_transport import AsyncResponse
from pyprocore.core.config import ProcoreSettings
from pyprocore.models import (
    ActionPlan,
    ActionPlanChangeHistoryEvent,
    BillingPeriod,
    BudgetDetailColumn,
    BudgetDetailRow,
    BudgetSummaryRow,
    BudgetView,
    CalendarItem,
    ChangeEvent,
    ChangeEventSettings,
    ChangeEventStatus,
    ChangeEventType,
    ChangeOrderPackage,
    Commitment,
    CommitmentChangeOrder,
    ContractPayment,
    CoordinationIssue,
    CoordinationIssueActivity,
    CoordinationIssueChangeHistoryEvent,
    CoordinationIssueFilterOption,
    CostCode,
    CostType,
    DirectCost,
    Form,
    FormTemplate,
    OwnerInvoice,
    PrimeChangeOrder,
    PrimeContract,
    ProjectSchedule,
    ScheduleImportStatus,
    ScheduleIntegration,
    ScheduleResourceAssignment,
    ScheduleSettings,
    ScheduleType,
    SubcontractorInvoice,
    Task,
    TaskRequestedChange,
    TaxCode,
    WbsCode,
)
from pyprocore.workflows import SUPPORTED_ASYNC_BATCH_RESOURCES
from pyprocore.workflows.async_batch import async_collect_project_resources
from pyprocore.workflows.async_exports import (
    async_export_change_events,
    async_export_contracts,
    async_export_project_schedule,
    async_export_tasks,
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


class Phase10EAsyncHeavyCoverageTests(unittest.IsolatedAsyncioTestCase):
    """Validate Phase 10E async resources with mock transports only."""

    async def test_async_financial_resources_list_get_find(self) -> None:
        """Financial async methods should use read-only endpoints and typed models."""
        client, transport = async_client(
            [
                json_response({"change_events": [{"id": 10, "number": "CE-1", "title": "Door"}]}),
                json_response({"id": 10, "number": "CE-1"}),
                json_response([{"id": 10, "number": "CE-1"}]),
                json_response({"statuses": [{"id": 11, "name": "Open"}]}),
                json_response({"types": [{"id": 12, "name": "Scope"}]}),
                json_response({"id": 13, "project_id": 456, "enabled": True}),
                json_response({"prime_change_orders": [{"id": 14, "number": "PCO-1"}]}),
                json_response({"id": 14, "number": "PCO-1"}),
                json_response({"commitment_change_orders": [{"id": 15, "number": "CCO-1"}]}),
                json_response({"id": 15, "number": "CCO-1"}),
                json_response({"change_order_packages": [{"id": 16, "number": "COP-1"}]}),
                json_response({"id": 16, "number": "COP-1"}),
                json_response({"direct_costs": [{"id": 17, "number": "DC-1"}]}),
                json_response({"id": 17, "number": "DC-1"}),
                json_response({"budget_views": [{"id": 18, "name": "Forecast"}]}),
                json_response({"columns": [{"id": 19, "name": "Budget"}]}),
                json_response({"rows": [{"id": 20, "name": "Concrete"}]}),
                json_response({"summary_rows": [{"id": 21, "name": "Summary"}]}),
                json_response({"cost_codes": [{"id": 22, "code": "03"}]}),
                json_response({"cost_codes": [{"id": 23, "code": "01"}]}),
                json_response({"wbs_codes": [{"id": 24, "code": "WBS"}]}),
                json_response({"commitments": [{"id": 25, "number": "C-1"}]}),
                json_response({"id": 25, "number": "C-1"}),
            ]
        )

        change_events = await client.list_change_events(123, 456)
        change_event = await client.get_change_event(123, 456, 10)
        found_change_event = await client.find_change_event(123, 456, number="CE-1")
        statuses = await client.list_change_event_statuses(123, 456)
        event_types = await client.list_change_event_types(123, 456)
        settings_model = await client.get_change_event_settings(123, 456)
        prime_cos = await client.list_prime_change_orders(123, 456)
        prime_co = await client.get_prime_change_order(123, 456, 14)
        commitment_cos = await client.list_commitment_change_orders(123, 456)
        commitment_co = await client.get_commitment_change_order(123, 456, 15)
        packages = await client.list_change_order_packages(123, 456)
        package = await client.get_change_order_package(123, 456, 16)
        direct_costs = await client.list_direct_costs(123, 456)
        direct_cost = await client.get_direct_cost(123, 456, 17)
        budget_views = await client.list_budget_views(123, 456)
        columns = await client.list_budget_view_columns(123, 456, 18)
        details = await client.list_budget_details(123, 456, 18)
        summary_rows = await client.list_budget_summary_rows(123, 456, 18)
        cost_codes = await client.list_cost_codes(123)
        standard_codes = await client.list_standard_cost_codes(123, 2)
        wbs_items = await client.list_wbs_items(123, 456)
        commitments = await client.list_commitments(123, 456)
        commitment = await client.get_commitment(123, 456, 25)

        self.assertIsInstance(change_events[0], ChangeEvent)
        self.assertIsInstance(change_event, ChangeEvent)
        self.assertEqual(found_change_event.id, 10)
        self.assertIsInstance(statuses[0], ChangeEventStatus)
        self.assertIsInstance(event_types[0], ChangeEventType)
        self.assertIsInstance(settings_model, ChangeEventSettings)
        self.assertIsInstance(prime_cos[0], PrimeChangeOrder)
        self.assertIsInstance(prime_co, PrimeChangeOrder)
        self.assertIsInstance(commitment_cos[0], CommitmentChangeOrder)
        self.assertIsInstance(commitment_co, CommitmentChangeOrder)
        self.assertIsInstance(packages[0], ChangeOrderPackage)
        self.assertIsInstance(package, ChangeOrderPackage)
        self.assertIsInstance(direct_costs[0], DirectCost)
        self.assertIsInstance(direct_cost, DirectCost)
        self.assertIsInstance(budget_views[0], BudgetView)
        self.assertIsInstance(columns[0], BudgetDetailColumn)
        self.assertIsInstance(details[0], BudgetDetailRow)
        self.assertIsInstance(summary_rows[0], BudgetSummaryRow)
        self.assertIsInstance(cost_codes[0], CostCode)
        self.assertIsInstance(standard_codes[0], CostCode)
        self.assertIsInstance(wbs_items[0], WbsCode)
        self.assertIsInstance(commitments[0], Commitment)
        self.assertIsInstance(commitment, Commitment)
        self.assertEqual(
            transport.requests[0].url,
            "https://api.example.com/rest/v1.0/projects/456/change_events",
        )
        self.assertEqual(transport.requests[0].headers["Procore-Company-Id"], "123")

    async def test_async_contract_and_billing_resources(self) -> None:
        """Contract and billing async methods should remain read-only and typed."""
        client, _ = async_client(
            [
                json_response({"prime_contracts": [{"id": 31, "number": "PC-1"}]}),
                json_response({"id": 31, "number": "PC-1"}),
                json_response([{"id": 31, "number": "PC-1"}]),
                json_response({"owner_invoices": [{"id": 32, "number": "OI-1"}]}),
                json_response({"id": 32, "number": "OI-1"}),
                json_response({"requisitions": [{"id": 33, "number": "REQ-1"}]}),
                json_response({"id": 33, "number": "REQ-1"}),
                json_response({"payments": [{"id": 34, "number": "PAY-1"}]}),
                json_response({"billing_periods": [{"id": 35, "name": "July"}]}),
                json_response({"cost_types": [{"id": 36, "code": "L"}]}),
                json_response({"tax_codes": [{"id": 37, "code": "TX"}]}),
            ]
        )

        contracts = await client.list_contracts(123, 456)
        contract = await client.get_contract(123, 456, 31)
        found_contract = await client.find_contract(123, 456, number="PC-1")
        owner_invoices = await client.list_owner_invoices(123, 456, 31)
        owner_invoice = await client.get_owner_invoice(123, 456, 31, 32)
        subcontractor_invoices = await client.list_subcontractor_invoices(123, 456)
        subcontractor_invoice = await client.get_subcontractor_invoice(123, 456, 33)
        payments = await client.list_contract_payments(123, 456)
        billing_periods = await client.list_billing_periods(123, 456)
        cost_types = await client.list_cost_types(123)
        tax_codes = await client.list_tax_codes(123)

        self.assertIsInstance(contracts[0], PrimeContract)
        self.assertIsInstance(contract, PrimeContract)
        self.assertEqual(found_contract.id, 31)
        self.assertIsInstance(owner_invoices[0], OwnerInvoice)
        self.assertIsInstance(owner_invoice, OwnerInvoice)
        self.assertIsInstance(subcontractor_invoices[0], SubcontractorInvoice)
        self.assertIsInstance(subcontractor_invoice, SubcontractorInvoice)
        self.assertIsInstance(payments[0], ContractPayment)
        self.assertIsInstance(billing_periods[0], BillingPeriod)
        self.assertIsInstance(cost_types[0], CostType)
        self.assertIsInstance(tax_codes[0], TaxCode)

    async def test_async_project_management_resources(self) -> None:
        """Project-management async methods should list/get typed read-only records."""
        client, _ = async_client(
            [
                json_response({"id": 41, "name": "Schedule"}),
                json_response({"id": 42, "schedule_type": "p6"}),
                json_response({"id": 43, "name": "Primavera"}),
                json_response({"id": 44, "provider": "p6"}),
                json_response({"id": 45, "status": "complete"}),
                json_response({"assignments": [{"id": 46, "name": "Crew"}]}),
                json_response({"tasks": [{"id": 47, "name": "Pour slab"}]}),
                json_response({"id": 47, "name": "Pour slab"}),
                json_response({"requested_changes": [{"id": 48, "title": "Shift"}]}),
                json_response({"calendar_items": [{"id": 49, "title": "Inspection"}]}),
                json_response({"id": 49, "title": "Inspection"}),
                json_response({"coordination_issues": [{"id": 50, "title": "Clash"}]}),
                json_response({"id": 50, "title": "Clash"}),
                json_response({"events": [{"id": 51, "event_type": "created"}]}),
                json_response({"activities": [{"id": 52, "action": "comment"}]}),
                json_response({"options": [{"id": 53, "name": "Open"}]}),
                json_response({"forms": [{"id": 54, "name": "Safety"}]}),
                json_response({"id": 54, "name": "Safety"}),
                json_response({"templates": [{"id": 55, "name": "Template"}]}),
                json_response({"action_plans": [{"id": 56, "name": "QA"}]}),
                json_response({"id": 56, "name": "QA"}),
                json_response({"events": [{"id": 57, "event_type": "updated"}]}),
            ]
        )

        schedule = await client.get_project_schedule(123, 456)
        schedule_settings = await client.get_schedule_settings(123, 456)
        schedule_type = await client.get_schedule_type(123, 456)
        schedule_integration = await client.get_schedule_integration(123, 456)
        import_status = await client.get_schedule_import_status(123, 456)
        assignments = await client.list_schedule_resource_assignments(123, 456)
        tasks = await client.list_tasks(123, 456)
        task = await client.get_task(123, 456, 47)
        requested_changes = await client.list_task_requested_changes(123, 456, 47)
        calendar_items = await client.list_calendar_items(123, 456)
        calendar_item = await client.get_calendar_item(123, 456, 49)
        issues = await client.list_coordination_issues(123, 456)
        issue = await client.get_coordination_issue(123, 456, 50)
        issue_history = await client.list_coordination_issue_change_history(123, 456, 50)
        issue_activity = await client.list_coordination_issue_activity(123, 456, 50)
        filter_options = await client.list_coordination_issue_filter_options(
            123,
            456,
            option_type="status",
        )
        forms = await client.list_forms(123, 456)
        form = await client.get_form(123, 456, 54)
        templates = await client.list_form_templates(123, 456)
        action_plans = await client.list_action_plans(123, 456)
        action_plan = await client.get_action_plan(123, 456, 56)
        action_history = await client.list_action_plan_change_history(123, 456, 56)

        self.assertIsInstance(schedule, ProjectSchedule)
        self.assertIsInstance(schedule_settings, ScheduleSettings)
        self.assertIsInstance(schedule_type, ScheduleType)
        self.assertIsInstance(schedule_integration, ScheduleIntegration)
        self.assertIsInstance(import_status, ScheduleImportStatus)
        self.assertIsInstance(assignments[0], ScheduleResourceAssignment)
        self.assertIsInstance(tasks[0], Task)
        self.assertIsInstance(task, Task)
        self.assertIsInstance(requested_changes[0], TaskRequestedChange)
        self.assertIsInstance(calendar_items[0], CalendarItem)
        self.assertIsInstance(calendar_item, CalendarItem)
        self.assertIsInstance(issues[0], CoordinationIssue)
        self.assertIsInstance(issue, CoordinationIssue)
        self.assertIsInstance(issue_history[0], CoordinationIssueChangeHistoryEvent)
        self.assertIsInstance(issue_activity[0], CoordinationIssueActivity)
        self.assertIsInstance(filter_options[0], CoordinationIssueFilterOption)
        self.assertIsInstance(forms[0], Form)
        self.assertIsInstance(form, Form)
        self.assertIsInstance(templates[0], FormTemplate)
        self.assertIsInstance(action_plans[0], ActionPlan)
        self.assertIsInstance(action_plan, ActionPlan)
        self.assertIsInstance(action_history[0], ActionPlanChangeHistoryEvent)

    async def test_async_exports_and_batch_resources(self) -> None:
        """New async exports and batch resources should write local files only."""
        client, _ = async_client(
            [
                json_response([{"id": 61, "number": "CE-1"}]),
                json_response([{"id": 62, "number": "PC-1"}]),
                json_response({"id": 63, "name": "Schedule"}),
                json_response([{"id": 64, "name": "Task"}]),
                json_response([{"id": 65, "number": "CE-2"}]),
                json_response([{"id": 66, "number": "PCO-1"}]),
                json_response([{"id": 67, "number": "REQ-1"}]),
                json_response({"id": 68, "name": "Schedule"}),
                json_response([{"id": 69, "name": "Task"}]),
                json_response([{"id": 70, "name": "Form"}]),
            ]
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            change_export = await async_export_change_events(client, 123, 456, tmp / "ce.jsonl")
            contract_export = await async_export_contracts(
                client, 123, 456, tmp / "contracts.csv", output_format="csv"
            )
            schedule_export = await async_export_project_schedule(
                client, 123, 456, tmp / "schedule.jsonl"
            )
            task_export = await async_export_tasks(client, 123, 456, tmp / "tasks.jsonl")
            batch = await async_collect_project_resources(
                client,
                123,
                456,
                [
                    "change_events",
                    "prime_change_orders",
                    "subcontractor_invoices",
                    "project_schedule",
                    "tasks",
                    "forms",
                ],
            )

            self.assertEqual(change_export.record_count, 1)
            self.assertEqual(contract_export.format, "csv")
            self.assertEqual(schedule_export.resource_name, "project_schedule")
            self.assertEqual(task_export.record_count, 1)
            self.assertTrue((tmp / "ce.jsonl").exists())
            self.assertTrue((tmp / "contracts.csv").exists())
            self.assertEqual([result.status for result in batch], ["completed"] * 6)

    def test_phase10e_exports_and_safety_are_discoverable(self) -> None:
        """Package exports and source code should preserve read-only safety boundaries."""
        for name in (
            "change_events",
            "prime_change_orders",
            "commitment_change_orders",
            "direct_costs",
            "budget_views",
            "commitments",
            "contracts",
            "subcontractor_invoices",
            "project_schedule",
            "tasks",
            "calendar_items",
            "coordination_issues",
            "forms",
            "action_plans",
        ):
            self.assertIn(name, SUPPORTED_ASYNC_BATCH_RESOURCES)

        self.assertTrue(hasattr(pyprocore, "AsyncFinancialsClient"))
        self.assertTrue(hasattr(pyprocore, "async_export_change_events"))
        source = (PROJECT_ROOT / "pyprocore" / "async_client.py").read_text(encoding="utf-8")
        forbidden = (
            "async def create_",
            "async def update_",
            "async def delete_",
            "async def upload_",
            "async def approve_",
            "async def reject_",
            "async def submit_",
            "async def complete_",
            "async def pay_",
        )
        for phrase in forbidden:
            self.assertNotIn(phrase, source)
