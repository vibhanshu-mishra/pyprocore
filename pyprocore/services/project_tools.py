"""Read-only Project Tools services for the Procore SDK."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pyprocore.core import endpoints
from pyprocore.core.client import ProcoreClient
from pyprocore.core.config import get_settings
from pyprocore.core.exceptions import DuplicateMatchError, NotFoundError, ValidationError
from pyprocore.models import ProjectTool
from pyprocore.services.query_params import build_query_params


class ProjectToolsService:
    """Service for read-only Procore Project Tools metadata."""

    def __init__(self, client: ProcoreClient | None = None) -> None:
        """Initialize the service.

        Args:
            client: Optional shared Procore HTTP client.
        """
        self._client = client or ProcoreClient()

    def list_project_tools(
        self,
        project_id: int,
        company_id: int | None = None,
        *,
        active: bool | None = None,
        mobile: bool | None = None,
        configurable: bool | None = None,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[ProjectTool]:
        """Return read-only Project Tool metadata for a project.

        Args:
            project_id: Procore project ID.
            company_id: Optional Procore company ID. Defaults to
                ``PROCORE_COMPANY_ID`` for the ``Procore-Company-Id`` header.
            active: Optional active-tool filter when supported by Procore.
            mobile: Optional mobile-tool filter when supported by Procore.
            configurable: Optional configurable-tool filter when supported by Procore.
            params: Optional additional query parameters.
            **extra_params: Additional Procore query parameters.

        Returns:
            A list of typed Project Tool models.
        """
        resolved_company_id = self._resolve_company_id(company_id)
        self._validate_positive_id(project_id, "project_id")
        response = self._client.get_all(
            endpoints.project_tools(project_id),
            params=build_query_params(
                params=params,
                extra_params=extra_params,
                active=active,
                mobile=mobile,
                configurable=configurable,
            ),
            headers=self._company_headers(resolved_company_id),
        )
        return [ProjectTool.model_validate(item) for item in self._extract_items(response)]

    def get_project_tool(
        self,
        project_id: int,
        tool_id: int,
        company_id: int | None = None,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> ProjectTool:
        """Return one Project Tool by direct endpoint or local fallback.

        Args:
            project_id: Procore project ID.
            tool_id: Procore project tool ID.
            company_id: Optional Procore company ID.
            params: Optional additional query parameters.
            **extra_params: Additional Procore query parameters.

        Returns:
            A typed Project Tool model.
        """
        resolved_company_id = self._resolve_company_id(company_id)
        self._validate_positive_id(project_id, "project_id")
        self._validate_positive_id(tool_id, "tool_id")
        response = self._client.get(
            endpoints.project_tool(project_id, tool_id),
            params=build_query_params(params=params, extra_params=extra_params),
            headers=self._company_headers(resolved_company_id),
        )
        if not isinstance(response, Mapping):
            raise ValidationError("Expected Procore project tool response to be an object.")
        return ProjectTool.model_validate(response)

    def find_project_tool(
        self,
        project_id: int,
        name: str,
        company_id: int | None = None,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> ProjectTool:
        """Find one Project Tool by case-insensitive name, title, label, or slug."""
        needle = name.strip().casefold()
        if not needle:
            raise ValidationError("name must not be blank.")
        matches = [
            tool
            for tool in self.list_project_tools(
                project_id,
                company_id=company_id,
                params=params,
                **extra_params,
            )
            if needle
            in {
                str(value).casefold()
                for value in (tool.name, tool.title, tool.label, tool.slug)
                if value
            }
        ]
        if not matches:
            raise NotFoundError(f"No Project Tool matched {name!r}.")
        if len(matches) > 1:
            raise DuplicateMatchError(f"Multiple Project Tools matched {name!r}.")
        return matches[0]

    @staticmethod
    def _extract_items(payload: object) -> list[Mapping[str, Any]]:
        """Extract resource dictionaries from common Procore response shapes."""
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, Mapping)]
        if isinstance(payload, Mapping):
            for key in ("project_tools", "tools", "items", "data", "results"):
                value = payload.get(key)
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, Mapping)]
        return []

    @staticmethod
    def _company_headers(company_id: int) -> dict[str, str]:
        """Return headers needed by company-context Procore endpoints."""
        return {"Procore-Company-Id": str(company_id)}

    @staticmethod
    def _resolve_company_id(company_id: int | None) -> int:
        """Return an explicit or configured company ID."""
        resolved = company_id or get_settings().company_id
        ProjectToolsService._validate_positive_id(resolved, "company_id")
        return resolved

    @staticmethod
    def _validate_positive_id(value: int, name: str) -> None:
        """Validate Procore integer identifiers."""
        if value <= 0:
            raise ValidationError(f"{name} must be a positive integer.")


def list_project_tools(
    project_id: int,
    company_id: int | None = None,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> list[ProjectTool]:
    """Return read-only Project Tool metadata for a project."""
    return ProjectToolsService(client=client).list_project_tools(
        project_id,
        company_id=company_id,
        **filters,
    )


def get_project_tool(
    project_id: int,
    tool_id: int,
    company_id: int | None = None,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> ProjectTool:
    """Return one Project Tool metadata resource."""
    return ProjectToolsService(client=client).get_project_tool(
        project_id,
        tool_id,
        company_id=company_id,
        **filters,
    )


def find_project_tool(
    project_id: int,
    name: str,
    company_id: int | None = None,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> ProjectTool:
    """Find one Project Tool by name, title, label, or slug."""
    return ProjectToolsService(client=client).find_project_tool(
        project_id,
        name,
        company_id=company_id,
        **filters,
    )
