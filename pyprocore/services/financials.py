"""Read-only financial and change-management services for Procore resources."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from pyprocore.core import endpoints
from pyprocore.core.client import ProcoreClient
from pyprocore.core.config import get_settings
from pyprocore.core.exceptions import ValidationError
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
    ProcoreModel,
    WbsCode,
)
from pyprocore.services.query_params import build_query_params

ModelT = TypeVar("ModelT", bound=ProcoreModel)


class FinancialsService:
    """Service for read-only financial and change-management resources."""

    def __init__(self, client: ProcoreClient | None = None) -> None:
        """Initialize the service.

        Args:
            client: Optional shared Procore HTTP client.
        """
        self._client = client or ProcoreClient()

    def list_change_events(
        self,
        company_id: int | None,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[ChangeEvent]:
        """Return project change events."""
        return self._list_project_resource(
            company_id,
            project_id,
            endpoints.change_events(project_id),
            ChangeEvent,
            ("change_events",),
            params=params,
            extra_params=extra_params,
        )

    def get_change_event(
        self,
        company_id: int | None,
        project_id: int,
        change_event_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> ChangeEvent:
        """Return one project change event."""
        return self._get_project_resource(
            company_id,
            project_id,
            change_event_id,
            "change_event_id",
            endpoints.change_event(project_id, change_event_id),
            ChangeEvent,
            params=params,
            extra_params=extra_params,
        )

    def list_change_event_statuses(
        self,
        company_id: int | None,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[ChangeEventStatus]:
        """Return project change event statuses when exposed by Procore."""
        return self._list_project_resource(
            company_id,
            project_id,
            endpoints.change_event_statuses(project_id),
            ChangeEventStatus,
            ("change_event_statuses", "statuses"),
            params=params,
            extra_params=extra_params,
        )

    def list_change_event_types(
        self,
        company_id: int | None,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[ChangeEventType]:
        """Return project change event types when exposed by Procore."""
        return self._list_project_resource(
            company_id,
            project_id,
            endpoints.change_event_types(project_id),
            ChangeEventType,
            ("change_event_types", "types"),
            params=params,
            extra_params=extra_params,
        )

    def get_change_event_settings(
        self,
        company_id: int | None,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> ChangeEventSettings:
        """Return read-only project change event settings."""
        response = self._get_project_payload(
            company_id,
            project_id,
            endpoints.change_event_settings(project_id),
            params=params,
            extra_params=extra_params,
        )
        return ChangeEventSettings.model_validate(response)

    def list_prime_change_orders(
        self,
        company_id: int | None,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[PrimeChangeOrder]:
        """Return project prime change orders."""
        return self._list_project_resource(
            company_id,
            project_id,
            endpoints.prime_change_orders(project_id),
            PrimeChangeOrder,
            ("prime_change_orders",),
            params=params,
            extra_params=extra_params,
        )

    def get_prime_change_order(
        self,
        company_id: int | None,
        project_id: int,
        prime_change_order_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> PrimeChangeOrder:
        """Return one prime change order."""
        return self._get_project_resource(
            company_id,
            project_id,
            prime_change_order_id,
            "prime_change_order_id",
            endpoints.prime_change_order(project_id, prime_change_order_id),
            PrimeChangeOrder,
            params=params,
            extra_params=extra_params,
        )

    def list_commitment_change_orders(
        self,
        company_id: int | None,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[CommitmentChangeOrder]:
        """Return project commitment change orders."""
        return self._list_project_resource(
            company_id,
            project_id,
            endpoints.commitment_change_orders(project_id),
            CommitmentChangeOrder,
            ("commitment_change_orders",),
            params=params,
            extra_params=extra_params,
        )

    def get_commitment_change_order(
        self,
        company_id: int | None,
        project_id: int,
        commitment_change_order_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> CommitmentChangeOrder:
        """Return one commitment change order."""
        return self._get_project_resource(
            company_id,
            project_id,
            commitment_change_order_id,
            "commitment_change_order_id",
            endpoints.commitment_change_order(project_id, commitment_change_order_id),
            CommitmentChangeOrder,
            params=params,
            extra_params=extra_params,
        )

    def list_change_order_packages(
        self,
        company_id: int | None,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[ChangeOrderPackage]:
        """Return project change order packages."""
        return self._list_project_resource(
            company_id,
            project_id,
            endpoints.change_order_packages(project_id),
            ChangeOrderPackage,
            ("change_order_packages",),
            params=params,
            extra_params=extra_params,
        )

    def get_change_order_package(
        self,
        company_id: int | None,
        project_id: int,
        change_order_package_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> ChangeOrderPackage:
        """Return one change order package."""
        return self._get_project_resource(
            company_id,
            project_id,
            change_order_package_id,
            "change_order_package_id",
            endpoints.change_order_package(project_id, change_order_package_id),
            ChangeOrderPackage,
            params=params,
            extra_params=extra_params,
        )

    def list_direct_costs(
        self,
        company_id: int | None,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[DirectCost]:
        """Return project direct costs."""
        return self._list_project_resource(
            company_id,
            project_id,
            endpoints.direct_costs(project_id),
            DirectCost,
            ("direct_costs",),
            params=params,
            extra_params=extra_params,
        )

    def get_direct_cost(
        self,
        company_id: int | None,
        project_id: int,
        direct_cost_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> DirectCost:
        """Return one direct cost."""
        return self._get_project_resource(
            company_id,
            project_id,
            direct_cost_id,
            "direct_cost_id",
            endpoints.direct_cost(project_id, direct_cost_id),
            DirectCost,
            params=params,
            extra_params=extra_params,
        )

    def list_budget_views(
        self,
        company_id: int | None,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[BudgetView]:
        """Return project budget views."""
        return self._list_project_resource(
            company_id,
            project_id,
            endpoints.budget_views(project_id),
            BudgetView,
            ("budget_views",),
            params=params,
            extra_params=extra_params,
        )

    def get_budget_view(
        self,
        company_id: int | None,
        project_id: int,
        budget_view_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> BudgetView:
        """Return one budget view."""
        return self._get_project_resource(
            company_id,
            project_id,
            budget_view_id,
            "budget_view_id",
            endpoints.budget_view(project_id, budget_view_id),
            BudgetView,
            params=params,
            extra_params=extra_params,
        )

    def list_budget_detail_columns(
        self,
        company_id: int | None,
        project_id: int,
        budget_view_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[BudgetDetailColumn]:
        """Return columns for one project budget view."""
        self._validate_positive_id(budget_view_id, "budget_view_id")
        return self._list_project_resource(
            company_id,
            project_id,
            endpoints.budget_detail_columns(project_id, budget_view_id),
            BudgetDetailColumn,
            ("budget_detail_columns", "columns"),
            params=params,
            extra_params=extra_params,
        )

    def list_budget_details(
        self,
        company_id: int | None,
        project_id: int,
        budget_view_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[BudgetDetailRow]:
        """Return budget detail rows for one project budget view."""
        self._validate_positive_id(budget_view_id, "budget_view_id")
        return self._list_project_resource(
            company_id,
            project_id,
            endpoints.budget_details(project_id, budget_view_id),
            BudgetDetailRow,
            ("budget_details", "budget_detail_rows", "rows"),
            params=params,
            extra_params=extra_params,
        )

    def list_budget_view_summary_rows(
        self,
        company_id: int | None,
        project_id: int,
        budget_view_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[BudgetSummaryRow]:
        """Return budget summary rows for one project budget view."""
        self._validate_positive_id(budget_view_id, "budget_view_id")
        return self._list_project_resource(
            company_id,
            project_id,
            endpoints.budget_view_summary_rows(project_id, budget_view_id),
            BudgetSummaryRow,
            ("budget_summary_rows", "summary_rows", "rows"),
            params=params,
            extra_params=extra_params,
        )

    def list_cost_codes(
        self,
        company_id: int | None,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[CostCode]:
        """Return company cost codes."""
        resolved_company_id = self._resolve_company_id(company_id)
        response = self._client.get_all(
            endpoints.cost_codes(resolved_company_id),
            params=self._query_params(params=params, extra_params=extra_params),
            headers=self._company_headers(resolved_company_id),
        )
        return self._parse_list(response, CostCode, ("cost_codes",))

    def list_standard_cost_codes(
        self,
        company_id: int | None,
        standard_cost_code_list_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[CostCode]:
        """Return cost codes for one standard cost code list."""
        resolved_company_id = self._resolve_company_id(company_id)
        self._validate_positive_id(
            standard_cost_code_list_id,
            "standard_cost_code_list_id",
        )
        response = self._client.get_all(
            endpoints.standard_cost_codes(
                resolved_company_id,
                standard_cost_code_list_id,
            ),
            params=self._query_params(params=params, extra_params=extra_params),
            headers=self._company_headers(resolved_company_id),
        )
        return self._parse_list(response, CostCode, ("cost_codes",))

    def list_wbs_codes(
        self,
        company_id: int | None,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[WbsCode]:
        """Return project WBS codes."""
        return self._list_project_resource(
            company_id,
            project_id,
            endpoints.wbs_codes(project_id),
            WbsCode,
            ("wbs_codes",),
            params=params,
            extra_params=extra_params,
        )

    def list_commitments(
        self,
        company_id: int | None,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[Commitment]:
        """Return project commitments."""
        return self._list_project_resource(
            company_id,
            project_id,
            endpoints.commitments(project_id),
            Commitment,
            ("commitments", "contracts"),
            params=params,
            extra_params=extra_params,
        )

    def get_commitment(
        self,
        company_id: int | None,
        project_id: int,
        commitment_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> Commitment:
        """Return one commitment."""
        return self._get_project_resource(
            company_id,
            project_id,
            commitment_id,
            "commitment_id",
            endpoints.commitment(project_id, commitment_id),
            Commitment,
            params=params,
            extra_params=extra_params,
        )

    def _list_project_resource(
        self,
        company_id: int | None,
        project_id: int,
        path: str,
        model_type: type[ModelT],
        keys: tuple[str, ...],
        *,
        params: Mapping[str, Any] | None,
        extra_params: Mapping[str, Any],
    ) -> list[ModelT]:
        """Return typed project resources from a read-only collection endpoint."""
        resolved_company_id = self._resolve_company_id(company_id)
        self._validate_positive_id(project_id, "project_id")
        response = self._client.get_all(
            path,
            params=self._query_params(params=params, extra_params=extra_params),
            headers=self._company_headers(resolved_company_id),
        )
        return self._parse_list(response, model_type, keys)

    def _get_project_resource(
        self,
        company_id: int | None,
        project_id: int,
        resource_id: int,
        resource_name: str,
        path: str,
        model_type: type[ModelT],
        *,
        params: Mapping[str, Any] | None,
        extra_params: Mapping[str, Any],
    ) -> ModelT:
        """Return one typed project resource from a read-only endpoint."""
        response = self._get_project_payload(
            company_id,
            project_id,
            path,
            resource_id=resource_id,
            resource_name=resource_name,
            params=params,
            extra_params=extra_params,
        )
        return model_type.model_validate(response)

    def _get_project_payload(
        self,
        company_id: int | None,
        project_id: int,
        path: str,
        *,
        resource_id: int | None = None,
        resource_name: str = "resource_id",
        params: Mapping[str, Any] | None,
        extra_params: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Return one project resource payload."""
        resolved_company_id = self._resolve_company_id(company_id)
        self._validate_positive_id(project_id, "project_id")
        if resource_id is not None:
            self._validate_positive_id(resource_id, resource_name)
        response = self._client.get(
            path,
            params=self._query_params(params=params, extra_params=extra_params),
            headers=self._company_headers(resolved_company_id),
        )
        return self._expect_mapping(response, "financial resource")

    @staticmethod
    def _parse_list(
        payload: object,
        model_type: type[ModelT],
        keys: tuple[str, ...],
    ) -> list[ModelT]:
        """Parse common Procore collection response shapes."""
        if isinstance(payload, list):
            return [
                model_type.model_validate(item) for item in payload if isinstance(item, Mapping)
            ]
        if isinstance(payload, Mapping):
            for key in keys:
                value = payload.get(key)
                if isinstance(value, list):
                    return [
                        model_type.model_validate(item)
                        for item in value
                        if isinstance(item, Mapping)
                    ]
            if all(key in payload for key in ("id",)):
                return [model_type.model_validate(payload)]
        raise ValidationError("Expected Procore response to contain a list of resources.")

    @staticmethod
    def _expect_mapping(payload: object, resource_name: str) -> Mapping[str, Any]:
        """Return a response payload as a mapping or raise a validation error."""
        if not isinstance(payload, Mapping):
            raise ValidationError(f"Expected Procore {resource_name} response to be an object.")
        return payload

    @staticmethod
    def _query_params(
        *,
        params: Mapping[str, Any] | None,
        extra_params: Mapping[str, Any] | None = None,
        **filters: Any,
    ) -> dict[str, Any] | None:
        """Build query parameters from explicit params and keyword filters."""
        return build_query_params(
            params=params,
            extra_params=dict(extra_params or {}),
            **filters,
        )

    @staticmethod
    def _company_headers(company_id: int) -> dict[str, str]:
        """Return the Procore company context header."""
        return {"Procore-Company-Id": str(company_id)}

    @staticmethod
    def _resolve_company_id(company_id: int | None) -> int:
        """Return an explicit or configured company ID."""
        resolved = company_id or get_settings().company_id
        FinancialsService._validate_positive_id(resolved, "company_id")
        return resolved

    @staticmethod
    def _validate_positive_id(value: int | None, name: str) -> None:
        """Validate that an ID value is a positive integer."""
        if value is None or value <= 0:
            raise ValidationError(f"{name} must be a positive integer.")


