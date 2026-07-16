"""Beginner-friendly async entry point for PyProcore."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Self

from pyprocore.auth.token_manager import TokenManager
from pyprocore.core import endpoints
from pyprocore.core.async_client import AsyncProcoreClient
from pyprocore.core.async_transport import AsyncTransport
from pyprocore.core.config import ProcoreSettings
from pyprocore.core.exceptions import ValidationError
from pyprocore.models import (
    RFI,
    Company,
    Document,
    Drawing,
    DrawingArea,
    Project,
    SpecificationSection,
    Submittal,
)
from pyprocore.services.query_params import build_query_params


class AsyncCompaniesClient:
    """Async grouped client for Procore companies."""

    def __init__(self, owner: "AsyncProcore") -> None:
        """Initialize the grouped client."""
        self._owner = owner

    async def list(self) -> list[Company]:
        """Return companies available to the authenticated user."""
        return await self._owner.list_companies()


class AsyncProjectsClient:
    """Async grouped client for Procore projects."""

    def __init__(self, owner: "AsyncProcore") -> None:
        """Initialize the grouped client."""
        self._owner = owner

    async def list(self, company_id: int) -> list[Project]:
        """Return projects for a company."""
        return await self._owner.list_projects(company_id)


class AsyncRFIsClient:
    """Async grouped client for RFIs."""

    def __init__(self, owner: "AsyncProcore") -> None:
        """Initialize the grouped client."""
        self._owner = owner

    async def list(
        self,
        company_id: int,
        project_id: int,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[RFI]:
        """Return RFIs for a project."""
        return await self._owner.list_rfis(
            company_id,
            project_id,
            params=params,
            **extra_params,
        )

    async def get(self, company_id: int, project_id: int, rfi_id: int) -> RFI:
        """Return one RFI."""
        return await self._owner.get_rfi(company_id, project_id, rfi_id)


class AsyncSubmittalsClient:
    """Async grouped client for submittals."""

    def __init__(self, owner: "AsyncProcore") -> None:
        """Initialize the grouped client."""
        self._owner = owner

    async def list(
        self,
        company_id: int,
        project_id: int,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[Submittal]:
        """Return submittals for a project."""
        return await self._owner.list_submittals(
            company_id,
            project_id,
            params=params,
            **extra_params,
        )

    async def get(self, company_id: int, project_id: int, submittal_id: int) -> Submittal:
        """Return one submittal."""
        return await self._owner.get_submittal(company_id, project_id, submittal_id)


class AsyncDocumentsClient:
    """Async grouped client for documents."""

    def __init__(self, owner: "AsyncProcore") -> None:
        """Initialize the grouped client."""
        self._owner = owner

    async def list(
        self,
        company_id: int,
        project_id: int,
        folder_id: int | None = None,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[Document]:
        """Return documents for a project."""
        return await self._owner.list_documents(
            company_id,
            project_id,
            folder_id=folder_id,
            params=params,
            **extra_params,
        )


class AsyncDrawingsClient:
    """Async grouped client for drawings."""

    def __init__(self, owner: "AsyncProcore") -> None:
        """Initialize the grouped client."""
        self._owner = owner

    async def list_areas(
        self,
        company_id: int,
        project_id: int,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[DrawingArea]:
        """Return drawing areas for a project."""
        return await self._owner.list_drawing_areas(
            company_id,
            project_id,
            params=params,
            **extra_params,
        )

    async def list(
        self,
        company_id: int,
        project_id: int,
        drawing_area_id: int | None = None,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[Drawing]:
        """Return drawings for one area or across all project areas."""
        return await self._owner.list_drawings(
            company_id,
            project_id,
            drawing_area_id=drawing_area_id,
            params=params,
            **extra_params,
        )


class AsyncSpecificationsClient:
    """Async grouped client for specifications."""

    def __init__(self, owner: "AsyncProcore") -> None:
        """Initialize the grouped client."""
        self._owner = owner

    async def list_sections(
        self,
        company_id: int,
        project_id: int,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[SpecificationSection]:
        """Return specification sections for a project."""
        return await self._owner.list_specification_sections(
            company_id,
            project_id,
            params=params,
            **extra_params,
        )


class AsyncProcore:
    """Async object-oriented entry point for read-oriented PyProcore workflows."""

    def __init__(
        self,
        *,
        settings: ProcoreSettings | None = None,
        token_manager: TokenManager | None = None,
        transport: AsyncTransport | None = None,
        client: AsyncProcoreClient | None = None,
        retry_sleep_seconds: float = 1.0,
    ) -> None:
        """Create an async Procore client.

        Args:
            settings: Optional SDK settings.
            token_manager: Optional token manager.
            transport: Optional async transport, commonly ``MockAsyncTransport`` in tests.
            client: Optional prebuilt async HTTP client.
            retry_sleep_seconds: Base retry delay for transient failures.
        """
        self._client = client or AsyncProcoreClient(
            settings=settings,
            token_manager=token_manager,
            transport=transport,
            retry_sleep_seconds=retry_sleep_seconds,
        )
        self.companies = AsyncCompaniesClient(self)
        self.projects = AsyncProjectsClient(self)
        self.rfis = AsyncRFIsClient(self)
        self.submittals = AsyncSubmittalsClient(self)
        self.documents = AsyncDocumentsClient(self)
        self.drawings = AsyncDrawingsClient(self)
        self.specifications = AsyncSpecificationsClient(self)

    async def __aenter__(self) -> Self:
        """Return this async client for context manager use."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: object | None,
    ) -> None:
        """Close transport resources when leaving an async context."""
        await self.close()

    async def close(self) -> None:
        """Close the underlying async HTTP client."""
        await self._client.close()

    async def list_companies(self) -> list[Company]:
        """Return companies available to the authenticated Procore user."""
        response = await self._client.get_all(endpoints.companies())
        return [Company.model_validate(item) for item in self._extract_items(response)]

    async def list_projects(self, company_id: int) -> list[Project]:
        """Return projects for a Procore company."""
        self._validate_positive_id(company_id, "company_id")
        response = await self._client.get_all(endpoints.projects(company_id))
        return [Project.model_validate(item) for item in self._extract_items(response)]

    async def list_rfis(
        self,
        company_id: int,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[RFI]:
        """Return RFIs for a Procore project."""
        self._validate_positive_id(company_id, "company_id")
        self._validate_positive_id(project_id, "project_id")
        response = await self._client.get_all(
            endpoints.rfis(project_id),
            params=build_query_params(params=params, extra_params=extra_params),
            headers=self._company_headers(company_id),
        )
        return [RFI.model_validate(item) for item in self._extract_items(response)]

    async def get_rfi(self, company_id: int, project_id: int, rfi_id: int) -> RFI:
        """Return one RFI for a Procore project."""
        self._validate_positive_id(company_id, "company_id")
        self._validate_positive_id(project_id, "project_id")
        self._validate_positive_id(rfi_id, "rfi_id")
        response = await self._client.get(
            endpoints.rfi(project_id, rfi_id),
            headers=self._company_headers(company_id),
        )
        return RFI.model_validate(self._expect_object(response, "RFI"))

    async def list_submittals(
        self,
        company_id: int,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[Submittal]:
        """Return submittals for a Procore project."""
        self._validate_positive_id(company_id, "company_id")
        self._validate_positive_id(project_id, "project_id")
        response = await self._client.get_all(
            endpoints.submittals(project_id),
            params=build_query_params(params=params, extra_params=extra_params),
            headers=self._company_headers(company_id),
        )
        return [Submittal.model_validate(item) for item in self._extract_items(response)]

    async def get_submittal(
        self,
        company_id: int,
        project_id: int,
        submittal_id: int,
    ) -> Submittal:
        """Return one submittal for a Procore project."""
        self._validate_positive_id(company_id, "company_id")
        self._validate_positive_id(project_id, "project_id")
        self._validate_positive_id(submittal_id, "submittal_id")
        response = await self._client.get(
            endpoints.submittal(project_id, submittal_id),
            headers=self._company_headers(company_id),
        )
        return Submittal.model_validate(self._expect_object(response, "submittal"))

    async def list_documents(
        self,
        company_id: int,
        project_id: int,
        *,
        folder_id: int | None = None,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[Document]:
        """Return documents for a Procore project."""
        self._validate_positive_id(company_id, "company_id")
        self._validate_positive_id(project_id, "project_id")
        self._validate_optional_id(folder_id, "folder_id")
        response = await self._client.get_all(
            endpoints.documents(project_id),
            params=build_query_params(
                params=params,
                extra_params=extra_params,
                project_id=project_id,
                **({"filters[folder_id]": folder_id} if folder_id is not None else {}),
            ),
            headers=self._company_headers(company_id),
        )
        return [Document.model_validate(item) for item in self._extract_nested(response, "files")]

    async def list_drawing_areas(
        self,
        company_id: int,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[DrawingArea]:
        """Return drawing areas for a Procore project."""
        self._validate_positive_id(company_id, "company_id")
        self._validate_positive_id(project_id, "project_id")
        response = await self._client.get_all(
            endpoints.drawing_areas(project_id),
            params=build_query_params(params=params, extra_params=extra_params),
            headers=self._company_headers(company_id),
        )
        return [DrawingArea.model_validate(item) for item in self._extract_items(response)]

    async def list_drawings(
        self,
        company_id: int,
        project_id: int,
        *,
        drawing_area_id: int | None = None,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[Drawing]:
        """Return drawings for one drawing area or across all project drawing areas."""
        self._validate_positive_id(company_id, "company_id")
        self._validate_positive_id(project_id, "project_id")
        self._validate_optional_id(drawing_area_id, "drawing_area_id")
        if drawing_area_id is None:
            drawings: list[Drawing] = []
            for area in await self.list_drawing_areas(company_id, project_id):
                if area.id is not None:
                    drawings.extend(
                        await self.list_drawings(
                            company_id,
                            project_id,
                            drawing_area_id=area.id,
                            params=params,
                            **extra_params,
                        )
                    )
            return drawings

        response = await self._client.get_all(
            endpoints.drawings(project_id, drawing_area_id),
            params=build_query_params(params=params, extra_params=extra_params),
            headers=self._company_headers(company_id),
        )
        return [Drawing.model_validate(item) for item in self._extract_items(response)]

    async def list_specification_sections(
        self,
        company_id: int,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[SpecificationSection]:
        """Return specification sections for a Procore project."""
        self._validate_positive_id(company_id, "company_id")
        self._validate_positive_id(project_id, "project_id")
        response = await self._client.get_all(
            endpoints.specification_sections(company_id, project_id),
            params=build_query_params(params=params, extra_params=extra_params),
            headers=self._company_headers(company_id),
        )
        return [SpecificationSection.model_validate(item) for item in self._extract_items(response)]

    @staticmethod
    def _company_headers(company_id: int) -> dict[str, str]:
        """Return the Procore company header."""
        return {"Procore-Company-Id": str(company_id)}

    @staticmethod
    def _expect_object(response: Any, resource_name: str) -> Mapping[str, Any]:
        """Return a response object or raise a validation error."""
        if not isinstance(response, Mapping):
            raise ValidationError(f"Expected Procore {resource_name} response to be an object.")
        return response

    @staticmethod
    def _extract_items(response: Any) -> list[Mapping[str, Any]]:
        """Extract a list of object-like records from a response."""
        if isinstance(response, Sequence) and not isinstance(response, (str, bytes)):
            return [item for item in response if isinstance(item, Mapping)]
        if isinstance(response, Mapping):
            for key in ("data", "items", "results"):
                value = response.get(key)
                if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                    return [item for item in value if isinstance(item, Mapping)]
            return [response]
        return []

    @classmethod
    def _extract_nested(cls, response: Any, key: str) -> list[Mapping[str, Any]]:
        """Extract nested collection values from paginated or wrapped responses."""
        extracted: list[Mapping[str, Any]] = []
        for item in cls._extract_items(response):
            nested = item.get(key)
            if isinstance(nested, Sequence) and not isinstance(nested, (str, bytes)):
                extracted.extend(value for value in nested if isinstance(value, Mapping))
            elif key in item:
                continue
            else:
                extracted.append(item)
        return extracted

    @staticmethod
    def _validate_positive_id(value: int, name: str) -> None:
        """Validate a required Procore integer identifier."""
        if value <= 0:
            raise ValidationError(f"{name} must be a positive integer.")

    @staticmethod
    def _validate_optional_id(value: int | None, name: str) -> None:
        """Validate an optional Procore integer identifier."""
        if value is not None and value <= 0:
            raise ValidationError(f"{name} must be a positive integer when provided.")


__all__ = [
    "AsyncCompaniesClient",
    "AsyncDocumentsClient",
    "AsyncDrawingsClient",
    "AsyncProcore",
    "AsyncProjectsClient",
    "AsyncRFIsClient",
    "AsyncSpecificationsClient",
    "AsyncSubmittalsClient",
]
