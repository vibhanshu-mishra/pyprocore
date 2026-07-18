"""Beginner-friendly async entry point for PyProcore."""

from __future__ import annotations

import builtins
from collections.abc import Mapping, Sequence
from typing import Any, Self, TypeVar

from pyprocore.auth.token_manager import TokenManager
from pyprocore.core import endpoints
from pyprocore.core.async_client import AsyncProcoreClient
from pyprocore.core.async_transport import AsyncTransport
from pyprocore.core.config import ProcoreSettings
from pyprocore.core.exceptions import MultipleResultsError, NotFoundError, ValidationError
from pyprocore.models import (
    RFI,
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
    Company,
    CompanyUser,
    ContractPayment,
    CoordinationIssue,
    CoordinationIssueActivity,
    CoordinationIssueChangeHistoryEvent,
    CoordinationIssueFilterOption,
    Correspondence,
    CostCode,
    CostType,
    DailyLogCount,
    DailyLogEntry,
    DailyLogHeader,
    Department,
    DirectCost,
    DistributionGroup,
    Document,
    Drawing,
    DrawingArea,
    Form,
    FormTemplate,
    GenericTool,
    Incident,
    IncidentConfiguration,
    Inspection,
    Location,
    Meeting,
    Observation,
    OwnerInvoice,
    PhotoAlbum,
    PhotoImage,
    PrimeChangeOrder,
    PrimeContract,
    Project,
    ProjectSchedule,
    ProjectUser,
    PunchItem,
    ScheduleImportStatus,
    ScheduleIntegration,
    ScheduleResourceAssignment,
    ScheduleSettings,
    ScheduleType,
    SpecificationSection,
    SubcontractorInvoice,
    Submittal,
    Task,
    TaskRequestedChange,
    TaxCode,
    Vendor,
    WbsCode,
)
from pyprocore.models.base import ProcoreModel
from pyprocore.services.query_params import build_query_params

_ModelT = TypeVar("_ModelT", bound=ProcoreModel)


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