def list_change_events(
    company_id: int | None,
    project_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[ChangeEvent]:
    """Return project change events."""
    return FinancialsService(client=client).list_change_events(company_id, project_id, **params)


def get_change_event(
    company_id: int | None,
    project_id: int,
    change_event_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> ChangeEvent:
    """Return one project change event."""
    return FinancialsService(client=client).get_change_event(
        company_id,
        project_id,
        change_event_id,
        **params,
    )


def list_change_event_statuses(
    company_id: int | None,
    project_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[ChangeEventStatus]:
    """Return project change event statuses."""
    return FinancialsService(client=client).list_change_event_statuses(
        company_id,
        project_id,
        **params,
    )


def list_change_event_types(
    company_id: int | None,
    project_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[ChangeEventType]:
    """Return project change event types."""
    return FinancialsService(client=client).list_change_event_types(
        company_id,
        project_id,
        **params,
    )


def get_change_event_settings(
    company_id: int | None,
    project_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> ChangeEventSettings:
    """Return project change event settings."""
    return FinancialsService(client=client).get_change_event_settings(
        company_id,
        project_id,
        **params,
    )


def list_prime_change_orders(
    company_id: int | None,
    project_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[PrimeChangeOrder]:
    """Return project prime change orders."""
    return FinancialsService(client=client).list_prime_change_orders(
        company_id,
        project_id,
        **params,
    )


def get_prime_change_order(
    company_id: int | None,
    project_id: int,
    prime_change_order_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> PrimeChangeOrder:
    """Return one prime change order."""
    return FinancialsService(client=client).get_prime_change_order(
        company_id,
        project_id,
        prime_change_order_id,
        **params,
    )


def list_commitment_change_orders(
    company_id: int | None,
    project_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[CommitmentChangeOrder]:
    """Return project commitment change orders."""
    return FinancialsService(client=client).list_commitment_change_orders(
        company_id,
        project_id,
        **params,
    )


def get_commitment_change_order(
    company_id: int | None,
    project_id: int,
    commitment_change_order_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> CommitmentChangeOrder:
    """Return one commitment change order."""
    return FinancialsService(client=client).get_commitment_change_order(
        company_id,
        project_id,
        commitment_change_order_id,
        **params,
    )


def list_change_order_packages(
    company_id: int | None,
    project_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[ChangeOrderPackage]:
    """Return project change order packages."""
    return FinancialsService(client=client).list_change_order_packages(
        company_id,
        project_id,
        **params,
    )


def get_change_order_package(
    company_id: int | None,
    project_id: int,
    change_order_package_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> ChangeOrderPackage:
    """Return one change order package."""
    return FinancialsService(client=client).get_change_order_package(
        company_id,
        project_id,
        change_order_package_id,
        **params,
    )


def list_direct_costs(
    company_id: int | None,
    project_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[DirectCost]:
    """Return project direct costs."""
    return FinancialsService(client=client).list_direct_costs(company_id, project_id, **params)


def get_direct_cost(
    company_id: int | None,
    project_id: int,
    direct_cost_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> DirectCost:
    """Return one direct cost."""
    return FinancialsService(client=client).get_direct_cost(
        company_id,
        project_id,
        direct_cost_id,
        **params,
    )


def list_budget_views(
    company_id: int | None,
    project_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[BudgetView]:
    """Return project budget views."""
    return FinancialsService(client=client).list_budget_views(company_id, project_id, **params)


def get_budget_view(
    company_id: int | None,
    project_id: int,
    budget_view_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> BudgetView:
    """Return one budget view."""
    return FinancialsService(client=client).get_budget_view(
        company_id,
        project_id,
        budget_view_id,
        **params,
    )


def list_budget_detail_columns(
    company_id: int | None,
    project_id: int,
    budget_view_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[BudgetDetailColumn]:
    """Return columns for one budget view."""
    return FinancialsService(client=client).list_budget_detail_columns(
        company_id,
        project_id,
        budget_view_id,
        **params,
    )


def list_budget_details(
    company_id: int | None,
    project_id: int,
    budget_view_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[BudgetDetailRow]:
    """Return budget detail rows for one budget view."""
    return FinancialsService(client=client).list_budget_details(
        company_id,
        project_id,
        budget_view_id,
        **params,
    )


def list_budget_view_summary_rows(
    company_id: int | None,
    project_id: int,
    budget_view_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[BudgetSummaryRow]:
    """Return summary rows for one budget view."""
    return FinancialsService(client=client).list_budget_view_summary_rows(
        company_id,
        project_id,
        budget_view_id,
        **params,
    )


def list_cost_codes(
    company_id: int | None,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[CostCode]:
    """Return company cost codes."""
    return FinancialsService(client=client).list_cost_codes(company_id, **params)


def list_standard_cost_codes(
    company_id: int | None,
    standard_cost_code_list_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[CostCode]:
    """Return standard cost codes."""
    return FinancialsService(client=client).list_standard_cost_codes(
        company_id,
        standard_cost_code_list_id,
        **params,
    )


def list_wbs_codes(
    company_id: int | None,
    project_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[WbsCode]:
    """Return project WBS codes."""
    return FinancialsService(client=client).list_wbs_codes(company_id, project_id, **params)


def list_commitments(
    company_id: int | None,
    project_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> list[Commitment]:
    """Return project commitments."""
    return FinancialsService(client=client).list_commitments(company_id, project_id, **params)


def get_commitment(
    company_id: int | None,
    project_id: int,
    commitment_id: int,
    *,
    client: ProcoreClient | None = None,
    **params: Any,
) -> Commitment:
    """Return one commitment."""
    return FinancialsService(client=client).get_commitment(
        company_id,
        project_id,
        commitment_id,
        **params,
    )
