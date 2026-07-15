"""Read-only contract, invoice, payment, and billing services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pyprocore.core import endpoints
from pyprocore.core.client import ProcoreClient
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
from pyprocore.services.financials import FinancialsService


class ContractsService(FinancialsService):
    """Service for read-only contracts, invoices, payments, and billing data."""

    def __init__(self, client: ProcoreClient | None = None) -> None:
        """Initialize the service.

        Args:
            client: Optional shared Procore HTTP client.
        """
        super().__init__(client=client)

    def list_prime_contracts(
        self,
        company_id: int | None,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[PrimeContract]:
        """Return project prime contracts."""
        return self._list_project_resource(
            company_id,
            project_id,
            endpoints.prime_contracts(project_id),
            PrimeContract,
            ("prime_contracts",),
            params=params,
            extra_params=extra_params,
        )

    def get_prime_contract(
        self,
        company_id: int | None,
        project_id: int,
        prime_contract_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> PrimeContract:
        """Return one prime contract."""
        return self._get_project_resource(
            company_id,
            project_id,
            prime_contract_id,
            "prime_contract_id",
            endpoints.prime_contract(project_id, prime_contract_id),
            PrimeContract,
            params=params,
            extra_params=extra_params,
        )

    def list_prime_contract_line_items(
        self,
        company_id: int | None,
        project_id: int,
        prime_contract_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[PrimeContractLineItem]:
        """Return line items for one prime contract."""
        self._validate_positive_id(prime_contract_id, "prime_contract_id")
        return self._list_project_resource(
            company_id,
            project_id,
            endpoints.prime_contract_line_items(project_id, prime_contract_id),
            PrimeContractLineItem,
            ("prime_contract_line_items", "line_items"),
            params=params,
            extra_params=extra_params,
        )

    def get_prime_contract_summary(
        self,
        company_id: int | None,
        project_id: int,
        prime_contract_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> PrimeContractSummary:
        """Return read-only summary data for one prime contract."""
        self._validate_positive_id(prime_contract_id, "prime_contract_id")
        response = self._get_project_payload(
            company_id,
            project_id,
            endpoints.prime_contract_summary(project_id, prime_contract_id),
            params=params,
            extra_params=extra_params,
        )
        return PrimeContractSummary.model_validate(response)

    def list_commitment_contracts(
        self,
        company_id: int | None,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[CommitmentContract]:
        """Return project commitment contracts."""
        return self._list_project_resource(
            company_id,
            project_id,
            endpoints.commitment_contracts(project_id),
            CommitmentContract,
            ("commitment_contracts", "commitments", "contracts"),
            params=params,
            extra_params=extra_params,
        )

    def get_commitment_contract(
        self,
        company_id: int | None,
        project_id: int,
        commitment_contract_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> CommitmentContract:
        """Return one commitment contract."""
        return self._get_project_resource(
            company_id,
            project_id,
            commitment_contract_id,
            "commitment_contract_id",
            endpoints.commitment_contract(project_id, commitment_contract_id),
            CommitmentContract,
            params=params,
            extra_params=extra_params,
        )

    def list_purchase_order_contracts(
        self,
        company_id: int | None,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[PurchaseOrderContract]:
        """Return project purchase order contracts."""
        return self._list_project_resource(
            company_id,
            project_id,
            endpoints.purchase_order_contracts(project_id),
            PurchaseOrderContract,
            ("purchase_order_contracts", "purchase_orders", "contracts"),
            params=params,
            extra_params=extra_params,
        )

    def get_purchase_order_contract(
        self,
        company_id: int | None,
        project_id: int,
        purchase_order_contract_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> PurchaseOrderContract:
        """Return one purchase order contract."""
        return self._get_project_resource(
            company_id,
            project_id,
            purchase_order_contract_id,
            "purchase_order_contract_id",
            endpoints.purchase_order_contract(project_id, purchase_order_contract_id),
            PurchaseOrderContract,
            params=params,
            extra_params=extra_params,
        )

    def list_work_order_contracts(
        self,
        company_id: int | None,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[WorkOrderContract]:
        """Return project work order contracts."""
        return self._list_project_resource(
            company_id,
            project_id,
            endpoints.work_order_contracts(project_id),
            WorkOrderContract,
            ("work_order_contracts", "work_orders", "contracts"),
            params=params,
            extra_params=extra_params,
        )

    def get_work_order_contract(
        self,
        company_id: int | None,
        project_id: int,
        work_order_contract_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> WorkOrderContract:
        """Return one work order contract."""
        return self._get_project_resource(
            company_id,
            project_id,
            work_order_contract_id,
            "work_order_contract_id",
            endpoints.work_order_contract(project_id, work_order_contract_id),
            WorkOrderContract,
            params=params,
            extra_params=extra_params,
        )

    def list_owner_invoices(
        self,
        company_id: int | None,
        project_id: int,
        prime_contract_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[OwnerInvoice]:
        """Return owner invoices/payment applications for one prime contract."""
        self._validate_positive_id(prime_contract_id, "prime_contract_id")
        return self._list_project_resource(
            company_id,
            project_id,
            endpoints.owner_invoices(project_id, prime_contract_id),
            OwnerInvoice,
            ("owner_invoices", "payment_applications", "invoices"),
            params=params,
            extra_params=extra_params,
        )

    def get_owner_invoice(
        self,
        company_id: int | None,
        project_id: int,
        prime_contract_id: int,
        owner_invoice_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> OwnerInvoice:
        """Return one owner invoice/payment application."""
        self._validate_positive_id(prime_contract_id, "prime_contract_id")
        return self._get_project_resource(
            company_id,
            project_id,
            owner_invoice_id,
            "owner_invoice_id",
            endpoints.owner_invoice(project_id, prime_contract_id, owner_invoice_id),
            OwnerInvoice,
            params=params,
            extra_params=extra_params,
        )

    def list_owner_invoice_line_items(
        self,
        company_id: int | None,
        project_id: int,
        prime_contract_id: int,
        owner_invoice_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[OwnerInvoiceLineItem]:
        """Return line items for one owner invoice."""
        self._validate_positive_id(prime_contract_id, "prime_contract_id")
        self._validate_positive_id(owner_invoice_id, "owner_invoice_id")
        return self._list_project_resource(
            company_id,
            project_id,
            endpoints.owner_invoice_line_items(
                project_id,
                prime_contract_id,
                owner_invoice_id,
            ),
            OwnerInvoiceLineItem,
            ("owner_invoice_line_items", "line_items"),
            params=params,
            extra_params=extra_params,
        )

    def list_subcontractor_invoices(
        self,
        company_id: int | None,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[SubcontractorInvoice]:
        """Return subcontractor invoices/requisitions for a project."""
        return self._list_project_resource(
            company_id,
            project_id,
            endpoints.subcontractor_invoices(project_id),
            SubcontractorInvoice,
            ("subcontractor_invoices", "requisitions", "invoices"),
            params=params,
            extra_params=extra_params,
        )

    def get_subcontractor_invoice(
        self,
        company_id: int | None,
        project_id: int,
        subcontractor_invoice_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> SubcontractorInvoice:
        """Return one subcontractor invoice/requisition."""
        return self._get_project_resource(
            company_id,
            project_id,
            subcontractor_invoice_id,
            "subcontractor_invoice_id",
            endpoints.subcontractor_invoice(project_id, subcontractor_invoice_id),
            SubcontractorInvoice,
            params=params,
            extra_params=extra_params,
        )

    def list_requisition_contract_items(
        self,
        company_id: int | None,
        project_id: int,
        requisition_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[RequisitionContractItem]:
        """Return contract items for one requisition."""
        self._validate_positive_id(requisition_id, "requisition_id")
        return self._list_project_resource(
            company_id,
            project_id,
            endpoints.requisition_contract_items(project_id, requisition_id),
            RequisitionContractItem,
            ("requisition_contract_items", "contract_items"),
            params=params,
            extra_params=extra_params,
        )

    def list_requisition_contract_detail_items(
        self,
        company_id: int | None,
        project_id: int,
        requisition_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[RequisitionContractDetailItem]:
        """Return contract detail items for one requisition."""
        self._validate_positive_id(requisition_id, "requisition_id")
        return self._list_project_resource(
            company_id,
            project_id,
            endpoints.requisition_contract_detail_items(project_id, requisition_id),
            RequisitionContractDetailItem,
            ("requisition_contract_detail_items", "contract_detail_items"),
            params=params,
            extra_params=extra_params,
        )

    def list_requisition_change_order_items(
        self,
        company_id: int | None,
        project_id: int,
        requisition_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[RequisitionChangeOrderItem]:
        """Return change order items for one requisition."""
        self._validate_positive_id(requisition_id, "requisition_id")
        return self._list_project_resource(
            company_id,
            project_id,
            endpoints.requisition_change_order_items(project_id, requisition_id),
            RequisitionChangeOrderItem,
            ("requisition_change_order_items", "change_order_items"),
            params=params,
            extra_params=extra_params,
        )

    def list_contract_payments(
        self,
        company_id: int | None,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[ContractPayment]:
        """Return project contract payments."""
        return self._list_project_resource(
            company_id,
            project_id,
            endpoints.contract_payments(project_id),
            ContractPayment,
            ("contract_payments", "payments"),
            params=params,
            extra_params=extra_params,
        )

    def get_contract_payment(
        self,
        company_id: int | None,
        project_id: int,
        contract_payment_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> ContractPayment:
        """Return one contract payment."""
        return self._get_project_resource(
            company_id,
            project_id,
            contract_payment_id,
            "contract_payment_id",
            endpoints.contract_payment(project_id, contract_payment_id),
            ContractPayment,
            params=params,
            extra_params=extra_params,
        )

    def list_billing_periods(
        self,
        company_id: int | None,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[BillingPeriod]:
        """Return project billing periods."""
        return self._list_project_resource(
            company_id,
            project_id,
            endpoints.billing_periods(project_id),
            BillingPeriod,
            ("billing_periods",),
            params=params,
            extra_params=extra_params,
        )

    def get_billing_period(
        self,
        company_id: int | None,
        project_id: int,
        billing_period_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> BillingPeriod:
        """Return one billing period."""
        return self._get_project_resource(
            company_id,
            project_id,
            billing_period_id,
            "billing_period_id",
            endpoints.billing_period(project_id, billing_period_id),
            BillingPeriod,
            params=params,
            extra_params=extra_params,
        )

    def list_cost_types(
        self,
        company_id: int | None,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[CostType]:
        """Return company cost types."""
        resolved_company_id = self._resolve_company_id(company_id)
        response = self._client.get_all(
            endpoints.cost_types(resolved_company_id),
            params=self._query_params(params=params, extra_params=extra_params),
            headers=self._company_headers(resolved_company_id),
        )
        return self._parse_list(response, CostType, ("cost_types",))

    def list_tax_codes(
        self,
        company_id: int | None,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[TaxCode]:
        """Return company tax codes."""
        resolved_company_id = self._resolve_company_id(company_id)
        response = self._client.get_all(
            endpoints.tax_codes(resolved_company_id),
            params=self._query_params(params=params, extra_params=extra_params),
            headers=self._company_headers(resolved_company_id),
        )
        return self._parse_list(response, TaxCode, ("tax_codes",))


def list_prime_contracts(
    company_id: int | None,
    project_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[PrimeContract]:
    """Return project prime contracts."""
    return ContractsService(client=client).list_prime_contracts(company_id, project_id, **params)


def get_prime_contract(
    company_id: int | None,
    project_id: int,
    prime_contract_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> PrimeContract:
    """Return one prime contract."""
    return ContractsService(client=client).get_prime_contract(
        company_id,
        project_id,
        prime_contract_id,
        **params,
    )


def list_prime_contract_line_items(
    company_id: int | None,
    project_id: int,
    prime_contract_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[PrimeContractLineItem]:
    """Return line items for one prime contract."""
    return ContractsService(client=client).list_prime_contract_line_items(
        company_id,
        project_id,
        prime_contract_id,
        **params,
    )


def get_prime_contract_summary(
    company_id: int | None,
    project_id: int,
    prime_contract_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> PrimeContractSummary:
    """Return read-only summary data for one prime contract."""
    return ContractsService(client=client).get_prime_contract_summary(
        company_id,
        project_id,
        prime_contract_id,
        **params,
    )


def list_commitment_contracts(
    company_id: int | None,
    project_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[CommitmentContract]:
    """Return project commitment contracts."""
    return ContractsService(client=client).list_commitment_contracts(
        company_id,
        project_id,
        **params,
    )


def get_commitment_contract(
    company_id: int | None,
    project_id: int,
    commitment_contract_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> CommitmentContract:
    """Return one commitment contract."""
    return ContractsService(client=client).get_commitment_contract(
        company_id,
        project_id,
        commitment_contract_id,
        **params,
    )


def list_purchase_order_contracts(
    company_id: int | None,
    project_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[PurchaseOrderContract]:
    """Return project purchase order contracts."""
    return ContractsService(client=client).list_purchase_order_contracts(
        company_id,
        project_id,
        **params,
    )


def get_purchase_order_contract(
    company_id: int | None,
    project_id: int,
    purchase_order_contract_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> PurchaseOrderContract:
    """Return one purchase order contract."""
    return ContractsService(client=client).get_purchase_order_contract(
        company_id,
        project_id,
        purchase_order_contract_id,
        **params,
    )


def list_work_order_contracts(
    company_id: int | None,
    project_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[WorkOrderContract]:
    """Return project work order contracts."""
    return ContractsService(client=client).list_work_order_contracts(
        company_id,
        project_id,
        **params,
    )


def get_work_order_contract(
    company_id: int | None,
    project_id: int,
    work_order_contract_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> WorkOrderContract:
    """Return one work order contract."""
    return ContractsService(client=client).get_work_order_contract(
        company_id,
        project_id,
        work_order_contract_id,
        **params,
    )


def list_owner_invoices(
    company_id: int | None,
    project_id: int,
    prime_contract_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[OwnerInvoice]:
    """Return owner invoices/payment applications for one prime contract."""
    return ContractsService(client=client).list_owner_invoices(
        company_id,
        project_id,
        prime_contract_id,
        **params,
    )


def list_payment_applications(
    company_id: int | None,
    project_id: int,
    prime_contract_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[OwnerInvoice]:
    """Return owner invoices using payment application terminology."""
    return list_owner_invoices(
        company_id,
        project_id,
        prime_contract_id,
        client=client,
        **params,
    )


def get_owner_invoice(
    company_id: int | None,
    project_id: int,
    prime_contract_id: int,
    owner_invoice_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> OwnerInvoice:
    """Return one owner invoice/payment application."""
    return ContractsService(client=client).get_owner_invoice(
        company_id,
        project_id,
        prime_contract_id,
        owner_invoice_id,
        **params,
    )


def list_owner_invoice_line_items(
    company_id: int | None,
    project_id: int,
    prime_contract_id: int,
    owner_invoice_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[OwnerInvoiceLineItem]:
    """Return line items for one owner invoice."""
    return ContractsService(client=client).list_owner_invoice_line_items(
        company_id,
        project_id,
        prime_contract_id,
        owner_invoice_id,
        **params,
    )


def list_subcontractor_invoices(
    company_id: int | None,
    project_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[SubcontractorInvoice]:
    """Return subcontractor invoices/requisitions for a project."""
    return ContractsService(client=client).list_subcontractor_invoices(
        company_id,
        project_id,
        **params,
    )


def list_requisitions(
    company_id: int | None,
    project_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[SubcontractorInvoice]:
    """Return subcontractor invoices using requisition terminology."""
    return list_subcontractor_invoices(company_id, project_id, client=client, **params)


def get_subcontractor_invoice(
    company_id: int | None,
    project_id: int,
    subcontractor_invoice_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> SubcontractorInvoice:
    """Return one subcontractor invoice/requisition."""
    return ContractsService(client=client).get_subcontractor_invoice(
        company_id,
        project_id,
        subcontractor_invoice_id,
        **params,
    )


def list_requisition_contract_items(
    company_id: int | None,
    project_id: int,
    requisition_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[RequisitionContractItem]:
    """Return contract items for one requisition."""
    return ContractsService(client=client).list_requisition_contract_items(
        company_id,
        project_id,
        requisition_id,
        **params,
    )


def list_requisition_contract_detail_items(
    company_id: int | None,
    project_id: int,
    requisition_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[RequisitionContractDetailItem]:
    """Return contract detail items for one requisition."""
    return ContractsService(client=client).list_requisition_contract_detail_items(
        company_id,
        project_id,
        requisition_id,
        **params,
    )


def list_requisition_change_order_items(
    company_id: int | None,
    project_id: int,
    requisition_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[RequisitionChangeOrderItem]:
    """Return change order items for one requisition."""
    return ContractsService(client=client).list_requisition_change_order_items(
        company_id,
        project_id,
        requisition_id,
        **params,
    )


def list_contract_payments(
    company_id: int | None,
    project_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[ContractPayment]:
    """Return project contract payments."""
    return ContractsService(client=client).list_contract_payments(company_id, project_id, **params)


def get_contract_payment(
    company_id: int | None,
    project_id: int,
    contract_payment_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> ContractPayment:
    """Return one contract payment."""
    return ContractsService(client=client).get_contract_payment(
        company_id,
        project_id,
        contract_payment_id,
        **params,
    )


def list_billing_periods(
    company_id: int | None,
    project_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[BillingPeriod]:
    """Return project billing periods."""
    return ContractsService(client=client).list_billing_periods(company_id, project_id, **params)


def get_billing_period(
    company_id: int | None,
    project_id: int,
    billing_period_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> BillingPeriod:
    """Return one billing period."""
    return ContractsService(client=client).get_billing_period(
        company_id,
        project_id,
        billing_period_id,
        **params,
    )


def list_cost_types(
    company_id: int | None,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[CostType]:
    """Return company cost types."""
    return ContractsService(client=client).list_cost_types(company_id, **params)


def list_tax_codes(
    company_id: int | None,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[TaxCode]:
    """Return company tax codes."""
    return ContractsService(client=client).list_tax_codes(company_id, **params)
