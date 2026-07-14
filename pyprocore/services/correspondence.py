"""Correspondence and Generic Tools services for the Procore SDK."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pyprocore.core import endpoints
from pyprocore.core.client import ProcoreClient
from pyprocore.core.config import get_settings
from pyprocore.core.exceptions import ValidationError
from pyprocore.models import Correspondence, GenericTool
from pyprocore.services.query_params import build_query_params


class CorrespondenceService:
    """Service for read-only Procore Generic Tools and correspondence items."""

    def __init__(self, client: ProcoreClient | None = None) -> None:
        """Initialize the service.

        Args:
            client: Optional shared Procore HTTP client.
        """
        self._client = client or ProcoreClient()

    def list_generic_tools(
        self,
        company_id: int | None,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[GenericTool]:
        """Return Generic Tool metadata for a Procore project.

        Args:
            company_id: Optional Procore company ID. Defaults to
                ``PROCORE_COMPANY_ID`` for the ``Procore-Company-Id`` header.
            project_id: Procore project ID.
            params: Optional additional query parameters.
            **extra_params: Additional Procore query parameters.

        Returns:
            A list of typed Generic Tool models.
        """
        resolved_company_id = self._resolve_company_id(company_id)
        self._validate_positive_id(project_id, "project_id")
        response = self._client.get_all(
            endpoints.generic_tools(project_id),
            params=self._project_params(project_id, params=params, extra_params=extra_params),
            headers=self._company_headers(resolved_company_id),
        )
        return [GenericTool.model_validate(item) for item in self._extract_items(response)]

    def get_generic_tool(
        self,
        company_id: int | None,
        project_id: int,
        generic_tool_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> GenericTool:
        """Return one Generic Tool metadata resource."""
        resolved_company_id = self._resolve_company_id(company_id)
        self._validate_positive_id(project_id, "project_id")
        self._validate_positive_id(generic_tool_id, "generic_tool_id")
        response = self._client.get(
            endpoints.generic_tool(project_id, generic_tool_id),
            params=self._project_params(project_id, params=params, extra_params=extra_params),
            headers=self._company_headers(resolved_company_id),
        )
        if not isinstance(response, dict):
            raise ValidationError("Expected Procore generic tool response to be an object.")
        return GenericTool.model_validate(response)

    def list_correspondences(
        self,
        company_id: int | None,
        project_id: int,
        generic_tool_id: int,
        *,
        status: str | None = None,
        updated_after: str | None = None,
        updated_before: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[Correspondence]:
        """Return correspondence items for a Generic Tool.

        Args:
            company_id: Optional Procore company ID. Defaults to
                ``PROCORE_COMPANY_ID`` for the ``Procore-Company-Id`` header.
            project_id: Procore project ID.
            generic_tool_id: Procore Generic Tool ID.
            status: Optional status filter.
            updated_after: Optional lower bound for updated date filtering.
            updated_before: Optional upper bound for updated date filtering.
            created_after: Optional lower bound for created date filtering.
            created_before: Optional upper bound for created date filtering.
            params: Optional additional query parameters.
            **extra_params: Additional Procore query parameters.

        Returns:
            A list of typed correspondence models.
        """
        resolved_company_id = self._resolve_company_id(company_id)
        self._validate_positive_id(project_id, "project_id")
        self._validate_positive_id(generic_tool_id, "generic_tool_id")
        response = self._client.get_all(
            endpoints.generic_tool_items(project_id, generic_tool_id),
            params=self._project_params(
                project_id,
                params=params,
                extra_params=extra_params,
                status=status,
                updated_after=updated_after,
                updated_before=updated_before,
                created_after=created_after,
                created_before=created_before,
            ),
            headers=self._company_headers(resolved_company_id),
        )
        return [Correspondence.model_validate(item) for item in self._extract_items(response)]

    def get_correspondence(
        self,
        company_id: int | None,
        project_id: int,
        correspondence_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> Correspondence:
        """Return one Generic Tool item or correspondence resource."""
        resolved_company_id = self._resolve_company_id(company_id)
        self._validate_positive_id(project_id, "project_id")
        self._validate_positive_id(correspondence_id, "correspondence_id")
        response = self._client.get(
            endpoints.generic_tool_item(project_id, correspondence_id),
            params=self._project_params(project_id, params=params, extra_params=extra_params),
            headers=self._company_headers(resolved_company_id),
        )
        if not isinstance(response, dict):
            raise ValidationError("Expected Procore correspondence response to be an object.")
        return Correspondence.model_validate(response)

    @staticmethod
    def _project_params(
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        extra_params: Mapping[str, Any] | None = None,
        **filters: Any,
    ) -> dict[str, Any]:
        """Return query parameters with the required project context."""
        merged = (
            build_query_params(
                params=params,
                extra_params=dict(extra_params or {}),
                **filters,
            )
            or {}
        )
        merged["project_id"] = project_id
        return merged

    @staticmethod
    def _extract_items(payload: object) -> list[Mapping[str, Any]]:
        """Extract resource dictionaries from common Procore response shapes."""
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, Mapping)]
        if isinstance(payload, Mapping):
            for key in (
                "generic_tools",
                "generic_tool_items",
                "correspondences",
                "items",
                "data",
                "results",
            ):
                value = payload.get(key)
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, Mapping)]
        return []

    @staticmethod
    def _company_headers(company_id: int) -> dict[str, str]:
        """Return headers needed by company-scoped Procore endpoints."""
        return {"Procore-Company-Id": str(company_id)}

    @staticmethod
    def _resolve_company_id(company_id: int | None) -> int:
        """Return an explicit or configured company ID."""
        resolved = company_id or get_settings().company_id
        CorrespondenceService._validate_positive_id(resolved, "company_id")
        return resolved

    @staticmethod
    def _validate_positive_id(value: int, name: str) -> None:
        """Validate Procore integer identifiers."""
        if value <= 0:
            raise ValidationError(f"{name} must be a positive integer.")


def list_generic_tools(
    company_id: int | None,
    project_id: int,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> list[GenericTool]:
    """Return Generic Tool metadata for a Procore project."""
    return CorrespondenceService(client=client).list_generic_tools(
        company_id,
        project_id,
        **filters,
    )


def get_generic_tool(
    company_id: int | None,
    project_id: int,
    generic_tool_id: int,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> GenericTool:
    """Return one Generic Tool metadata resource."""
    return CorrespondenceService(client=client).get_generic_tool(
        company_id,
        project_id,
        generic_tool_id,
        **filters,
    )


def list_correspondences(
    company_id: int | None,
    project_id: int,
    generic_tool_id: int,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> list[Correspondence]:
    """Return correspondence items for a Procore Generic Tool."""
    return CorrespondenceService(client=client).list_correspondences(
        company_id,
        project_id,
        generic_tool_id,
        **filters,
    )


def get_correspondence(
    company_id: int | None,
    project_id: int,
    correspondence_id: int,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> Correspondence:
    """Return one Generic Tool item or correspondence resource."""
    return CorrespondenceService(client=client).get_correspondence(
        company_id,
        project_id,
        correspondence_id,
        **filters,
    )