class AsyncPhotosClient:
    """Async grouped client for photos and photo albums."""

    def __init__(self, owner: "AsyncProcore") -> None:
        """Initialize the grouped client."""
        self._owner = owner

    async def list_albums(
        self,
        company_id: int,
        project_id: int,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[PhotoAlbum]:
        """Return photo albums for a project."""
        return await self._owner.list_photo_albums(
            company_id,
            project_id,
            params=params,
            **extra_params,
        )

    async def get_album(self, company_id: int, project_id: int, album_id: int) -> PhotoAlbum:
        """Return one photo album."""
        return await self._owner.get_photo_album(company_id, project_id, album_id)

    async def list(
        self,
        company_id: int,
        project_id: int,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[PhotoImage]:
        """Return photos for a project."""
        return await self._owner.list_photos(
            company_id,
            project_id,
            params=params,
            **extra_params,
        )

    async def get(self, company_id: int, project_id: int, photo_id: int) -> PhotoImage:
        """Return one photo."""
        return await self._owner.get_photo(company_id, project_id, photo_id)


class AsyncObservationsClient:
    """Async grouped client for observations."""

    def __init__(self, owner: "AsyncProcore") -> None:
        """Initialize the grouped client."""
        self._owner = owner

    async def list(
        self,
        company_id: int,
        project_id: int,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[Observation]:
        """Return observations for a project."""
        return await self._owner.list_observations(
            company_id,
            project_id,
            params=params,
            **extra_params,
        )

    async def get(self, company_id: int, project_id: int, observation_id: int) -> Observation:
        """Return one observation."""
        return await self._owner.get_observation(company_id, project_id, observation_id)

    async def find(self, company_id: int, project_id: int, **criteria: Any) -> Observation:
        """Find one observation by ID, number, title, name, or text."""
        return await self._owner.find_observation(company_id, project_id, **criteria)


class AsyncPunchItemsClient:
    """Async grouped client for punch items."""

    def __init__(self, owner: "AsyncProcore") -> None:
        """Initialize the grouped client."""
        self._owner = owner

    async def list(
        self,
        company_id: int,
        project_id: int,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[PunchItem]:
        """Return punch items for a project."""
        return await self._owner.list_punch_items(
            company_id,
            project_id,
            params=params,
            **extra_params,
        )

    async def get(self, company_id: int, project_id: int, punch_item_id: int) -> PunchItem:
        """Return one punch item."""
        return await self._owner.get_punch_item(company_id, project_id, punch_item_id)

    async def find(self, company_id: int, project_id: int, **criteria: Any) -> PunchItem:
        """Find one punch item by ID, number, title, name, or text."""
        return await self._owner.find_punch_item(company_id, project_id, **criteria)


class AsyncCorrespondenceClient:
    """Async grouped client for Generic Tools and correspondence items."""

    def __init__(self, owner: "AsyncProcore") -> None:
        """Initialize the grouped client."""
        self._owner = owner

    async def list_generic_tools(self, company_id: int, project_id: int) -> list[GenericTool]:
        """Return Generic Tool metadata for a project."""
        return await self._owner.list_generic_tools(company_id, project_id)

    async def get_generic_tool(
        self,
        company_id: int,
        project_id: int,
        generic_tool_id: int,
    ) -> GenericTool:
        """Return one Generic Tool metadata record."""
        return await self._owner.get_generic_tool(company_id, project_id, generic_tool_id)

    async def list(
        self,
        company_id: int,
        project_id: int,
        generic_tool_id: int,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[Correspondence]:
        """Return correspondence items for a Generic Tool."""
        return await self._owner.list_correspondences(
            company_id,
            project_id,
            generic_tool_id,
            params=params,
            **extra_params,
        )

    async def get(
        self,
        company_id: int,
        project_id: int,
        generic_tool_id: int,
        correspondence_id: int,
    ) -> Correspondence:
        """Return one correspondence item."""
        return await self._owner.get_correspondence(
            company_id,
            project_id,
            generic_tool_id,
            correspondence_id,
        )

    async def find(
        self,
        company_id: int,
        project_id: int,
        generic_tool_id: int,
        **criteria: Any,
    ) -> Correspondence:
        """Find one correspondence item by ID, number, title, subject, or text."""
        return await self._owner.find_correspondence(
            company_id,
            project_id,
            generic_tool_id,
            **criteria,
        )


class AsyncOperationsClient:
    """Async grouped client for meetings, inspections, and incidents."""

    def __init__(self, owner: "AsyncProcore") -> None:
        """Initialize the grouped client."""
        self._owner = owner

    async def list_meetings(self, company_id: int, project_id: int) -> list[Meeting]:
        """Return meetings for a project."""
        return await self._owner.list_meetings(company_id, project_id)

    async def list_inspections(self, company_id: int, project_id: int) -> list[Inspection]:
        """Return inspections for a project."""
        return await self._owner.list_inspections(company_id, project_id)

    async def list_incidents(self, company_id: int, project_id: int) -> list[Incident]:
        """Return incidents for a project."""
        return await self._owner.list_incidents(company_id, project_id)

    async def get_incident_configuration(
        self,
        company_id: int,
        project_id: int,
    ) -> IncidentConfiguration:
        """Return incident configuration for a project."""
        return await self._owner.get_project_incident_configuration(company_id, project_id)


class AsyncDirectoryClient:
    """Async grouped client for read-only directory resources."""

    def __init__(self, owner: "AsyncProcore") -> None:
        """Initialize the grouped client."""
        self._owner = owner

    async def list_company_users(self, company_id: int, **filters: Any) -> list[CompanyUser]:
        """Return company directory users."""
        return await self._owner.list_company_users(company_id, **filters)

    async def list_project_users(
        self,
        company_id: int,
        project_id: int,
        **filters: Any,
    ) -> list[ProjectUser]:
        """Return project directory users."""
        return await self._owner.list_project_users(company_id, project_id, **filters)

    async def list_vendors(self, company_id: int, **filters: Any) -> list[Vendor]:
        """Return company vendors."""
        return await self._owner.list_vendors(company_id, **filters)

    async def list_departments(self, company_id: int, **filters: Any) -> list[Department]:
        """Return company departments."""
        return await self._owner.list_departments(company_id, **filters)

    async def list_distribution_groups(
        self,
        company_id: int,
        project_id: int,
        **filters: Any,
    ) -> list[DistributionGroup]:
        """Return project distribution groups."""
        return await self._owner.list_project_distribution_groups(
            company_id,
            project_id,
            **filters,
        )

    async def list_locations(
        self,
        company_id: int,
        project_id: int,
        **filters: Any,
    ) -> list[Location]:
        """Return project locations."""
        return await self._owner.list_locations(company_id, project_id, **filters)


class AsyncFinancialsClient:
    """Async grouped client for read-only financial and change-management resources."""

    def __init__(self, owner: "AsyncProcore") -> None:
        """Initialize the grouped client."""
        self._owner = owner

    async def list_change_events(
        self, company_id: int, project_id: int, **filters: Any
    ) -> list[ChangeEvent]:
        """Return project change events."""
        return await self._owner.list_change_events(company_id, project_id, **filters)

    async def get_change_event(
        self, company_id: int, project_id: int, change_event_id: int
    ) -> ChangeEvent:
        """Return one project change event."""
        return await self._owner.get_change_event(company_id, project_id, change_event_id)

    async def find_change_event(
        self, company_id: int, project_id: int, **criteria: Any
    ) -> ChangeEvent:
        """Find one change event by ID, number, title, name, or text."""
        return await self._owner.find_change_event(company_id, project_id, **criteria)

    async def list_direct_costs(
        self, company_id: int, project_id: int, **filters: Any
    ) -> list[DirectCost]:
        """Return project direct costs."""
        return await self._owner.list_direct_costs(company_id, project_id, **filters)

    async def list_budget_views(
        self, company_id: int, project_id: int, **filters: Any
    ) -> list[BudgetView]:
        """Return project budget views."""
        return await self._owner.list_budget_views(company_id, project_id, **filters)

    async def list_commitments(
        self, company_id: int, project_id: int, **filters: Any
    ) -> list[Commitment]:
        """Return project commitments."""
        return await self._owner.list_commitments(company_id, project_id, **filters)


class AsyncContractsClient:
    """Async grouped client for read-only contracts, invoices, and billing resources."""

    def __init__(self, owner: "AsyncProcore") -> None:
        """Initialize the grouped client."""
        self._owner = owner

    async def list(self, company_id: int, project_id: int, **filters: Any) -> list[PrimeContract]:
        """Return project prime contracts."""
        return await self._owner.list_contracts(company_id, project_id, **filters)

    async def get(self, company_id: int, project_id: int, contract_id: int) -> PrimeContract:
        """Return one prime contract."""
        return await self._owner.get_contract(company_id, project_id, contract_id)

    async def find(self, company_id: int, project_id: int, **criteria: Any) -> PrimeContract:
        """Find one prime contract by ID, number, title, name, or text."""
        return await self._owner.find_contract(company_id, project_id, **criteria)

    async def list_owner_invoices(
        self,
        company_id: int,
        project_id: int,
        prime_contract_id: int,
        **filters: Any,
    ) -> builtins.list[OwnerInvoice]:
        """Return owner invoices for one prime contract."""
        return await self._owner.list_owner_invoices(
            company_id,
            project_id,
            prime_contract_id,
            **filters,
        )

    async def list_subcontractor_invoices(
        self,
        company_id: int,
        project_id: int,
        **filters: Any,
    ) -> builtins.list[SubcontractorInvoice]:
        """Return subcontractor invoices for a project."""
        return await self._owner.list_subcontractor_invoices(company_id, project_id, **filters)


class AsyncProjectManagementClient:
    """Async grouped client for read-only schedule, task, form, and action-plan data."""

    def __init__(self, owner: "AsyncProcore") -> None:
        """Initialize the grouped client."""
        self._owner = owner

    async def get_schedule(self, company_id: int, project_id: int) -> ProjectSchedule:
        """Return read-only project schedule metadata."""
        return await self._owner.get_project_schedule(company_id, project_id)

    async def list_tasks(self, company_id: int, project_id: int, **filters: Any) -> list[Task]:
        """Return project tasks."""
        return await self._owner.list_tasks(company_id, project_id, **filters)

    async def list_calendar_items(
        self,
        company_id: int,
        project_id: int,
        **filters: Any,
    ) -> list[CalendarItem]:
        """Return project calendar items."""
        return await self._owner.list_calendar_items(company_id, project_id, **filters)

    async def list_coordination_issues(
        self,
        company_id: int,
        project_id: int,
        **filters: Any,
    ) -> list[CoordinationIssue]:
        """Return project coordination issues."""
        return await self._owner.list_coordination_issues(company_id, project_id, **filters)

    async def list_forms(self, company_id: int, project_id: int, **filters: Any) -> list[Form]:
        """Return project forms."""
        return await self._owner.list_forms(company_id, project_id, **filters)

    async def list_action_plans(
        self,
        company_id: int,
        project_id: int,
        **filters: Any,
    ) -> list[ActionPlan]:
        """Return project action plans."""
        return await self._owner.list_action_plans(company_id, project_id, **filters)


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
        self.photos = AsyncPhotosClient(self)
        self.observations = AsyncObservationsClient(self)
        self.punch_items = AsyncPunchItemsClient(self)
        self.correspondence = AsyncCorrespondenceClient(self)
        self.operations = AsyncOperationsClient(self)
        self.directory = AsyncDirectoryClient(self)
        self.financials = AsyncFinancialsClient(self)
        self.contracts = AsyncContractsClient(self)
        self.project_management = AsyncProjectManagementClient(self)

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

    async def list_photo_albums(
        self,
        company_id: int,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[PhotoAlbum]:
        """Return photo albums for a Procore project."""
        self._validate_positive_id(company_id, "company_id")
        self._validate_positive_id(project_id, "project_id")
        response = await self._client.get_all(
            endpoints.image_categories(),
            params=build_query_params(
                params=params,
                extra_params=extra_params,
                project_id=project_id,
            ),
            headers=self._company_headers(company_id),
        )
        return [PhotoAlbum.model_validate(item) for item in self._extract_items(response)]

    async def get_photo_album(self, company_id: int, project_id: int, album_id: int) -> PhotoAlbum:
        """Return one photo album for a Procore project."""
        self._validate_positive_id(company_id, "company_id")
        self._validate_positive_id(project_id, "project_id")
        self._validate_positive_id(album_id, "album_id")
        response = await self._client.get(
            endpoints.image_category(album_id),
            params={"project_id": project_id},
            headers=self._company_headers(company_id),
        )
        return PhotoAlbum.model_validate(self._expect_object(response, "photo album"))

    async def list_photos(
        self,
        company_id: int,
        project_id: int,
        *,
        album_id: int | None = None,
        image_category_id: int | None = None,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[PhotoImage]:
        """Return photos/images for a Procore project."""
        self._validate_positive_id(company_id, "company_id")
        self._validate_positive_id(project_id, "project_id")
        self._validate_optional_id(album_id, "album_id")
        self._validate_optional_id(image_category_id, "image_category_id")
        category_id = image_category_id if image_category_id is not None else album_id
        response = await self._client.get_all(
            endpoints.images(),
            params=build_query_params(
                params=params,
                extra_params=extra_params,
                project_id=project_id,
                image_category_id=category_id,
            ),
            headers=self._company_headers(company_id),
        )
        return [PhotoImage.model_validate(item) for item in self._extract_items(response)]

    async def get_photo(self, company_id: int, project_id: int, photo_id: int) -> PhotoImage:
        """Return one photo/image for a Procore project."""
        self._validate_positive_id(company_id, "company_id")
        self._validate_positive_id(project_id, "project_id")
        self._validate_positive_id(photo_id, "photo_id")
        response = await self._client.get(
            endpoints.image(photo_id),
            params={"project_id": project_id},
            headers=self._company_headers(company_id),
        )
        return PhotoImage.model_validate(self._expect_object(response, "photo"))

    async def get_daily_log_counts(
        self,
        company_id: int,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[DailyLogCount]:
        """Return Daily Log count records for a project."""
        response = await self._project_get_all(
            company_id,
            project_id,
            endpoints.daily_log_counts(project_id),
            params=params,
            extra_params=extra_params,
        )
        return [DailyLogCount.model_validate(item) for item in self._extract_items(response)]

    async def list_daily_log_headers(
        self,
        company_id: int,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[DailyLogHeader]:
        """Return Daily Log headers for a project."""
        response = await self._project_get_all(
            company_id,
            project_id,
            endpoints.daily_log_headers(project_id),
            params=params,
            extra_params=extra_params,
        )
        return [DailyLogHeader.model_validate(item) for item in self._extract_items(response)]

    async def list_daily_logs(
        self,
        company_id: int,
        project_id: int,
        log_type: str = "manpower",
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[DailyLogEntry]:
        """Return Daily Log entries for one supported log type."""
        response = await self._project_get_all(
            company_id,
            project_id,
            endpoints.daily_log_type(project_id, log_type),
            params=params,
            extra_params=extra_params,
        )
        entries = [DailyLogEntry.model_validate(item) for item in self._extract_items(response)]
        for entry in entries:
            if entry.log_type is None:
                entry.log_type = log_type
        return entries

    async def list_observations(
        self,
        company_id: int,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[Observation]:
        """Return observations for a Procore project."""
        response = await self._project_get_all(
            company_id,
            project_id,
            endpoints.observations(project_id),
            params=params,
            extra_params=extra_params,
        )
        return [
            Observation.model_validate(item)
            for item in self._extract_items_by_keys(response, ("observations", "items"))
        ]

    async def get_observation(
        self,
        company_id: int,
        project_id: int,
        observation_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> Observation:
        """Return one observation for a Procore project."""
        self._validate_positive_id(observation_id, "observation_id")
        response = await self._project_get(
            company_id,
            project_id,
            endpoints.observation(project_id, observation_id),
            params=params,
            extra_params=extra_params,
        )
        return Observation.model_validate(self._expect_object(response, "observation"))

    async def find_observation(
        self,
        company_id: int,
        project_id: int,
        *,
        observation_id: int | None = None,
        number: str | int | None = None,
        title: str | None = None,
        name: str | None = None,
        query: str | None = None,
    ) -> Observation:
        """Find one observation by ID, number, title, name, or text."""
        records = await self.list_observations(company_id, project_id)
        return self._find_one(
            records,
            "observation",
            resource_id=observation_id,
            criteria={"number": number, "title": title, "name": name},
            query=query,
        )

    async def list_punch_items(
        self,
        company_id: int,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[PunchItem]:
        """Return punch items for a Procore project."""
        response = await self._project_get_all(
            company_id,
            project_id,
            endpoints.punch_items(project_id),
            params=params,
            extra_params=extra_params,
        )
        return [
            PunchItem.model_validate(item)
            for item in self._extract_items_by_keys(response, ("punch_items", "items"))
        ]

    async def get_punch_item(
        self,
        company_id: int,
        project_id: int,
        punch_item_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> PunchItem:
        """Return one punch item for a Procore project."""
        self._validate_positive_id(punch_item_id, "punch_item_id")
        response = await self._project_get(
            company_id,
            project_id,
            endpoints.punch_item(project_id, punch_item_id),
            params=params,
            extra_params=extra_params,
        )
        return PunchItem.model_validate(self._expect_object(response, "punch item"))

    async def find_punch_item(
        self,
        company_id: int,
        project_id: int,
        *,
        punch_item_id: int | None = None,
        number: str | int | None = None,
        title: str | None = None,
        name: str | None = None,
        query: str | None = None,
    ) -> PunchItem:
        """Find one punch item by ID, number, title, name, or text."""
        records = await self.list_punch_items(company_id, project_id)
        return self._find_one(
            records,
            "punch item",
            resource_id=punch_item_id,
            criteria={"number": number, "title": title, "name": name},
            query=query,
        )

    async def list_generic_tools(
        self,
        company_id: int,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[GenericTool]:
        """Return Generic Tools for a Procore project."""
        response = await self._project_get_all(
            company_id,
            project_id,
            endpoints.generic_tools(project_id),
            params=params,
            extra_params=extra_params,
        )
        return [GenericTool.model_validate(item) for item in self._extract_items(response)]

    async def get_generic_tool(
        self,
        company_id: int,
        project_id: int,
        generic_tool_id: int,
    ) -> GenericTool:
        """Return one Generic Tool for a Procore project."""
        self._validate_positive_id(generic_tool_id, "generic_tool_id")
        response = await self._project_get(
            company_id,
            project_id,
            endpoints.generic_tool(project_id, generic_tool_id),
        )
        return GenericTool.model_validate(self._expect_object(response, "generic tool"))

    async def list_correspondences(
        self,
        company_id: int,
        project_id: int,
        generic_tool_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[Correspondence]:
        """Return correspondence items for a Generic Tool."""
        self._validate_positive_id(generic_tool_id, "generic_tool_id")
        response = await self._project_get_all(
            company_id,
            project_id,
            endpoints.generic_tool_items(project_id, generic_tool_id),
            params=params,
            extra_params=extra_params,
        )
        return [
            Correspondence.model_validate(item)
            for item in self._extract_items_by_keys(response, ("generic_tool_items", "items"))
        ]

    async def get_correspondence(
        self,
        company_id: int,
        project_id: int,
        generic_tool_id: int,
        correspondence_id: int,
    ) -> Correspondence:
        """Return one correspondence item for a Generic Tool."""
        self._validate_positive_id(generic_tool_id, "generic_tool_id")
        self._validate_positive_id(correspondence_id, "correspondence_id")
        response = await self._project_get(
            company_id,
            project_id,
            endpoints.generic_tool_item(project_id, correspondence_id),
        )
        return Correspondence.model_validate(self._expect_object(response, "correspondence"))

    async def find_correspondence(
        self,
        company_id: int,
        project_id: int,
        generic_tool_id: int,
        *,
        correspondence_id: int | None = None,
        number: str | int | None = None,
        title: str | None = None,
        subject: str | None = None,
        query: str | None = None,
    ) -> Correspondence:
        """Find one correspondence by ID, number, title, subject, or text."""
        records = await self.list_correspondences(company_id, project_id, generic_tool_id)
        return self._find_one(
            records,
            "correspondence",
            resource_id=correspondence_id,
            criteria={"number": number, "title": title, "subject": subject},
            query=query,
        )

    async def list_meetings(
        self,
        company_id: int,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[Meeting]:
        """Return meetings for a Procore project."""
        response = await self._project_get_all(
            company_id,
            project_id,
            endpoints.meetings(project_id),
            params=params,
            extra_params=extra_params,
        )
        return [
            Meeting.model_validate(item)
            for item in self._extract_items_by_keys(response, ("meetings", "items"))
        ]

    async def get_meeting(self, company_id: int, project_id: int, meeting_id: int) -> Meeting:
        """Return one meeting for a Procore project."""
        self._validate_positive_id(meeting_id, "meeting_id")
        response = await self._project_get(
            company_id,
            project_id,
            endpoints.meeting(project_id, meeting_id),
        )
        return Meeting.model_validate(self._expect_object(response, "meeting"))

    async def find_meeting(
        self,
        company_id: int,
        project_id: int,
        *,
        meeting_id: int | None = None,
        number: str | int | None = None,
        title: str | None = None,
        name: str | None = None,
        query: str | None = None,
    ) -> Meeting:
        """Find one meeting by ID, number, title, name, or text."""
        records = await self.list_meetings(company_id, project_id)
        return self._find_one(
            records,
            "meeting",
            resource_id=meeting_id,
            criteria={"number": number, "title": title, "name": name},
            query=query,
        )

    async def list_inspections(
        self,
        company_id: int,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[Inspection]:
        """Return inspections/checklists for a Procore project."""
        response = await self._project_get_all(
            company_id,
            project_id,
            endpoints.inspections(project_id),
            params=params,
            extra_params=extra_params,
        )
        return [
            Inspection.model_validate(item)
            for item in self._extract_items_by_keys(
                response, ("inspections", "checklists", "items")
            )
        ]

    async def get_inspection(
        self,
        company_id: int,
        project_id: int,
        inspection_id: int,
    ) -> Inspection:
        """Return one inspection/checklist for a Procore project."""
        self._validate_positive_id(inspection_id, "inspection_id")
        response = await self._project_get(
            company_id,
            project_id,
            endpoints.inspection(project_id, inspection_id),
        )
        return Inspection.model_validate(self._expect_object(response, "inspection"))

    async def find_inspection(
        self,
        company_id: int,
        project_id: int,
        *,
        inspection_id: int | None = None,
        number: str | int | None = None,
        title: str | None = None,
        name: str | None = None,
        query: str | None = None,
    ) -> Inspection:
        """Find one inspection by ID, number, title, name, or text."""
        records = await self.list_inspections(company_id, project_id)
        return self._find_one(
            records,
            "inspection",
            resource_id=inspection_id,
            criteria={"number": number, "title": title, "name": name},
            query=query,
        )

    async def list_incidents(
        self,
        company_id: int,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[Incident]:
        """Return incidents for a Procore project."""
        response = await self._project_get_all(
            company_id,
            project_id,
            endpoints.incidents(project_id),
            params=params,
            extra_params=extra_params,
        )
        return [
            Incident.model_validate(item)
            for item in self._extract_items_by_keys(response, ("incidents", "items"))
        ]

    async def get_incident(self, company_id: int, project_id: int, incident_id: int) -> Incident:
        """Return one incident for a Procore project."""
        self._validate_positive_id(incident_id, "incident_id")
        response = await self._project_get(
            company_id,
            project_id,
            endpoints.incident(project_id, incident_id),
        )
        return Incident.model_validate(self._expect_object(response, "incident"))

    async def find_incident(
        self,
        company_id: int,
        project_id: int,
        *,
        incident_id: int | None = None,
        number: str | int | None = None,
        title: str | None = None,
        name: str | None = None,
        query: str | None = None,
    ) -> Incident:
        """Find one incident by ID, number, title, name, or text."""
        records = await self.list_incidents(company_id, project_id)
        return self._find_one(
            records,
            "incident",
            resource_id=incident_id,
            criteria={"number": number, "title": title, "name": name},
            query=query,
        )

    async def get_project_incident_configuration(
        self,
        company_id: int,
        project_id: int,
    ) -> IncidentConfiguration:
        """Return incident configuration for a Procore project."""
        self._validate_positive_id(company_id, "company_id")
        self._validate_positive_id(project_id, "project_id")
        response = await self._client.get(
            endpoints.project_incident_configuration(project_id),
            headers=self._company_headers(company_id),
        )
        return IncidentConfiguration.model_validate(
            self._expect_object(response, "incident configuration")
        )

    async def list_company_users(
        self,
        company_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[CompanyUser]:
        """Return company directory users."""
        self._validate_positive_id(company_id, "company_id")
        response = await self._client.get_all(
            endpoints.company_users(company_id),
            params=build_query_params(params=params, extra_params=extra_params),
            headers=self._company_headers(company_id),
        )
        return [
            CompanyUser.model_validate(item)
            for item in self._extract_items_by_keys(response, ("users", "company_users", "items"))
        ]

    async def get_company_user(self, company_id: int, user_id: int) -> CompanyUser:
        """Return one company directory user."""
        self._validate_positive_id(company_id, "company_id")
        self._validate_positive_id(user_id, "user_id")
        response = await self._client.get(
            endpoints.company_user(company_id, user_id),
            headers=self._company_headers(company_id),
        )
        return CompanyUser.model_validate(self._expect_object(response, "company user"))

    async def find_company_user(
        self,
        company_id: int,
        *,
        name: str | None = None,
        email: str | None = None,
        query: str | None = None,
    ) -> CompanyUser:
        """Find one company user by name, email, or text."""
        records = await self.list_company_users(company_id)
        return self._find_one(
            records,
            "company user",
            criteria={"name": name, "email": email, "email_address": email},
            query=query,
        )

    async def list_project_users(
        self,
        company_id: int,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[ProjectUser]:
        """Return project directory users."""
        response = await self._project_get_all(
            company_id,
            project_id,
            endpoints.project_users(project_id),
            params=params,
            extra_params=extra_params,
        )
        return [
            ProjectUser.model_validate(item)
            for item in self._extract_items_by_keys(response, ("users", "project_users", "items"))
        ]

    async def get_project_user(self, company_id: int, project_id: int, user_id: int) -> ProjectUser:
        """Return one project directory user."""
        self._validate_positive_id(user_id, "user_id")
        response = await self._project_get(
            company_id,
            project_id,
            endpoints.project_user(project_id, user_id),
        )
        return ProjectUser.model_validate(self._expect_object(response, "project user"))

    async def find_project_user(
        self,
        company_id: int,
        project_id: int,
        *,
        name: str | None = None,
        email: str | None = None,
        query: str | None = None,
    ) -> ProjectUser:
        """Find one project user by name, email, or text."""
        records = await self.list_project_users(company_id, project_id)
        return self._find_one(
            records,
            "project user",
            criteria={"name": name, "email": email, "email_address": email},
            query=query,
        )

    async def list_vendors(
        self,
        company_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[Vendor]:
        """Return company vendors."""
        self._validate_positive_id(company_id, "company_id")
        response = await self._client.get_all(
            endpoints.vendors(company_id),
            params=build_query_params(
                params=params, extra_params=extra_params, company_id=company_id
            ),
            headers=self._company_headers(company_id),
        )
        return [Vendor.model_validate(item) for item in self._extract_items(response)]

    async def get_vendor(self, company_id: int, vendor_id: int) -> Vendor:
        """Return one company vendor."""
        self._validate_positive_id(company_id, "company_id")
        self._validate_positive_id(vendor_id, "vendor_id")
        response = await self._client.get(
            endpoints.vendor(company_id, vendor_id),
            params={"company_id": company_id},
            headers=self._company_headers(company_id),
        )
        return Vendor.model_validate(self._expect_object(response, "vendor"))

    async def find_vendor(
        self,
        company_id: int,
        *,
        name: str | None = None,
        number: str | int | None = None,
        query: str | None = None,
    ) -> Vendor:
        """Find one vendor by name, number, or text."""
        records = await self.list_vendors(company_id)
        return self._find_one(
            records,
            "vendor",
            criteria={"name": name, "number": number, "vendor_number": number},
            query=query,
        )

    async def list_departments(
        self,
        company_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[Department]:
        """Return company departments."""
        self._validate_positive_id(company_id, "company_id")
        response = await self._client.get_all(
            endpoints.departments(company_id),
            params=build_query_params(params=params, extra_params=extra_params),
            headers=self._company_headers(company_id),
        )
        return [Department.model_validate(item) for item in self._extract_items(response)]

    async def get_department(self, company_id: int, department_id: int) -> Department:
        """Return one company department."""
        self._validate_positive_id(company_id, "company_id")
        self._validate_positive_id(department_id, "department_id")
        response = await self._client.get(
            endpoints.department(company_id, department_id),
            headers=self._company_headers(company_id),
        )
        return Department.model_validate(self._expect_object(response, "department"))

    async def find_department(
        self,
        company_id: int,
        *,
        name: str | None = None,
        code: str | int | None = None,
        query: str | None = None,
    ) -> Department:
        """Find one department by name, code, or text."""
        records = await self.list_departments(company_id)
        return self._find_one(
            records,
            "department",
            criteria={"name": name, "code": code},
            query=query,
        )

    async def list_project_distribution_groups(
        self,
        company_id: int,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[DistributionGroup]:
        """Return project distribution groups."""
        response = await self._project_get_all(
            company_id,
            project_id,
            endpoints.project_distribution_groups(project_id),
            params=params,
            extra_params=extra_params,
        )
        return [
            DistributionGroup.model_validate(item)
            for item in self._extract_items_by_keys(
                response,
                ("distribution_groups", "items"),
            )
        ]

    async def get_project_distribution_group(
        self,
        company_id: int,
        project_id: int,
        distribution_group_id: int,
    ) -> DistributionGroup:
        """Return one project distribution group."""
        self._validate_positive_id(distribution_group_id, "distribution_group_id")
        response = await self._project_get(
            company_id,
            project_id,
            endpoints.project_distribution_group(project_id, distribution_group_id),
        )
        return DistributionGroup.model_validate(self._expect_object(response, "distribution group"))

    async def find_project_distribution_group(
        self,
        company_id: int,
        project_id: int,
        *,
        name: str | None = None,
        query: str | None = None,
    ) -> DistributionGroup:
        """Find one project distribution group by name or text."""
        records = await self.list_project_distribution_groups(company_id, project_id)
        return self._find_one(
            records,
            "distribution group",
            criteria={"name": name},
            query=query,
        )

    async def list_locations(
        self,
        company_id: int,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[Location]:
        """Return project locations."""
        response = await self._project_get_all(
            company_id,
            project_id,
            endpoints.locations(project_id),
            params=params,
            extra_params=extra_params,
        )
        return [Location.model_validate(item) for item in self._extract_items(response)]

    async def get_location(self, company_id: int, project_id: int, location_id: int) -> Location:
        """Return one project location."""
        self._validate_positive_id(location_id, "location_id")
        response = await self._project_get(
            company_id,
            project_id,
            endpoints.location(project_id, location_id),
        )
        return Location.model_validate(self._expect_object(response, "location"))

    async def find_location(
        self,
        company_id: int,
        project_id: int,
        *,
        name: str | None = None,
        code: str | int | None = None,
        query: str | None = None,
    ) -> Location:
        """Find one project location by name, code, path, or text."""
        records = await self.list_locations(company_id, project_id)
        return self._find_one(
            records,
            "location",
            criteria={"name": name, "full_name": name, "code": code},
            query=query,
        )

    async def list_change_events(
        self,
        company_id: int,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[ChangeEvent]:
        """Return project change events."""
        return await self._list_project_models(
            company_id,
            project_id,
            endpoints.change_events(project_id),
            ChangeEvent,
            ("change_events",),
            params=params,
            extra_params=extra_params,
        )

    async def get_change_event(
        self,
        company_id: int,
        project_id: int,
        change_event_id: int,
    ) -> ChangeEvent:
        """Return one project change event."""
        return await self._get_project_model(
            company_id,
            project_id,
            change_event_id,
            "change_event_id",
            endpoints.change_event(project_id, change_event_id),
            ChangeEvent,
            "change event",
        )

    async def find_change_event(
        self,
        company_id: int,
        project_id: int,
        *,
        change_event_id: int | None = None,
        number: str | int | None = None,
        title: str | None = None,
        name: str | None = None,
        query: str | None = None,
    ) -> ChangeEvent:
        """Find one change event by ID, number, title, name, or text."""
        records = await self.list_change_events(company_id, project_id)
        return self._find_one(
            records,
            "change event",
            resource_id=change_event_id,
            criteria={"number": number, "title": title, "name": name},
            query=query,
        )

    async def list_change_event_statuses(
        self,
        company_id: int,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[ChangeEventStatus]:
        """Return project change event statuses."""
        return await self._list_project_models(
            company_id,
            project_id,
            endpoints.change_event_statuses(project_id),
            ChangeEventStatus,
            ("change_event_statuses", "statuses"),
            params=params,
            extra_params=extra_params,
        )

    async def list_change_event_types(
        self,
        company_id: int,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[ChangeEventType]:
        """Return project change event types."""
        return await self._list_project_models(
            company_id,
            project_id,
            endpoints.change_event_types(project_id),
            ChangeEventType,
            ("change_event_types", "types"),
            params=params,
            extra_params=extra_params,
        )

    async def get_change_event_settings(
        self,
        company_id: int,
        project_id: int,
    ) -> ChangeEventSettings:
        """Return read-only project change event settings."""
        response = await self._project_get(
            company_id,
            project_id,
            endpoints.change_event_settings(project_id),
        )
        return ChangeEventSettings.model_validate(
            self._expect_object(response, "change event settings")
        )

    async def list_prime_change_orders(
        self,
        company_id: int,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[PrimeChangeOrder]:
        """Return project prime change orders."""
        return await self._list_project_models(
            company_id,
            project_id,
            endpoints.prime_change_orders(project_id),
            PrimeChangeOrder,
            ("prime_change_orders",),
            params=params,
            extra_params=extra_params,
        )

    async def get_prime_change_order(
        self,
        company_id: int,
        project_id: int,
        prime_change_order_id: int,
    ) -> PrimeChangeOrder:
        """Return one prime change order."""
        return await self._get_project_model(
            company_id,
            project_id,
            prime_change_order_id,
            "prime_change_order_id",
            endpoints.prime_change_order(project_id, prime_change_order_id),
            PrimeChangeOrder,
            "prime change order",
        )

    async def list_commitment_change_orders(
        self,
        company_id: int,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[CommitmentChangeOrder]:
        """Return project commitment change orders."""
        return await self._list_project_models(
            company_id,
            project_id,
            endpoints.commitment_change_orders(project_id),
            CommitmentChangeOrder,
            ("commitment_change_orders",),
            params=params,
            extra_params=extra_params,
        )

    async def get_commitment_change_order(
        self,
        company_id: int,
        project_id: int,
        commitment_change_order_id: int,
    ) -> CommitmentChangeOrder:
        """Return one commitment change order."""
        return await self._get_project_model(
            company_id,
            project_id,
            commitment_change_order_id,
            "commitment_change_order_id",
            endpoints.commitment_change_order(project_id, commitment_change_order_id),
            CommitmentChangeOrder,
            "commitment change order",
        )

    async def list_change_order_packages(
        self,
        company_id: int,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[ChangeOrderPackage]:
        """Return project change order packages."""
        return await self._list_project_models(
            company_id,
            project_id,
            endpoints.change_order_packages(project_id),
            ChangeOrderPackage,
            ("change_order_packages",),
            params=params,
            extra_params=extra_params,
        )

    async def get_change_order_package(
        self,
        company_id: int,
        project_id: int,
        change_order_package_id: int,
    ) -> ChangeOrderPackage:
        """Return one change order package."""
        return await self._get_project_model(
            company_id,
            project_id,
            change_order_package_id,
            "change_order_package_id",
            endpoints.change_order_package(project_id, change_order_package_id),
            ChangeOrderPackage,
            "change order package",
        )

    async def list_direct_costs(
        self,
        company_id: int,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[DirectCost]:
        """Return project direct costs."""
        return await self._list_project_models(
            company_id,
            project_id,
            endpoints.direct_costs(project_id),
            DirectCost,
            ("direct_costs",),
            params=params,
            extra_params=extra_params,
        )

    async def get_direct_cost(
        self,
        company_id: int,
        project_id: int,
        direct_cost_id: int,
    ) -> DirectCost:
        """Return one direct cost."""
        return await self._get_project_model(
            company_id,
            project_id,
            direct_cost_id,
            "direct_cost_id",
            endpoints.direct_cost(project_id, direct_cost_id),
            DirectCost,
            "direct cost",
        )

    async def list_budget_views(
        self,
        company_id: int,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[BudgetView]:
        """Return project budget views."""
        return await self._list_project_models(
            company_id,
            project_id,
            endpoints.budget_views(project_id),
            BudgetView,
            ("budget_views",),
            params=params,
            extra_params=extra_params,
        )

    async def list_budget_view_columns(
        self,
        company_id: int,
        project_id: int,
        budget_view_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[BudgetDetailColumn]:
        """Return columns for one project budget view."""
        self._validate_positive_id(budget_view_id, "budget_view_id")
        return await self._list_project_models(
            company_id,
            project_id,
            endpoints.budget_detail_columns(project_id, budget_view_id),
            BudgetDetailColumn,
            ("budget_detail_columns", "columns"),
            params=params,
            extra_params=extra_params,
        )

    async def list_budget_details(
        self,
        company_id: int,
        project_id: int,
        budget_view_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[BudgetDetailRow]:
        """Return detail rows for one project budget view."""
        self._validate_positive_id(budget_view_id, "budget_view_id")
        return await self._list_project_models(
            company_id,
            project_id,
            endpoints.budget_details(project_id, budget_view_id),
            BudgetDetailRow,
            ("budget_details", "budget_detail_rows", "rows"),
            params=params,
            extra_params=extra_params,
        )

    async def list_budget_summary_rows(
        self,
        company_id: int,
        project_id: int,
        budget_view_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[BudgetSummaryRow]:
        """Return summary rows for one project budget view."""
        self._validate_positive_id(budget_view_id, "budget_view_id")
        return await self._list_project_models(
            company_id,
            project_id,
            endpoints.budget_view_summary_rows(project_id, budget_view_id),
            BudgetSummaryRow,
            ("budget_summary_rows", "summary_rows", "rows"),
            params=params,
            extra_params=extra_params,
        )

    async def list_cost_codes(
        self,
        company_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[CostCode]:
        """Return company cost codes."""
        return await self._list_company_models(
            company_id,
            endpoints.cost_codes(company_id),
            CostCode,
            ("cost_codes",),
            params=params,
            extra_params=extra_params,
        )

    async def list_standard_cost_codes(
        self,
        company_id: int,
        standard_cost_code_list_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[CostCode]:
        """Return cost codes for one standard cost code list."""
        self._validate_positive_id(standard_cost_code_list_id, "standard_cost_code_list_id")
        return await self._list_company_models(
            company_id,
            endpoints.standard_cost_codes(company_id, standard_cost_code_list_id),
            CostCode,
            ("cost_codes",),
            params=params,
            extra_params=extra_params,
        )

    async def list_wbs_items(
        self,
        company_id: int,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[WbsCode]:
        """Return project WBS codes/items."""
        return await self._list_project_models(
            company_id,
            project_id,
            endpoints.wbs_codes(project_id),
            WbsCode,
            ("wbs_codes", "wbs_items"),
            params=params,
            extra_params=extra_params,
        )

    async def list_commitments(
        self,
        company_id: int,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[Commitment]:
        """Return project commitments."""
        return await self._list_project_models(
            company_id,
            project_id,
            endpoints.commitments(project_id),
            Commitment,
            ("commitments", "contracts"),
            params=params,
            extra_params=extra_params,
        )

    async def get_commitment(
        self,
        company_id: int,
        project_id: int,
        commitment_id: int,
    ) -> Commitment:
        """Return one project commitment."""
        return await self._get_project_model(
            company_id,
            project_id,
            commitment_id,
            "commitment_id",
            endpoints.commitment(project_id, commitment_id),
            Commitment,
            "commitment",
        )

    async def list_contracts(
        self,
        company_id: int,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[PrimeContract]:
        """Return project prime contracts."""
        return await self._list_project_models(
            company_id,
            project_id,
            endpoints.prime_contracts(project_id),
            PrimeContract,
            ("prime_contracts",),
            params=params,
            extra_params=extra_params,
        )

    async def get_contract(
        self, company_id: int, project_id: int, contract_id: int
    ) -> PrimeContract:
        """Return one prime contract."""
        return await self._get_project_model(
            company_id,
            project_id,
            contract_id,
            "contract_id",
            endpoints.prime_contract(project_id, contract_id),
            PrimeContract,
            "contract",
        )

    async def find_contract(
        self,
        company_id: int,
        project_id: int,
        *,
        contract_id: int | None = None,
        number: str | int | None = None,
        title: str | None = None,
        name: str | None = None,
        query: str | None = None,
    ) -> PrimeContract:
        """Find one prime contract by ID, number, title, name, or text."""
        records = await self.list_contracts(company_id, project_id)
        return self._find_one(
            records,
            "contract",
            resource_id=contract_id,
            criteria={"number": number, "title": title, "name": name},
            query=query,
        )

    async def list_owner_invoices(
        self,
        company_id: int,
        project_id: int,
        prime_contract_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[OwnerInvoice]:
        """Return owner invoices/payment applications for one prime contract."""
        self._validate_positive_id(prime_contract_id, "prime_contract_id")
        return await self._list_project_models(
            company_id,
            project_id,
            endpoints.owner_invoices(project_id, prime_contract_id),
            OwnerInvoice,
            ("owner_invoices", "payment_applications", "invoices"),
            params=params,
            extra_params=extra_params,
        )

    async def get_owner_invoice(
        self,
        company_id: int,
        project_id: int,
        prime_contract_id: int,
        invoice_id: int,
    ) -> OwnerInvoice:
        """Return one owner invoice/payment application."""
        self._validate_positive_id(prime_contract_id, "prime_contract_id")
        return await self._get_project_model(
            company_id,
            project_id,
            invoice_id,
            "invoice_id",
            endpoints.owner_invoice(project_id, prime_contract_id, invoice_id),
            OwnerInvoice,
            "owner invoice",
        )

    async def list_subcontractor_invoices(
        self,
        company_id: int,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[SubcontractorInvoice]:
        """Return subcontractor invoices/requisitions for a project."""
        return await self._list_project_models(
            company_id,
            project_id,
            endpoints.subcontractor_invoices(project_id),
            SubcontractorInvoice,
            ("subcontractor_invoices", "requisitions", "invoices"),
            params=params,
            extra_params=extra_params,
        )

    async def get_subcontractor_invoice(
        self,
        company_id: int,
        project_id: int,
        invoice_id: int,
    ) -> SubcontractorInvoice:
        """Return one subcontractor invoice/requisition."""
        return await self._get_project_model(
            company_id,
            project_id,
            invoice_id,
            "invoice_id",
            endpoints.subcontractor_invoice(project_id, invoice_id),
            SubcontractorInvoice,
            "subcontractor invoice",
        )

    async def list_contract_payments(
        self,
        company_id: int,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[ContractPayment]:
        """Return project contract payments."""
        return await self._list_project_models(
            company_id,
            project_id,
            endpoints.contract_payments(project_id),
            ContractPayment,
            ("contract_payments", "payments"),
            params=params,
            extra_params=extra_params,
        )

    async def list_billing_periods(
        self,
        company_id: int,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[BillingPeriod]:
        """Return project billing periods."""
        return await self._list_project_models(
            company_id,
            project_id,
            endpoints.billing_periods(project_id),
            BillingPeriod,
            ("billing_periods",),
            params=params,
            extra_params=extra_params,
        )

    async def list_cost_types(
        self,
        company_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[CostType]:
        """Return company cost types."""
        return await self._list_company_models(
            company_id,
            endpoints.cost_types(company_id),
            CostType,
            ("cost_types",),
            params=params,
            extra_params=extra_params,
        )

    async def list_tax_codes(
        self,
        company_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[TaxCode]:
        """Return company tax codes."""
        return await self._list_company_models(
            company_id,
            endpoints.tax_codes(company_id),
            TaxCode,
            ("tax_codes",),
            params=params,
            extra_params=extra_params,
        )

    async def get_project_schedule(self, company_id: int, project_id: int) -> ProjectSchedule:
        """Return read-only project schedule metadata."""
        response = await self._project_get(
            company_id, project_id, endpoints.project_schedule(project_id)
        )
        return ProjectSchedule.model_validate(self._expect_object(response, "project schedule"))

    async def get_schedule_settings(self, company_id: int, project_id: int) -> ScheduleSettings:
        """Return read-only project schedule settings."""
        response = await self._project_get(
            company_id, project_id, endpoints.schedule_settings(project_id)
        )
        return ScheduleSettings.model_validate(self._expect_object(response, "schedule settings"))

    async def get_schedule_type(self, company_id: int, project_id: int) -> ScheduleType:
        """Return read-only project schedule type metadata."""
        response = await self._project_get(
            company_id, project_id, endpoints.schedule_type(project_id)
        )
        return ScheduleType.model_validate(self._expect_object(response, "schedule type"))

    async def get_schedule_integration(
        self,
        company_id: int,
        project_id: int,
    ) -> ScheduleIntegration:
        """Return read-only project schedule integration metadata."""
        response = await self._project_get(
            company_id,
            project_id,
            endpoints.schedule_integration(project_id),
        )
        return ScheduleIntegration.model_validate(
            self._expect_object(response, "schedule integration")
        )

    async def get_schedule_import_status(
        self,
        company_id: int,
        project_id: int,
    ) -> ScheduleImportStatus:
        """Return read-only status for the latest project schedule import."""
        response = await self._project_get(
            company_id,
            project_id,
            endpoints.schedule_import_status(project_id),
        )
        return ScheduleImportStatus.model_validate(
            self._expect_object(response, "schedule import status")
        )

    async def list_schedule_resource_assignments(
        self,
        company_id: int,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[ScheduleResourceAssignment]:
        """Return project schedule resource assignments."""
        return await self._list_project_models(
            company_id,
            project_id,
            endpoints.schedule_resource_assignments(project_id),
            ScheduleResourceAssignment,
            ("schedule_resource_assignments", "resource_assignments", "assignments"),
            params=params,
            extra_params=extra_params,
        )

    async def list_tasks(
        self,
        company_id: int,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[Task]:
        """Return read-only project tasks."""
        return await self._list_project_models(
            company_id,
            project_id,
            endpoints.tasks(project_id),
            Task,
            ("tasks", "schedule_tasks"),
            params=params,
            extra_params=extra_params,
        )

    async def get_task(self, company_id: int, project_id: int, task_id: int) -> Task:
        """Return one read-only project task."""
        return await self._get_project_model(
            company_id,
            project_id,
            task_id,
            "task_id",
            endpoints.task(project_id, task_id),
            Task,
            "task",
        )

    async def list_task_requested_changes(
        self,
        company_id: int,
        project_id: int,
        task_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[TaskRequestedChange]:
        """Return read-only requested changes for one task."""
        self._validate_positive_id(task_id, "task_id")
        return await self._list_project_models(
            company_id,
            project_id,
            endpoints.task_requested_changes(project_id, task_id),
            TaskRequestedChange,
            ("task_requested_changes", "requested_changes"),
            params=params,
            extra_params=extra_params,
        )

    async def list_calendar_items(
        self,
        company_id: int,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[CalendarItem]:
        """Return read-only project calendar items."""
        return await self._list_project_models(
            company_id,
            project_id,
            endpoints.calendar_items(project_id),
            CalendarItem,
            ("calendar_items",),
            params=params,
            extra_params=extra_params,
        )

    async def get_calendar_item(
        self,
        company_id: int,
        project_id: int,
        calendar_item_id: int,
    ) -> CalendarItem:
        """Return one read-only project calendar item."""
        return await self._get_project_model(
            company_id,
            project_id,
            calendar_item_id,
            "calendar_item_id",
            endpoints.calendar_item(project_id, calendar_item_id),
            CalendarItem,
            "calendar item",
        )

    async def list_coordination_issues(
        self,
        company_id: int,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[CoordinationIssue]:
        """Return read-only project coordination issues."""
        return await self._list_project_models(
            company_id,
            project_id,
            endpoints.coordination_issues(project_id),
            CoordinationIssue,
            ("coordination_issues",),
            params=params,
            extra_params=extra_params,
        )

    async def get_coordination_issue(
        self,
        company_id: int,
        project_id: int,
        coordination_issue_id: int,
    ) -> CoordinationIssue:
        """Return one read-only project coordination issue."""
        return await self._get_project_model(
            company_id,
            project_id,
            coordination_issue_id,
            "coordination_issue_id",
            endpoints.coordination_issue(project_id, coordination_issue_id),
            CoordinationIssue,
            "coordination issue",
        )

    async def list_coordination_issue_change_history(
        self,
        company_id: int,
        project_id: int,
        coordination_issue_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[CoordinationIssueChangeHistoryEvent]:
        """Return read-only change history for one coordination issue."""
        self._validate_positive_id(coordination_issue_id, "coordination_issue_id")
        return await self._list_project_models(
            company_id,
            project_id,
            endpoints.coordination_issue_change_history(project_id, coordination_issue_id),
            CoordinationIssueChangeHistoryEvent,
            ("coordination_issue_change_history", "change_history", "events"),
            params=params,
            extra_params=extra_params,
        )

    async def list_coordination_issue_activity(
        self,
        company_id: int,
        project_id: int,
        coordination_issue_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[CoordinationIssueActivity]:
        """Return read-only activity entries for one coordination issue."""
        self._validate_positive_id(coordination_issue_id, "coordination_issue_id")
        return await self._list_project_models(
            company_id,
            project_id,
            endpoints.coordination_issue_activity_feed(project_id, coordination_issue_id),
            CoordinationIssueActivity,
            ("coordination_issue_activity_feed", "activity_feed", "activities"),
            params=params,
            extra_params=extra_params,
        )

    async def list_coordination_issue_filter_options(
        self,
        company_id: int,
        project_id: int,
        *,
        option_type: str | None = None,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[CoordinationIssueFilterOption]:
        """Return read-only coordination issue filter options."""
        option_params = dict(extra_params)
        if option_type is not None:
            option_params["option_type"] = option_type
        return await self._list_project_models(
            company_id,
            project_id,
            endpoints.coordination_issue_filter_options(project_id),
            CoordinationIssueFilterOption,
            ("coordination_issue_filter_options", "filter_options", "options"),
            params=params,
            extra_params=option_params,
        )

    async def list_forms(
        self,
        company_id: int,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[Form]:
        """Return read-only project forms."""
        return await self._list_project_models(
            company_id,
            project_id,
            endpoints.forms(project_id),
            Form,
            ("forms",),
            params=params,
            extra_params=extra_params,
        )

    async def get_form(self, company_id: int, project_id: int, form_id: int) -> Form:
        """Return one read-only project form."""
        return await self._get_project_model(
            company_id,
            project_id,
            form_id,
            "form_id",
            endpoints.form(project_id, form_id),
            Form,
            "form",
        )

    async def list_form_templates(
        self,
        company_id: int,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[FormTemplate]:
        """Return read-only project form templates."""
        return await self._list_project_models(
            company_id,
            project_id,
            endpoints.form_templates(project_id),
            FormTemplate,
            ("form_templates", "templates"),
            params=params,
            extra_params=extra_params,
        )

    async def list_action_plans(
        self,
        company_id: int,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[ActionPlan]:
        """Return read-only project action plans."""
        return await self._list_project_models(
            company_id,
            project_id,
            endpoints.action_plans(project_id),
            ActionPlan,
            ("action_plans",),
            params=params,
            extra_params=extra_params,
        )

    async def get_action_plan(
        self,
        company_id: int,
        project_id: int,
        action_plan_id: int,
    ) -> ActionPlan:
        """Return one read-only project action plan."""
        return await self._get_project_model(
            company_id,
            project_id,
            action_plan_id,
            "action_plan_id",
            endpoints.action_plan(project_id, action_plan_id),
            ActionPlan,
            "action plan",
        )

    async def list_action_plan_change_history(
        self,
        company_id: int,
        project_id: int,
        action_plan_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[ActionPlanChangeHistoryEvent]:
        """Return read-only change history events for one action plan."""
        self._validate_positive_id(action_plan_id, "action_plan_id")
        return await self._list_project_models(
            company_id,
            project_id,
            endpoints.action_plan_change_history_events(project_id, action_plan_id),
            ActionPlanChangeHistoryEvent,
            ("action_plan_change_history_events", "change_history_events", "events"),
            params=params,
            extra_params=extra_params,
        )

    async def _list_project_models(
        self,
        company_id: int,
        project_id: int,
        endpoint: str,
        model_type: type[_ModelT],
        keys: Sequence[str],
        *,
        params: Mapping[str, Any] | None = None,
        extra_params: Mapping[str, Any] | None = None,
    ) -> list[_ModelT]:
        """Return typed models from a project-scoped read-only collection."""
        response = await self._project_get_all(
            company_id,
            project_id,
            endpoint,
            params=params,
            extra_params=extra_params,
        )
        return [
            model_type.model_validate(item) for item in self._extract_items_by_keys(response, keys)
        ]

    async def _get_project_model(
        self,
        company_id: int,
        project_id: int,
        resource_id: int,
        resource_name: str,
        endpoint: str,
        model_type: type[_ModelT],
        label: str,
    ) -> _ModelT:
        """Return one typed model from a project-scoped read-only endpoint."""
        self._validate_positive_id(resource_id, resource_name)
        response = await self._project_get(company_id, project_id, endpoint)
        return model_type.model_validate(self._expect_object(response, label))

    async def _list_company_models(
        self,
        company_id: int,
        endpoint: str,
        model_type: type[_ModelT],
        keys: Sequence[str],
        *,
        params: Mapping[str, Any] | None = None,
        extra_params: Mapping[str, Any] | None = None,
    ) -> list[_ModelT]:
        """Return typed models from a company-scoped read-only collection."""
        self._validate_positive_id(company_id, "company_id")
        response = await self._client.get_all(
            endpoint,
            params=build_query_params(params=params, extra_params=extra_params or {}),
            headers=self._company_headers(company_id),
        )
        return [
            model_type.model_validate(item) for item in self._extract_items_by_keys(response, keys)
        ]

    async def _project_get_all(
        self,
        company_id: int,
        project_id: int,
        endpoint: str,
        *,
        params: Mapping[str, Any] | None = None,
        extra_params: Mapping[str, Any] | None = None,
    ) -> Any:
        """Run a project-scoped async get_all request."""
        self._validate_positive_id(company_id, "company_id")
        self._validate_positive_id(project_id, "project_id")
        return await self._client.get_all(
            endpoint,
            params=build_query_params(
                params=params,
                extra_params=extra_params or {},
                project_id=project_id,
            ),
            headers=self._company_headers(company_id),
        )

    async def _project_get(
        self,
        company_id: int,
        project_id: int,
        endpoint: str,
        *,
        params: Mapping[str, Any] | None = None,
        extra_params: Mapping[str, Any] | None = None,
    ) -> Any:
        """Run a project-scoped async get request."""
        self._validate_positive_id(company_id, "company_id")
        self._validate_positive_id(project_id, "project_id")
        return await self._client.get(
            endpoint,
            params=build_query_params(
                params=params,
                extra_params=extra_params or {},
                project_id=project_id,
            ),
            headers=self._company_headers(company_id),
        )

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

    @classmethod
    def _extract_items_by_keys(
        cls,
        response: Any,
        keys: Sequence[str],
    ) -> list[Mapping[str, Any]]:
        """Extract records from common Procore wrapper keys."""
        if isinstance(response, Mapping):
            for key in keys:
                value = response.get(key)
                if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                    return [item for item in value if isinstance(item, Mapping)]
        return cls._extract_items(response)

    @classmethod
    def _find_one(
        cls,
        records: Sequence[_ModelT],
        resource_name: str,
        *,
        resource_id: int | None = None,
        criteria: Mapping[str, str | int | None],
        query: str | None = None,
    ) -> _ModelT:
        """Resolve exactly one typed record from local async search results."""
        active_criteria = {key: value for key, value in criteria.items() if value is not None}
        if resource_id is None and not active_criteria and not query:
            raise ValidationError(
                f"Provide an ID, exact field, or query to find a {resource_name}."
            )

        matches: list[_ModelT] = []
        for record in records:
            payload = record.model_dump(mode="json")
            if resource_id is not None and payload.get("id") == resource_id:
                matches.append(record)
                continue
            if active_criteria and cls._matches_exact(payload, active_criteria):
                matches.append(record)
                continue
            if query and cls._matches_query(payload, query):
                matches.append(record)

        if not matches:
            raise NotFoundError(f"No {resource_name} matched the provided search criteria.")
        if len(matches) > 1:
            raise MultipleResultsError(
                f"Multiple {resource_name} records matched the provided search criteria."
            )
        return matches[0]

    @staticmethod
    def _matches_exact(
        payload: Mapping[str, Any],
        criteria: Mapping[str, str | int | None],
    ) -> bool:
        """Return whether any provided field criterion matches case-insensitively."""
        for key, expected in criteria.items():
            if expected is None:
                continue
            value = payload.get(key)
            if value is None:
                continue
            if str(value).casefold() == str(expected).casefold():
                return True
        return False

    @staticmethod
    def _matches_query(payload: Mapping[str, Any], query: str) -> bool:
        """Return whether a query appears in common textual record fields."""
        needle = query.casefold()
        for key in (
            "name",
            "title",
            "subject",
            "description",
            "number",
            "code",
            "full_name",
            "path",
            "email",
            "email_address",
            "legal_name",
            "trade_name",
        ):
            value = payload.get(key)
            if value is not None and needle in str(value).casefold():
                return True
        return False

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
    "AsyncContractsClient",
    "AsyncCorrespondenceClient",
    "AsyncDirectoryClient",
    "AsyncDocumentsClient",
    "AsyncDrawingsClient",
    "AsyncFinancialsClient",
    "AsyncObservationsClient",
    "AsyncOperationsClient",
    "AsyncPhotosClient",
    "AsyncProcore",
    "AsyncProjectManagementClient",
    "AsyncProjectsClient",
    "AsyncPunchItemsClient",
    "AsyncRFIsClient",
    "AsyncSpecificationsClient",
    "AsyncSubmittalsClient",
]
