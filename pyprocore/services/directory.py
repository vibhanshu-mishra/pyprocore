"""Read-only directory services for users, vendors, departments, and locations."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, TypeVar

from pyprocore.core import endpoints
from pyprocore.core.client import ProcoreClient
from pyprocore.core.config import get_settings
from pyprocore.core.exceptions import ValidationError
from pyprocore.models import (
    CompanyUser,
    Department,
    DistributionGroup,
    Location,
    ProcoreModel,
    ProjectUser,
    Vendor,
)
from pyprocore.services.query_params import build_query_params

ModelT = TypeVar("ModelT", bound=ProcoreModel)


class DirectoryService:
    """Service for read-only Procore directory and location resources."""

    def __init__(self, client: ProcoreClient | None = None) -> None:
        """Initialize the service.

        Args:
            client: Optional shared Procore HTTP client.
        """
        self._client = client or ProcoreClient()

    def list_company_users(
        self,
        company_id: int | None,
        *,
        active: bool | None = None,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[CompanyUser]:
        """Return company directory users."""
        resolved_company_id = self._resolve_company_id(company_id)
        response = self._client.get_all(
            endpoints.company_users(resolved_company_id),
            params=self._query_params(params=params, extra_params=extra_params, active=active),
            headers=self._company_headers(resolved_company_id),
        )
        return self._parse_list(response, CompanyUser, ("users", "company_users"))

    def list_company_inactive_users(
        self,
        company_id: int | None,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[CompanyUser]:
        """Return inactive company directory users when Procore supports filtering."""
        return self.list_company_users(
            company_id,
            active=False,
            params=params,
            **extra_params,
        )

    def get_company_user(
        self,
        company_id: int | None,
        user_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> CompanyUser:
        """Return one company user."""
        resolved_company_id = self._resolve_company_id(company_id)
        self._validate_positive_id(user_id, "user_id")
        response = self._client.get(
            endpoints.company_user(resolved_company_id, user_id),
            params=self._query_params(params=params, extra_params=extra_params),
            headers=self._company_headers(resolved_company_id),
        )
        return CompanyUser.model_validate(self._expect_mapping(response, "company user"))

    def list_project_users(
        self,
        company_id: int | None,
        project_id: int,
        *,
        active: bool | None = None,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[ProjectUser]:
        """Return project directory users."""
        resolved_company_id = self._resolve_company_id(company_id)
        self._validate_positive_id(project_id, "project_id")
        response = self._client.get_all(
            endpoints.project_users(project_id),
            params=self._query_params(params=params, extra_params=extra_params, active=active),
            headers=self._company_headers(resolved_company_id),
        )
        return self._parse_list(response, ProjectUser, ("users", "project_users"))

    def get_project_user(
        self,
        company_id: int | None,
        project_id: int,
        user_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> ProjectUser:
        """Return one project user."""
        resolved_company_id = self._resolve_company_id(company_id)
        self._validate_positive_id(project_id, "project_id")
        self._validate_positive_id(user_id, "user_id")
        response = self._client.get(
            endpoints.project_user(project_id, user_id),
            params=self._query_params(params=params, extra_params=extra_params),
            headers=self._company_headers(resolved_company_id),
        )
        return ProjectUser.model_validate(self._expect_mapping(response, "project user"))

    def list_vendors(
        self,
        company_id: int | None,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[Vendor]:
        """Return company vendors using a conservative company query context."""
        resolved_company_id = self._resolve_company_id(company_id)
        response = self._client.get_all(
            endpoints.vendors(resolved_company_id),
            params=self._query_params(
                params=params,
                extra_params=extra_params,
                company_id=resolved_company_id,
            ),
            headers=self._company_headers(resolved_company_id),
        )
        return self._parse_list(response, Vendor, ("vendors", "companies"))

    def list_project_vendors(
        self,
        company_id: int | None,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[Vendor]:
        """Return vendors filtered by project when Procore supports the filter."""
        self._validate_positive_id(project_id, "project_id")
        return self.list_vendors(
            company_id,
            params=params,
            project_id=project_id,
            **extra_params,
        )

    def get_vendor(
        self,
        company_id: int | None,
        vendor_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> Vendor:
        """Return one vendor."""
        resolved_company_id = self._resolve_company_id(company_id)
        self._validate_positive_id(vendor_id, "vendor_id")
        response = self._client.get(
            endpoints.vendor(resolved_company_id, vendor_id),
            params=self._query_params(
                params=params,
                extra_params=extra_params,
                company_id=resolved_company_id,
            ),
            headers=self._company_headers(resolved_company_id),
        )
        return Vendor.model_validate(self._expect_mapping(response, "vendor"))

    def list_departments(
        self,
        company_id: int | None,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[Department]:
        """Return company departments."""
        resolved_company_id = self._resolve_company_id(company_id)
        response = self._client.get_all(
            endpoints.departments(resolved_company_id),
            params=self._query_params(params=params, extra_params=extra_params),
            headers=self._company_headers(resolved_company_id),
        )
        return self._parse_list(response, Department, ("departments",))

    def get_department(
        self,
        company_id: int | None,
        department_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> Department:
        """Return one department."""
        resolved_company_id = self._resolve_company_id(company_id)
        self._validate_positive_id(department_id, "department_id")
        response = self._client.get(
            endpoints.department(resolved_company_id, department_id),
            params=self._query_params(params=params, extra_params=extra_params),
            headers=self._company_headers(resolved_company_id),
        )
        return Department.model_validate(self._expect_mapping(response, "department"))

    def list_project_distribution_groups(
        self,
        company_id: int | None,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[DistributionGroup]:
        """Return project distribution groups."""
        resolved_company_id = self._resolve_company_id(company_id)
        self._validate_positive_id(project_id, "project_id")
        response = self._client.get_all(
            endpoints.project_distribution_groups(project_id),
            params=self._query_params(params=params, extra_params=extra_params),
            headers=self._company_headers(resolved_company_id),
        )
        return self._parse_list(
            response,
            DistributionGroup,
            ("distribution_groups", "groups"),
        )

    def get_project_distribution_group(
        self,
        company_id: int | None,
        project_id: int,
        distribution_group_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> DistributionGroup:
        """Return one project distribution group."""
        resolved_company_id = self._resolve_company_id(company_id)
        self._validate_positive_id(project_id, "project_id")
        self._validate_positive_id(distribution_group_id, "distribution_group_id")
        response = self._client.get(
            endpoints.project_distribution_group(project_id, distribution_group_id),
            params=self._query_params(params=params, extra_params=extra_params),
            headers=self._company_headers(resolved_company_id),
        )
        return DistributionGroup.model_validate(
            self._expect_mapping(response, "distribution group")
        )

    def list_locations(
        self,
        company_id: int | None,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[Location]:
        """Return project locations."""
        resolved_company_id = self._resolve_company_id(company_id)
        self._validate_positive_id(project_id, "project_id")
        response = self._client.get_all(
            endpoints.locations(project_id),
            params=self._query_params(params=params, extra_params=extra_params),
            headers=self._company_headers(resolved_company_id),
        )
        return self._parse_list(response, Location, ("locations",))

    def get_location(
        self,
        company_id: int | None,
        project_id: int,
        location_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> Location:
        """Return one project location."""
        resolved_company_id = self._resolve_company_id(company_id)
        self._validate_positive_id(project_id, "project_id")
        self._validate_positive_id(location_id, "location_id")
        response = self._client.get(
            endpoints.location(project_id, location_id),
            params=self._query_params(params=params, extra_params=extra_params),
            headers=self._company_headers(resolved_company_id),
        )
        return Location.model_validate(self._expect_mapping(response, "location"))

    @staticmethod
    def _query_params(
        *,
        params: Mapping[str, Any] | None = None,
        extra_params: Mapping[str, Any] | None = None,
        **filters: Any,
    ) -> dict[str, Any] | None:
        """Return merged query parameters."""
        return build_query_params(
            params=params,
            extra_params=dict(extra_params or {}),
            **filters,
        )

    @staticmethod
    def _parse_list(
        payload: object,
        model_type: type[ModelT],
        resource_keys: Sequence[str],
    ) -> list[ModelT]:
        """Parse list payloads from common Procore response shapes."""
        return [model_type.model_validate(item) for item in _extract_items(payload, resource_keys)]

    @staticmethod
    def _company_headers(company_id: int) -> dict[str, str]:
        """Return headers needed by company-scoped Procore endpoints."""
        return {"Procore-Company-Id": str(company_id)}

    @staticmethod
    def _resolve_company_id(company_id: int | None) -> int:
        """Return an explicit or configured company ID."""
        resolved = company_id or get_settings().company_id
        DirectoryService._validate_positive_id(resolved, "company_id")
        return resolved

    @staticmethod
    def _validate_positive_id(value: int, name: str) -> None:
        """Validate Procore integer identifiers."""
        if value <= 0:
            raise ValidationError(f"{name} must be a positive integer.")

    @staticmethod
    def _expect_mapping(payload: object, resource_name: str) -> Mapping[str, Any]:
        """Return an object payload or raise a validation error."""
        if not isinstance(payload, Mapping):
            raise ValidationError(f"Expected Procore {resource_name} response to be an object.")
        return payload


def _extract_items(payload: object, resource_keys: Sequence[str]) -> list[Mapping[str, Any]]:
    """Extract resource dictionaries from common Procore response shapes."""
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, Mapping)]
    if isinstance(payload, Mapping):
        for key in (*resource_keys, "items", "data", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, Mapping)]
    return []


def list_company_users(
    company_id: int | None,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> list[CompanyUser]:
    """Return company directory users."""
    return DirectoryService(client=client).list_company_users(company_id, **filters)


def list_company_inactive_users(
    company_id: int | None,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> list[CompanyUser]:
    """Return inactive company directory users."""
    return DirectoryService(client=client).list_company_inactive_users(company_id, **filters)


def get_company_user(
    company_id: int | None,
    user_id: int,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> CompanyUser:
    """Return one company user."""
    return DirectoryService(client=client).get_company_user(company_id, user_id, **filters)


def list_project_users(
    company_id: int | None,
    project_id: int,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> list[ProjectUser]:
    """Return project directory users."""
    return DirectoryService(client=client).list_project_users(company_id, project_id, **filters)


def get_project_user(
    company_id: int | None,
    project_id: int,
    user_id: int,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> ProjectUser:
    """Return one project user."""
    return DirectoryService(client=client).get_project_user(
        company_id,
        project_id,
        user_id,
        **filters,
    )


def list_vendors(
    company_id: int | None,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> list[Vendor]:
    """Return company vendors."""
    return DirectoryService(client=client).list_vendors(company_id, **filters)


def list_project_vendors(
    company_id: int | None,
    project_id: int,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> list[Vendor]:
    """Return project-filtered vendors."""
    return DirectoryService(client=client).list_project_vendors(
        company_id,
        project_id,
        **filters,
    )


def get_vendor(
    company_id: int | None,
    vendor_id: int,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> Vendor:
    """Return one vendor."""
    return DirectoryService(client=client).get_vendor(company_id, vendor_id, **filters)


def list_departments(
    company_id: int | None,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> list[Department]:
    """Return company departments."""
    return DirectoryService(client=client).list_departments(company_id, **filters)


def get_department(
    company_id: int | None,
    department_id: int,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> Department:
    """Return one department."""
    return DirectoryService(client=client).get_department(
        company_id,
        department_id,
        **filters,
    )


def list_project_distribution_groups(
    company_id: int | None,
    project_id: int,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> list[DistributionGroup]:
    """Return project distribution groups."""
    return DirectoryService(client=client).list_project_distribution_groups(
        company_id,
        project_id,
        **filters,
    )


def get_project_distribution_group(
    company_id: int | None,
    project_id: int,
    distribution_group_id: int,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> DistributionGroup:
    """Return one project distribution group."""
    return DirectoryService(client=client).get_project_distribution_group(
        company_id,
        project_id,
        distribution_group_id,
        **filters,
    )


def list_locations(
    company_id: int | None,
    project_id: int,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> list[Location]:
    """Return project locations."""
    return DirectoryService(client=client).list_locations(company_id, project_id, **filters)


def get_location(
    company_id: int | None,
    project_id: int,
    location_id: int,
    client: ProcoreClient | None = None,
    **filters: Any,
) -> Location:
    """Return one project location."""
    return DirectoryService(client=client).get_location(
        company_id,
        project_id,
        location_id,
        **filters,
    )
