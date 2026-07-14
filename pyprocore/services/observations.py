"""Observation services for the Procore SDK."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pyprocore.core import endpoints
from pyprocore.core.client import ProcoreClient
from pyprocore.core.config import get_settings
from pyprocore.core.exceptions import ValidationError
from pyprocore.models import Observation
from pyprocore.services.query_params import build_query_params


class ObservationsService:
    """Service for read-only Procore observation item resources."""

    def __init__(self, client: ProcoreClient | None = None) -> None:
        """Initialize the service.

        Args:
            client: Optional shared Procore HTTP client.
        """
        self._client = client or ProcoreClient()

    def list_observations(
        self,
        company_id: int | None,
        project_id: int,
        *,
        status: str | None = None,
        updated_after: str | None = None,
        updated_before: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[Observation]:
        """Return observation items for a Procore project.

        Args:
            company_id: Optional Procore company ID. Defaults to
                ``PROCORE_COMPANY_ID`` for the ``Procore-Company-Id`` header.
            project_id: Procore project ID.
            status: Optional observation status filter.
            updated_after: Optional lower bound for updated date filtering.
            updated_before: Optional upper bound for updated date filtering.
            created_after: Optional lower bound for created date filtering.
            created_before: Optional upper bound for created date filtering.
            params: Optional additional query parameters.
            **extra_params: Additional Procore query parameters.

        Returns:
            A list of typed observation models.
        """
        resolved_company_id = self._resolve_company_id(company_id)
        self._validate_positive_id(project_id, "project_id")
        response = self._client.get_all(
            endpoints.observations(project_id),
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
        return [Observation.model_validate(item) for item in self._extract_items(response)]

    def get_observation(
        self,
        company_id: int | None,
        project_id: int,
        observation_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> Observation:
        """Return one observation item."""
        resolved_company_id = self._resolve_company_id(company_id)
        self._validate_positive_id(project_id, "project_id")
        self._validate_positive_id(observation_id, "observation_id")
        response = self._client.get(
            endpoints.observation(project_id, observation_id),
            params=self._project_params(project_id, params=params, extra_params=extra_params),
            headers=self._company_headers(resolved_company_id),
        )
        if not isinstance(response, dict):
            raise ValidationError("Expected Procore observation response to be an object.")
        return Observation.model_validate(response)

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
        """Extract observation dictionaries from common Procore response shapes."""
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, Mapping)]
        if isinstance(payload, Mapping):
            for key in ("observations", "items", "data", "results"):
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
        ObservationsService._validate_positive_id(resolved, "company_id")
        return resolved

    @staticmethod
    def _validate_positive_id(value: int, name: str) -> None:
        """Validate Procore integer identifiers."""
        if value <= 0:
            raise ValidationError(f"{name} must be a positive integer.")


def list_observations(
    company_id: int | None,
    project_id: int,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> list[Observation]:
    """Return observation items for a Procore project."""
    return ObservationsService(client=client).list_observations(
        company_id,
        project_id,
        **filters,
    )


def get_observation(
    company_id: int | None,
    project_id: int,
    observation_id: int,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> Observation:
    """Return one observation item."""
    return ObservationsService(client=client).get_observation(
        company_id,
        project_id,
        observation_id,
        **filters,
    )
