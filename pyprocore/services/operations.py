"""Read-only operations services for meetings, inspections, and incidents."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pyprocore.core import endpoints
from pyprocore.core.client import ProcoreClient
from pyprocore.core.config import get_settings
from pyprocore.core.exceptions import ValidationError
from pyprocore.models import Incident, IncidentConfiguration, Inspection, Meeting
from pyprocore.services.query_params import build_query_params


class OperationsService:
    """Service for read-only construction operations resources."""

    def __init__(self, client: ProcoreClient | None = None) -> None:
        """Initialize the service.

        Args:
            client: Optional shared Procore HTTP client.
        """
        self._client = client or ProcoreClient()

    def list_meetings(
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
    ) -> list[Meeting]:
        """Return meetings for a Procore project."""
        resolved_company_id = self._resolve_company_id(company_id)
        self._validate_positive_id(project_id, "project_id")
        response = self._client.get_all(
            endpoints.meetings(project_id),
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
        return [Meeting.model_validate(item) for item in self._extract_items(response)]

    def get_meeting(
        self,
        company_id: int | None,
        project_id: int,
        meeting_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> Meeting:
        """Return one meeting."""
        response = self._get_project_resource(
            company_id=company_id,
            project_id=project_id,
            resource_id=meeting_id,
            resource_name="meeting_id",
            path=endpoints.meeting(project_id, meeting_id),
            params=params,
            extra_params=extra_params,
        )
        return Meeting.model_validate(response)

    def list_inspections(
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
    ) -> list[Inspection]:
        """Return inspections for a project using Procore checklist resources."""
        resolved_company_id = self._resolve_company_id(company_id)
        self._validate_positive_id(project_id, "project_id")
        response = self._client.get_all(
            endpoints.inspections(project_id),
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
        return [Inspection.model_validate(item) for item in self._extract_items(response)]

    def get_inspection(
        self,
        company_id: int | None,
        project_id: int,
        inspection_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> Inspection:
        """Return one checklist-backed inspection."""
        response = self._get_project_resource(
            company_id=company_id,
            project_id=project_id,
            resource_id=inspection_id,
            resource_name="inspection_id",
            path=endpoints.inspection(project_id, inspection_id),
            params=params,
            extra_params=extra_params,
        )
        return Inspection.model_validate(response)

    def list_incidents(
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
    ) -> list[Incident]:
        """Return incidents for a Procore project."""
        resolved_company_id = self._resolve_company_id(company_id)
        self._validate_positive_id(project_id, "project_id")
        response = self._client.get_all(
            endpoints.incidents(project_id),
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
        return [Incident.model_validate(item) for item in self._extract_items(response)]

    def get_incident(
        self,
        company_id: int | None,
        project_id: int,
        incident_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> Incident:
        """Return one incident."""
        response = self._get_project_resource(
            company_id=company_id,
            project_id=project_id,
            resource_id=incident_id,
            resource_name="incident_id",
            path=endpoints.incident(project_id, incident_id),
            params=params,
            extra_params=extra_params,
        )
        return Incident.model_validate(response)

    def get_project_incident_configuration(
        self,
        company_id: int | None,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> IncidentConfiguration:
        """Return project incident configuration when available."""
        resolved_company_id = self._resolve_company_id(company_id)
        self._validate_positive_id(project_id, "project_id")
        response = self._client.get(
            endpoints.project_incident_configuration(project_id),
            params=self._project_params(project_id, params=params, extra_params=extra_params),
            headers=self._company_headers(resolved_company_id),
        )
        if not isinstance(response, Mapping):
            raise ValidationError(
                "Expected Procore incident configuration response to be an object."
            )
        return IncidentConfiguration.model_validate(response)

    def _get_project_resource(
        self,
        *,
        company_id: int | None,
        project_id: int,
        resource_id: int,
        resource_name: str,
        path: str,
        params: Mapping[str, Any] | None,
        extra_params: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Return one project-scoped resource payload."""
        resolved_company_id = self._resolve_company_id(company_id)
        self._validate_positive_id(project_id, "project_id")
        self._validate_positive_id(resource_id, resource_name)
        response = self._client.get(
            path,
            params=self._project_params(project_id, params=params, extra_params=extra_params),
            headers=self._company_headers(resolved_company_id),
        )
        if not isinstance(response, Mapping):
            raise ValidationError("Expected Procore response to be an object.")
        return response

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
                "meetings",
                "inspections",
                "checklists",
                "incidents",
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
        OperationsService._validate_positive_id(resolved, "company_id")
        return resolved

    @staticmethod
    def _validate_positive_id(value: int, name: str) -> None:
        """Validate Procore integer identifiers."""
        if value <= 0:
            raise ValidationError(f"{name} must be a positive integer.")


def list_meetings(
    company_id: int | None,
    project_id: int,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> list[Meeting]:
    """Return meetings for a Procore project."""
    return OperationsService(client=client).list_meetings(company_id, project_id, **filters)


def get_meeting(
    company_id: int | None,
    project_id: int,
    meeting_id: int,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> Meeting:
    """Return one meeting."""
    return OperationsService(client=client).get_meeting(
        company_id,
        project_id,
        meeting_id,
        **filters,
    )


def list_inspections(
    company_id: int | None,
    project_id: int,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> list[Inspection]:
    """Return checklist-backed inspections for a Procore project."""
    return OperationsService(client=client).list_inspections(company_id, project_id, **filters)


def get_inspection(
    company_id: int | None,
    project_id: int,
    inspection_id: int,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> Inspection:
    """Return one checklist-backed inspection."""
    return OperationsService(client=client).get_inspection(
        company_id,
        project_id,
        inspection_id,
        **filters,
    )


def list_incidents(
    company_id: int | None,
    project_id: int,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> list[Incident]:
    """Return incidents for a Procore project."""
    return OperationsService(client=client).list_incidents(company_id, project_id, **filters)


def get_incident(
    company_id: int | None,
    project_id: int,
    incident_id: int,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> Incident:
    """Return one incident."""
    return OperationsService(client=client).get_incident(
        company_id,
        project_id,
        incident_id,
        **filters,
    )


def get_project_incident_configuration(
    company_id: int | None,
    project_id: int,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> IncidentConfiguration:
    """Return project incident configuration when available."""
    return OperationsService(client=client).get_project_incident_configuration(
        company_id,
        project_id,
        **filters,
    )
