"""Tests for Phase 8F read-only contracts, invoices, and payments coverage."""

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
    BillingPeriod,
    CommitmentContract,
    ContractPayment,
    CostType,
    OwnerInvoice,
    OwnerInvoiceLineItem,
    PrimeContract,
    PrimeContractLineItem,
    PrimeContractSummary,
    PurchaseOrderContract,
    RequisitionChangeOrderItem,
    RequisitionContractDetailItem,
    RequisitionContractItem,
    SubcontractorInvoice,
    TaxCode,
    WorkOrderContract,
)
from pyprocore.services import contracts
from pyprocore.services.contracts import ContractsService
from pyprocore.services.search import (
    find_contract_payment,
    find_owner_invoice,
    find_prime_contract,
    find_subcontractor_invoice,
)
from pyprocore.workflows import exports as exports_module
from pyprocore.workflows.exports import (
    export_billing_periods_to_csv,
    export_contract_payments_to_csv,
    export_cost_types_to_csv,
    export_owner_invoices_to_csv,
    export_prime_contracts_to_csv,
    export_subcontractor_invoices_to_csv,
    export_tax_codes_to_csv,
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


class Phase8FEndpointTestCase(unittest.TestCase):
    """Endpoint construction tests for Phase 8F resources."""

    def test_phase8f_endpoint_paths(self) -> None:
        """Endpoint helpers should return read-only contract paths."""
        self.assertEqual(endpoints.prime_contracts(123), "/rest/v1.0/projects/123/prime_contracts")
        self.assertEqual(
            endpoints.prime_contract_line_items(123, 7),
            "/rest/v1.0/projects/123/prime_contracts/7/line_items",
        )
        self.assertEqual(
            endpoints.owner_invoices(123, 7),
            "/rest/v1.0/projects/123/prime_contracts/7/owner_invoices",
        )
        self.assertEqual(
            endpoints.subcontractor_invoices(123),
            "/rest/v1.0/projects/123/requisitions",
        )
        self.assertEqual(
            endpoints.contract_payment(123, 8),
            "/rest/v1.0/projects/123/contract_payments/8",
        )
        self.assertEqual(endpoints.cost_types(456), "/rest/v1.0/companies/456/cost_types")
        self.assertEqual(endpoints.tax_codes(456), "/rest/v1.0/companies/456/tax_codes")


class Phase8FServiceTestCase(unittest.TestCase):
    """Service tests with mocked HTTP client behavior."""

    def test_list_and_get_prime_contracts(self) -> None:
        """Prime contracts should use project paths and company headers."""
        fake = FakeClient()
        fake.list_response = {"prime_contracts": [{"id": 1, "number": "PC-1"}]}
        service = ContractsService(client=fake)

        contracts_list = service.list_prime_contracts(456, 123, status="approved")

        self.assertIsInstance(contracts_list[0], PrimeContract)
        self.assertEqual(fake.calls[0][1], "/rest/v1.0/projects/123/prime_contracts")
        self.assertEqual(fake.calls[0][2], {"status": "approved"})
        self.assertEqual(fake.calls[0][3], {"Procore-Company-Id": "456"})

        fake.get_response = {"id": 1, "number": "PC-1"}
        contract = service.get_prime_contract(456, 123, 1)
        self.assertEqual(contract.number, "PC-1")
        self.assertEqual(fake.calls[-1][1], "/rest/v1.0/projects/123/prime_contracts/1")

    def test_contract_list_helpers_return_typed_models(self) -> None:
        """Phase 8F list helpers should parse typed models."""
        fake = FakeClient()
        service = ContractsService(client=fake)

        cases: list[tuple[str, str, type[object], tuple[int, ...]]] = [
            ("list_prime_contract_line_items", "line_items", PrimeContractLineItem, (456, 123, 7)),
            ("list_commitment_contracts", "commitment_contracts", CommitmentContract, (456, 123)),
            (
                "list_purchase_order_contracts",
                "purchase_order_contracts",
                PurchaseOrderContract,
                (456, 123),
            ),
            ("list_work_order_contracts", "work_order_contracts", WorkOrderContract, (456, 123)),
            ("list_owner_invoices", "owner_invoices", OwnerInvoice, (456, 123, 7)),
            (
                "list_owner_invoice_line_items",
                "line_items",
                OwnerInvoiceLineItem,
                (456, 123, 7, 9),
            ),
            (
                "list_subcontractor_invoices",
                "requisitions",
                SubcontractorInvoice,
                (456, 123),
            ),
            (
                "list_requisition_contract_items",
                "contract_items",
                RequisitionContractItem,
                (456, 123, 10),
            ),
            (
                "list_requisition_contract_detail_items",
                "contract_detail_items",
                RequisitionContractDetailItem,
                (456, 123, 10),
            ),
            (
                "list_requisition_change_order_items",
                "change_order_items",
                RequisitionChangeOrderItem,
                (456, 123, 10),
            ),
            ("list_contract_payments", "contract_payments", ContractPayment, (456, 123)),
            ("list_billing_periods", "billing_periods", BillingPeriod, (456, 123)),
        ]
        for method_name, response_key, model_type, args in cases:
            fake.list_response = {response_key: [{"id": 1, "number": "1", "name": "Item"}]}
            result = getattr(service, method_name)(*args)
            self.assertIsInstance(result[0], model_type)

        fake.list_response = {"cost_types": [{"id": 2, "name": "Labor"}]}
        self.assertIsInstance(service.list_cost_types(456)[0], CostType)
        fake.list_response = {"tax_codes": [{"id": 3, "name": "Tax"}]}
        self.assertIsInstance(service.list_tax_codes(456)[0], TaxCode)

    def test_get_helpers_and_module_aliases(self) -> None:
        """Get helpers and aliases should preserve typed responses."""
        fake = FakeClient()
        service = ContractsService(client=fake)
        fake.get_response = {"id": 1, "number": "1", "summary": {}}
        self.assertIsInstance(service.get_prime_contract_summary(456, 123, 1), PrimeContractSummary)

        get_cases = [
            (service.get_commitment_contract, CommitmentContract, (456, 123, 1)),
            (service.get_purchase_order_contract, PurchaseOrderContract, (456, 123, 2)),
            (service.get_work_order_contract, WorkOrderContract, (456, 123, 3)),
            (service.get_owner_invoice, OwnerInvoice, (456, 123, 4, 5)),
            (service.get_subcontractor_invoice, SubcontractorInvoice, (456, 123, 6)),
            (service.get_contract_payment, ContractPayment, (456, 123, 7)),
            (service.get_billing_period, BillingPeriod, (456, 123, 8)),
        ]
        for method, model_type, args in get_cases:
            fake.get_response = {"id": args[-1], "number": "1", "name": "Item"}
            self.assertIsInstance(method(*args), model_type)

        fake.list_response = [{"id": 9, "number": "REQ-1"}]
        self.assertIsInstance(
            contracts.list_requisitions(456, 123, client=fake)[0], SubcontractorInvoice
        )

    def test_module_level_wrappers_delegate_to_service(self) -> None:
        """Module-level helpers should keep the public functional API covered."""
        fake = FakeClient()
        fake.list_response = [{"id": 1, "number": "1", "name": "Item"}]

        list_cases = [
            (contracts.list_prime_contracts, (456, 123), PrimeContract),
            (contracts.list_prime_contract_line_items, (456, 123, 7), PrimeContractLineItem),
            (contracts.list_commitment_contracts, (456, 123), CommitmentContract),
            (contracts.list_purchase_order_contracts, (456, 123), PurchaseOrderContract),
            (contracts.list_work_order_contracts, (456, 123), WorkOrderContract),
            (contracts.list_owner_invoices, (456, 123, 7), OwnerInvoice),
            (contracts.list_payment_applications, (456, 123, 7), OwnerInvoice),
            (contracts.list_owner_invoice_line_items, (456, 123, 7, 9), OwnerInvoiceLineItem),
            (contracts.list_subcontractor_invoices, (456, 123), SubcontractorInvoice),
            (contracts.list_requisitions, (456, 123), SubcontractorInvoice),
            (contracts.list_requisition_contract_items, (456, 123, 10), RequisitionContractItem),
            (
                contracts.list_requisition_contract_detail_items,
                (456, 123, 10),
                RequisitionContractDetailItem,
            ),
            (
                contracts.list_requisition_change_order_items,
                (456, 123, 10),
                RequisitionChangeOrderItem,
            ),
            (contracts.list_contract_payments, (456, 123), ContractPayment),
            (contracts.list_billing_periods, (456, 123), BillingPeriod),
            (contracts.list_cost_types, (456,), CostType),
            (contracts.list_tax_codes, (456,), TaxCode),
        ]
        for function, args, model_type in list_cases:
            self.assertIsInstance(function(*args, client=fake)[0], model_type)

        fake.get_response = {"id": 1, "number": "1", "name": "Item"}
        get_cases = [
            (contracts.get_prime_contract, (456, 123, 1), PrimeContract),
            (contracts.get_prime_contract_summary, (456, 123, 1), PrimeContractSummary),
            (contracts.get_commitment_contract, (456, 123, 1), CommitmentContract),
            (contracts.get_purchase_order_contract, (456, 123, 1), PurchaseOrderContract),
            (contracts.get_work_order_contract, (456, 123, 1), WorkOrderContract),
            (contracts.get_owner_invoice, (456, 123, 7, 1), OwnerInvoice),
            (contracts.get_subcontractor_invoice, (456, 123, 1), SubcontractorInvoice),
            (contracts.get_contract_payment, (456, 123, 1), ContractPayment),
            (contracts.get_billing_period, (456, 123, 1), BillingPeriod),
        ]
        for function, args, model_type in get_cases:
            self.assertIsInstance(function(*args, client=fake), model_type)


class Phase8FIntegrationSurfaceTestCase(unittest.TestCase):
    """Search, export, object-client, CLI, and agent metadata tests."""

    def test_search_helpers_resolve_matches(self) -> None:
        """Search helpers should resolve typed models from mocked lists."""
        with patch(
            "pyprocore.services.search.list_prime_contracts",
            return_value=[PrimeContract(id=1, number="7")],
        ):
            self.assertEqual(find_prime_contract(123, number="7", company_id=456).id, 1)
        with patch(
            "pyprocore.services.search.list_owner_invoices",
            return_value=[OwnerInvoice(id=2, number="OI-1")],
        ):
            self.assertEqual(find_owner_invoice(123, 7, number="OI-1", company_id=456).id, 2)
        with patch(
            "pyprocore.services.search.list_subcontractor_invoices",
            return_value=[SubcontractorInvoice(id=3, number="REQ-1")],
        ):
            self.assertEqual(find_subcontractor_invoice(123, number="REQ-1", company_id=456).id, 3)
        with patch(
            "pyprocore.services.search.list_contract_payments",
            return_value=[ContractPayment(id=4, number="PAY-1")],
        ):
            self.assertEqual(find_contract_payment(123, number="PAY-1", company_id=456).id, 4)

    def test_exports_write_csv_files(self) -> None:
        """Phase 8F exports should write local CSV files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            export_cases = [
                (
                    "pyprocore.workflows.exports.list_prime_contracts",
                    [PrimeContract(id=1)],
                    export_prime_contracts_to_csv,
                    (456, 123, Path(temp_dir) / "pc.csv"),
                ),
                (
                    "pyprocore.workflows.exports.list_owner_invoices",
                    [OwnerInvoice(id=2)],
                    export_owner_invoices_to_csv,
                    (456, 123, 7, Path(temp_dir) / "owner.csv"),
                ),
                (
                    "pyprocore.workflows.exports.list_subcontractor_invoices",
                    [SubcontractorInvoice(id=3)],
                    export_subcontractor_invoices_to_csv,
                    (456, 123, Path(temp_dir) / "subs.csv"),
                ),
                (
                    "pyprocore.workflows.exports.list_contract_payments",
                    [ContractPayment(id=4)],
                    export_contract_payments_to_csv,
                    (456, 123, Path(temp_dir) / "payments.csv"),
                ),
                (
                    "pyprocore.workflows.exports.list_billing_periods",
                    [BillingPeriod(id=5)],
                    export_billing_periods_to_csv,
                    (456, 123, Path(temp_dir) / "billing.csv"),
                ),
                (
                    "pyprocore.workflows.exports.list_cost_types",
                    [CostType(id=6)],
                    export_cost_types_to_csv,
                    (456, Path(temp_dir) / "cost-types.csv"),
                ),
                (
                    "pyprocore.workflows.exports.list_tax_codes",
                    [TaxCode(id=7)],
                    export_tax_codes_to_csv,
                    (456, Path(temp_dir) / "tax.csv"),
                ),
            ]
            for patch_path, return_value, export_func, args in export_cases:
                with patch(patch_path, return_value=return_value):
                    self.assertTrue(export_func(*args).exists())

    def test_phase8f_jsonl_exports_write_files(self) -> None:
        """Phase 8F JSONL exports should write local newline-delimited JSON files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            export_cases = [
                (
                    "list_prime_contracts",
                    [PrimeContract(id=1)],
                    exports_module.export_prime_contracts_to_jsonl,
                    (456, 123, Path(temp_dir) / "prime.jsonl"),
                ),
                (
                    "list_prime_contract_line_items",
                    [PrimeContractLineItem(id=2)],
                    exports_module.export_prime_contract_line_items_to_jsonl,
                    (456, 123, 7, Path(temp_dir) / "prime-lines.jsonl"),
                ),
                (
                    "list_commitment_contracts",
                    [CommitmentContract(id=3)],
                    exports_module.export_commitment_contracts_to_jsonl,
                    (456, 123, Path(temp_dir) / "commitments.jsonl"),
                ),
                (
                    "list_purchase_order_contracts",
                    [PurchaseOrderContract(id=4)],
                    exports_module.export_purchase_order_contracts_to_jsonl,
                    (456, 123, Path(temp_dir) / "purchase-orders.jsonl"),
                ),
                (
                    "list_work_order_contracts",
                    [WorkOrderContract(id=5)],
                    exports_module.export_work_order_contracts_to_jsonl,
                    (456, 123, Path(temp_dir) / "work-orders.jsonl"),
                ),
                (
                    "list_owner_invoices",
                    [OwnerInvoice(id=6)],
                    exports_module.export_owner_invoices_to_jsonl,
                    (456, 123, 7, Path(temp_dir) / "owner.jsonl"),
                ),
                (
                    "list_owner_invoice_line_items",
                    [OwnerInvoiceLineItem(id=7)],
                    exports_module.export_owner_invoice_line_items_to_jsonl,
                    (456, 123, 7, 9, Path(temp_dir) / "owner-lines.jsonl"),
                ),
                (
                    "list_subcontractor_invoices",
                    [SubcontractorInvoice(id=8)],
                    exports_module.export_subcontractor_invoices_to_jsonl,
                    (456, 123, Path(temp_dir) / "subs.jsonl"),
                ),
                (
                    "list_requisition_contract_items",
                    [RequisitionContractItem(id=9)],
                    exports_module.export_requisition_contract_items_to_jsonl,
                    (456, 123, 10, Path(temp_dir) / "req-items.jsonl"),
                ),
                (
                    "list_requisition_contract_detail_items",
                    [RequisitionContractDetailItem(id=10)],
                    exports_module.export_requisition_contract_detail_items_to_jsonl,
                    (456, 123, 10, Path(temp_dir) / "req-details.jsonl"),
                ),
                (
                    "list_requisition_change_order_items",
                    [RequisitionChangeOrderItem(id=11)],
                    exports_module.export_requisition_change_order_items_to_jsonl,
                    (456, 123, 10, Path(temp_dir) / "req-changes.jsonl"),
                ),
                (
                    "list_contract_payments",
                    [ContractPayment(id=12)],
                    exports_module.export_contract_payments_to_jsonl,
                    (456, 123, Path(temp_dir) / "payments.jsonl"),
                ),
                (
                    "list_billing_periods",
                    [BillingPeriod(id=13)],
                    exports_module.export_billing_periods_to_jsonl,
                    (456, 123, Path(temp_dir) / "billing.jsonl"),
                ),
                (
                    "list_cost_types",
                    [CostType(id=14)],
                    exports_module.export_cost_types_to_jsonl,
                    (456, Path(temp_dir) / "cost-types.jsonl"),
                ),
                (
                    "list_tax_codes",
                    [TaxCode(id=15)],
                    exports_module.export_tax_codes_to_jsonl,
                    (456, Path(temp_dir) / "tax.jsonl"),
                ),
            ]
            for loader_name, return_value, export_func, args in export_cases:
                with patch(f"pyprocore.workflows.exports.{loader_name}", return_value=return_value):
                    output_path = export_func(*args)
                    self.assertTrue(output_path.exists())
                    self.assertIn('"id"', output_path.read_text(encoding="utf-8"))

    def test_phase8f_write_helpers_cover_csv_variants(self) -> None:
        """Phase 8F write helpers should support already-loaded typed models."""
        with tempfile.TemporaryDirectory() as temp_dir:
            write_cases = [
                (exports_module.write_prime_contracts_csv, [PrimeContract(id=1)], "prime.csv"),
                (
                    exports_module.write_prime_contract_line_items_csv,
                    [PrimeContractLineItem(id=2)],
                    "prime-lines.csv",
                ),
                (
                    exports_module.write_commitment_contracts_csv,
                    [CommitmentContract(id=3)],
                    "commitments.csv",
                ),
                (
                    exports_module.write_purchase_order_contracts_csv,
                    [PurchaseOrderContract(id=4)],
                    "purchase-orders.csv",
                ),
                (
                    exports_module.write_work_order_contracts_csv,
                    [WorkOrderContract(id=5)],
                    "work-orders.csv",
                ),
                (exports_module.write_owner_invoices_csv, [OwnerInvoice(id=6)], "owner.csv"),
                (
                    exports_module.write_owner_invoice_line_items_csv,
                    [OwnerInvoiceLineItem(id=7)],
                    "owner-lines.csv",
                ),
                (
                    exports_module.write_subcontractor_invoices_csv,
                    [SubcontractorInvoice(id=8)],
                    "subs.csv",
                ),
                (
                    exports_module.write_requisition_contract_items_csv,
                    [RequisitionContractItem(id=9)],
                    "req-items.csv",
                ),
                (
                    exports_module.write_requisition_contract_detail_items_csv,
                    [RequisitionContractDetailItem(id=10)],
                    "req-details.csv",
                ),
                (
                    exports_module.write_requisition_change_order_items_csv,
                    [RequisitionChangeOrderItem(id=11)],
                    "req-changes.csv",
                ),
                (
                    exports_module.write_contract_payments_csv,
                    [ContractPayment(id=12)],
                    "payments.csv",
                ),
                (
                    exports_module.write_billing_periods_csv,
                    [BillingPeriod(id=13)],
                    "billing.csv",
                ),
                (exports_module.write_cost_types_csv, [CostType(id=14)], "cost-types.csv"),
                (exports_module.write_tax_codes_csv, [TaxCode(id=15)], "tax.csv"),
            ]
            for write_func, items, file_name in write_cases:
                output_path = write_func(items, Path(temp_dir) / file_name)
                self.assertTrue(output_path.exists())

    def test_object_client_groups_delegate(self) -> None:
        """Object client groups should delegate to Phase 8F services."""
        client = Procore()
        with patch("pyprocore.client.list_prime_contracts", return_value=[PrimeContract(id=1)]):
            self.assertEqual(client.prime_contracts.list(123, company_id=456)[0].id, 1)
        with patch("pyprocore.client.get_prime_contract", return_value=PrimeContract(id=1)):
            self.assertEqual(client.prime_contracts.get(123, 1, company_id=456).id, 1)
        with patch("pyprocore.client.find_prime_contract", return_value=PrimeContract(id=1)):
            self.assertEqual(client.prime_contracts.find(123, company_id=456, number="1").id, 1)
        with patch(
            "pyprocore.client.list_prime_contract_line_items",
            return_value=[PrimeContractLineItem(id=11)],
        ):
            self.assertEqual(client.prime_contracts.line_items(123, 1, company_id=456)[0].id, 11)
        with patch(
            "pyprocore.client.get_prime_contract_summary",
            return_value=PrimeContractSummary(id=12),
        ):
            self.assertEqual(client.prime_contracts.summary(123, 1, company_id=456).id, 12)
        with patch(
            "pyprocore.client.list_commitment_contracts",
            return_value=[CommitmentContract(id=13)],
        ):
            self.assertEqual(client.commitment_contracts.list(123, company_id=456)[0].id, 13)
        with patch(
            "pyprocore.client.get_commitment_contract",
            return_value=CommitmentContract(id=14),
        ):
            self.assertEqual(client.commitment_contracts.get(123, 14, company_id=456).id, 14)
        with patch(
            "pyprocore.client.find_commitment_contract",
            return_value=CommitmentContract(id=15),
        ):
            self.assertEqual(client.commitment_contracts.find(123, company_id=456, name="C").id, 15)
        with patch(
            "pyprocore.client.list_purchase_order_contracts",
            return_value=[PurchaseOrderContract(id=16)],
        ):
            self.assertEqual(client.purchase_order_contracts.list(123, company_id=456)[0].id, 16)
        with patch(
            "pyprocore.client.get_purchase_order_contract",
            return_value=PurchaseOrderContract(id=17),
        ):
            self.assertEqual(client.purchase_order_contracts.get(123, 17, company_id=456).id, 17)
        with patch(
            "pyprocore.client.find_purchase_order_contract",
            return_value=PurchaseOrderContract(id=18),
        ):
            self.assertEqual(
                client.purchase_order_contracts.find(123, company_id=456, number="PO").id,
                18,
            )
        with patch(
            "pyprocore.client.list_work_order_contracts",
            return_value=[WorkOrderContract(id=19)],
        ):
            self.assertEqual(client.work_order_contracts.list(123, company_id=456)[0].id, 19)
        with patch(
            "pyprocore.client.get_work_order_contract",
            return_value=WorkOrderContract(id=20),
        ):
            self.assertEqual(client.work_order_contracts.get(123, 20, company_id=456).id, 20)
        with patch(
            "pyprocore.client.find_work_order_contract",
            return_value=WorkOrderContract(id=21),
        ):
            self.assertEqual(
                client.work_order_contracts.find(123, company_id=456, name="WO").id, 21
            )
        with patch("pyprocore.client.list_owner_invoices", return_value=[OwnerInvoice(id=2)]):
            self.assertEqual(client.owner_invoices.list(123, 7, company_id=456)[0].id, 2)
        with patch("pyprocore.client.get_owner_invoice", return_value=OwnerInvoice(id=22)):
            self.assertEqual(client.owner_invoices.get(123, 7, 22, company_id=456).id, 22)
        with patch("pyprocore.client.find_owner_invoice", return_value=OwnerInvoice(id=23)):
            self.assertEqual(client.owner_invoices.find(123, 7, company_id=456, number="OI").id, 23)
        with patch(
            "pyprocore.client.list_owner_invoice_line_items",
            return_value=[OwnerInvoiceLineItem(id=24)],
        ):
            self.assertEqual(client.owner_invoices.line_items(123, 7, 9, company_id=456)[0].id, 24)
        with patch(
            "pyprocore.client.list_subcontractor_invoices",
            return_value=[SubcontractorInvoice(id=25)],
        ):
            self.assertEqual(client.subcontractor_invoices.list(123, company_id=456)[0].id, 25)
        with patch(
            "pyprocore.client.get_subcontractor_invoice",
            return_value=SubcontractorInvoice(id=26),
        ):
            self.assertEqual(client.subcontractor_invoices.get(123, 26, company_id=456).id, 26)
        with patch(
            "pyprocore.client.find_subcontractor_invoice",
            return_value=SubcontractorInvoice(id=27),
        ):
            self.assertEqual(
                client.subcontractor_invoices.find(123, company_id=456, name="REQ").id,
                27,
            )
        with patch(
            "pyprocore.client.list_requisition_contract_items",
            return_value=[RequisitionContractItem(id=28)],
        ):
            self.assertEqual(
                client.subcontractor_invoices.contract_items(123, 10, company_id=456)[0].id,
                28,
            )
        with patch(
            "pyprocore.client.list_requisition_contract_detail_items",
            return_value=[RequisitionContractDetailItem(id=29)],
        ):
            self.assertEqual(
                client.subcontractor_invoices.contract_detail_items(123, 10, company_id=456)[0].id,
                29,
            )
        with patch(
            "pyprocore.client.list_requisition_change_order_items",
            return_value=[RequisitionChangeOrderItem(id=30)],
        ):
            self.assertEqual(
                client.subcontractor_invoices.change_order_items(123, 10, company_id=456)[0].id,
                30,
            )
        with patch("pyprocore.client.list_contract_payments", return_value=[ContractPayment(id=3)]):
            self.assertEqual(client.contract_payments.list(123, company_id=456)[0].id, 3)
        with patch("pyprocore.client.get_contract_payment", return_value=ContractPayment(id=31)):
            self.assertEqual(client.contract_payments.get(123, 31, company_id=456).id, 31)
        with patch("pyprocore.client.find_contract_payment", return_value=ContractPayment(id=32)):
            self.assertEqual(client.contract_payments.find(123, company_id=456, number="P").id, 32)
        with patch("pyprocore.client.list_billing_periods", return_value=[BillingPeriod(id=4)]):
            self.assertEqual(client.billing_periods.list(123, company_id=456)[0].id, 4)
        with patch("pyprocore.client.get_billing_period", return_value=BillingPeriod(id=33)):
            self.assertEqual(client.billing_periods.get(123, 33, company_id=456).id, 33)
        with patch("pyprocore.client.list_cost_types", return_value=[CostType(id=34)]):
            self.assertEqual(client.cost_types.list(456)[0].id, 34)
        with patch("pyprocore.client.list_tax_codes", return_value=[TaxCode(id=5)]):
            self.assertEqual(client.tax_codes.list(456)[0].id, 5)

    def test_cli_parser_and_routes(self) -> None:
        """CLI parser should include Phase 8F commands and route them."""
        parser = build_parser()
        route_cases = [
            (
                "prime-contracts --project 123 --company-id 456",
                "list_prime_contracts",
                [PrimeContract(id=1)],
            ),
            (
                "owner-invoices --project 123 --company-id 456 --prime-contract 7",
                "list_owner_invoices",
                [OwnerInvoice(id=1)],
            ),
            (
                "subcontractor-invoices --project 123 --company-id 456",
                "list_subcontractor_invoices",
                [SubcontractorInvoice(id=1)],
            ),
            (
                "contract-payments --project 123 --company-id 456",
                "list_contract_payments",
                [ContractPayment(id=1)],
            ),
            (
                "billing-periods --project 123 --company-id 456",
                "list_billing_periods",
                [BillingPeriod(id=1)],
            ),
            ("cost-types --company-id 456", "list_cost_types", [CostType(id=1)]),
            ("tax-codes --company-id 456", "list_tax_codes", [TaxCode(id=1)]),
        ]
        for command, function_name, return_value in route_cases:
            with patch(f"pyprocore.app.{function_name}", return_value=return_value):
                self.assertIsNotNone(run_command(parser.parse_args(command.split())))

    def test_cli_export_routes(self) -> None:
        """CLI export commands should route to Phase 8F CSV helpers."""
        parser = build_parser()
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "out.csv"
            route_cases = [
                (
                    f"export-prime-contracts --project 123 --company-id 456 --output {output_path}",
                    "export_prime_contracts_to_csv",
                ),
                (
                    "export-prime-contract-line-items --project 123 --company-id 456 "
                    f"--prime-contract 7 --output {output_path}",
                    "export_prime_contract_line_items_to_csv",
                ),
                (
                    "export-commitment-contracts --project 123 --company-id 456 "
                    f"--output {output_path}",
                    "export_commitment_contracts_to_csv",
                ),
                (
                    "export-purchase-order-contracts --project 123 --company-id 456 "
                    f"--output {output_path}",
                    "export_purchase_order_contracts_to_csv",
                ),
                (
                    "export-work-order-contracts --project 123 --company-id 456 "
                    f"--output {output_path}",
                    "export_work_order_contracts_to_csv",
                ),
                (
                    "export-owner-invoices --project 123 --company-id 456 "
                    f"--prime-contract 7 --output {output_path}",
                    "export_owner_invoices_to_csv",
                ),
                (
                    "export-owner-invoice-line-items --project 123 --company-id 456 "
                    f"--prime-contract 7 --owner-invoice 9 --output {output_path}",
                    "export_owner_invoice_line_items_to_csv",
                ),
                (
                    "export-subcontractor-invoices --project 123 --company-id 456 "
                    f"--output {output_path}",
                    "export_subcontractor_invoices_to_csv",
                ),
                (
                    "export-requisition-contract-items --project 123 --company-id 456 "
                    f"--requisition 10 --output {output_path}",
                    "export_requisition_contract_items_to_csv",
                ),
                (
                    "export-requisition-contract-detail-items --project 123 --company-id 456 "
                    f"--requisition 10 --output {output_path}",
                    "export_requisition_contract_detail_items_to_csv",
                ),
                (
                    "export-requisition-change-order-items --project 123 --company-id 456 "
                    f"--requisition 10 --output {output_path}",
                    "export_requisition_change_order_items_to_csv",
                ),
                (
                    "export-contract-payments --project 123 --company-id 456 "
                    f"--output {output_path}",
                    "export_contract_payments_to_csv",
                ),
                (
                    f"export-billing-periods --project 123 --company-id 456 --output {output_path}",
                    "export_billing_periods_to_csv",
                ),
                (
                    f"export-cost-types --company-id 456 --output {output_path}",
                    "export_cost_types_to_csv",
                ),
                (
                    f"export-tax-codes --company-id 456 --output {output_path}",
                    "export_tax_codes_to_csv",
                ),
            ]
            for command, function_name in route_cases:
                with patch(f"pyprocore.app.{function_name}", return_value=output_path):
                    self.assertEqual(run_command(parser.parse_args(command.split())), output_path)

    def test_agent_registry_and_mcp_include_phase8f_tools(self) -> None:
        """Agent and MCP discovery should include Phase 8F metadata only."""
        tool_names = {tool.name for tool in list_agent_tools()}
        self.assertIn("procore.list_prime_contracts", tool_names)
        self.assertIn("procore.list_owner_invoices", tool_names)
        self.assertIn("procore.list_contract_payments", tool_names)

        mcp_json = export_mcp_tools_json()
        self.assertIn("procore.list_billing_periods", mcp_json)
        self.assertIn("procore.list_tax_codes", mcp_json)

    def test_contract_modules_remain_read_only(self) -> None:
        """Contract service should not expose write, approval, or mutation verbs."""
        forbidden = (
            "create",
            "update",
            "delete",
            "approve",
            "reject",
            "submit",
            "void",
            "mutate",
            "generate_pdf",
        )
        public_functions = [
            name
            for name, value in inspect.getmembers(contracts)
            if inspect.isfunction(value) and not name.startswith("_")
        ]
        for name in public_functions:
            self.assertFalse(any(word in name for word in forbidden), name)

        parser_help = build_parser().format_help()
        self.assertNotIn("approve", parser_help)
        self.assertNotIn("submit-invoice", parser_help)
        self.assertNotIn("generate-pdf", parser_help)


if __name__ == "__main__":
    unittest.main()
