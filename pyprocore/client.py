"""Object-oriented client interface for PyProcore services."""

from __future__ import annotations

import builtins
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Literal

from pyprocore.automation import (
    AutomationInput,
    WorkflowPackage,
    build_rfi_package,
    build_submittal_package,
    build_workflow_package,
)
from pyprocore.core.config import get_settings
from pyprocore.core.exceptions import ValidationError
from pyprocore.models import (
    RFI,
    BillingPeriod,
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
    CommitmentContract,
    Company,
    CompanyUser,
    ContractPayment,
    Correspondence,
    CostCode,
    CostType,
    DailyLogCount,
    DailyLogEntry,
    DailyLogHeader,
    DailyLogsByType,
    DelayLogType,
    Department,
    DirectCost,
    DistributionGroup,
    Document,
    DocumentFolder,
    Drawing,
    DrawingArea,
    DrawingDiscipline,
    GenericTool,
    Incident,
    IncidentConfiguration,
    Inspection,
    Location,
    Meeting,
    Observation,
    OwnerInvoice,
    OwnerInvoiceLineItem,
    PhotoAlbum,
    PhotoAlbumDownloadResult,
    PhotoImage,
    PrimeChangeOrder,
    PrimeContract,
    PrimeContractLineItem,
    PrimeContractSummary,
    Project,
    ProjectUser,
    PunchItem,
    PurchaseOrderContract,
    RequisitionChangeOrderItem,
    RequisitionContractDetailItem,
    RequisitionContractItem,
    SpecificationSection,
    SpecificationSectionRevision,
    SpecificationSet,
    SubcontractorInvoice,
    Submittal,
    TaxCode,
    Vendor,
    WbsCode,
    WorkOrderContract,
)
from pyprocore.services import (
    download_document,
    download_drawing,
    download_photo,
    download_photo_album,
    download_rfi_attachments,
    download_specification_section_revision,
    download_submittal_attachments,
    find_change_event,
    find_commitment,
    find_commitment_contract,
    find_company,
    find_company_user,
    find_contract_payment,
    find_correspondence,
    find_department,
    find_direct_cost,
    find_document,
    find_document_folder,
    find_drawing,
    find_drawings_contains,
    find_incident,
    find_inspection,
    find_location,
    find_meeting,
    find_observation,
    find_owner_invoice,
    find_photo,
    find_photo_album,
    find_prime_change_order,
    find_prime_contract,
    find_project,
    find_project_contains,
    find_project_distribution_group,
    find_project_user,
    find_punch_item,
    find_purchase_order_contract,
    find_rfi,
    find_specification_section,
    find_subcontractor_invoice,
    find_submittal,
    find_vendor,
    find_work_order_contract,
    get_billing_period,
    get_budget_view,
    get_change_event,
    get_change_event_settings,
    get_change_order_package,
    get_commitment,
    get_commitment_change_order,
    get_commitment_contract,
    get_company_user,
    get_contract_payment,
    get_correspondence,
    get_daily_log,
    get_daily_log_counts,
    get_daily_log_header,
    get_department,
    get_direct_cost,
    get_document,
    get_document_folder,
    get_drawing,
    get_drawing_area,
    get_generic_tool,
    get_incident,
    get_inspection,
    get_location,
    get_meeting,
    get_observation,
    get_owner_invoice,
    get_photo,
    get_photo_album,
    get_prime_change_order,
    get_prime_contract,
    get_prime_contract_summary,
    get_project,
    get_project_distribution_group,
    get_project_incident_configuration,
    get_project_user,
    get_punch_item,
    get_purchase_order_contract,
    get_rfi,
    get_specification_section,
    get_specification_section_revision,
    get_subcontractor_invoice,
    get_submittal,
    get_vendor,
    get_work_order_contract,
    list_accident_logs,
    list_billing_periods,
    list_budget_detail_columns,
    list_budget_details,
    list_budget_view_summary_rows,
    list_budget_views,
    list_call_logs,
    list_change_event_statuses,
    list_change_event_types,
    list_change_events,
    list_change_order_packages,
    list_commitment_change_orders,
    list_commitment_contracts,
    list_commitments,
    list_companies,
    list_company_inactive_users,
    list_company_users,
    list_contract_payments,
    list_correspondences,
    list_cost_codes,
    list_cost_types,
    list_daily_construction_report_logs,
    list_daily_log_headers,
    list_daily_logs,
    list_daily_logs_for_date,
    list_delay_log_types,
    list_delay_logs,
    list_delivery_logs,
    list_departments,
    list_direct_costs,
    list_document_folders,
    list_documents,
    list_drawing_areas,
    list_drawing_disciplines,
    list_drawings,
    list_dumpster_logs,
    list_generic_tools,
    list_incidents,
    list_inspections,
    list_locations,
    list_manpower_logs,
    list_meetings,
    list_notes_logs,
    list_observations,
    list_owner_invoice_line_items,
    list_owner_invoices,
    list_photo_albums,
    list_photos,
    list_plan_revision_logs,
    list_prime_change_orders,
    list_prime_contract_line_items,
    list_prime_contracts,
    list_productivity_logs,
    list_project_distribution_groups,
    list_project_users,
    list_project_vendors,
    list_projects,
    list_punch_items,
    list_purchase_order_contracts,
    list_requisition_change_order_items,
    list_requisition_contract_detail_items,
    list_requisition_contract_items,
    list_rfis,
    list_specification_section_revisions,
    list_specification_sections,
    list_specification_sets,
    list_standard_cost_codes,
    list_subcontractor_invoices,
    list_submittals,
    list_tax_codes,
    list_vendors,
    list_visitor_logs,
    list_wbs_codes,
    list_work_order_contracts,
)
from pyprocore.workflows import (  # noqa: F401
    AIExportResult,
    EnhancedRFIPackageResult,
    EnhancedSubmittalPackageResult,
    ProjectContextResult,
    ProjectSyncResult,
    SyncResult,
    WorkflowPlan,
    WorkflowRunResult,
    build_ai_prompt_pack,
    build_ai_review_export,
    build_enhanced_rfi_package,
    build_enhanced_submittal_package,
    build_project_context_package,
    export_billing_periods_to_csv,
    export_budget_details_to_csv,
    export_budget_summary_rows_to_csv,
    export_budget_views_to_csv,
    export_change_events_to_csv,
    export_change_events_to_jsonl,
    export_change_order_packages_to_csv,
    export_commitment_change_orders_to_csv,
    export_commitment_contracts_to_csv,
    export_commitments_to_csv,
    export_company_users_to_csv,
    export_company_users_to_jsonl,
    export_contract_payments_to_csv,
    export_correspondences_to_csv,
    export_correspondences_to_jsonl,
    export_cost_codes_to_csv,
    export_cost_types_to_csv,
    export_departments_to_csv,
    export_departments_to_jsonl,
    export_direct_costs_to_csv,
    export_direct_costs_to_jsonl,
    export_distribution_groups_to_csv,
    export_distribution_groups_to_jsonl,
    export_incidents_to_csv,
    export_incidents_to_jsonl,
    export_inspections_to_csv,
    export_inspections_to_jsonl,
    export_locations_to_csv,
    export_locations_to_jsonl,
    export_meetings_to_csv,
    export_meetings_to_jsonl,
    export_observations_to_csv,
    export_observations_to_jsonl,
    export_owner_invoices_to_csv,
    export_prime_change_orders_to_csv,
    export_prime_change_orders_to_jsonl,
    export_prime_contracts_to_csv,
    export_project_users_to_csv,
    export_project_users_to_jsonl,
    export_punch_items_to_csv,
    export_punch_items_to_jsonl,
    export_purchase_order_contracts_to_csv,
    export_rfis_to_csv,
    export_rfis_to_jsonl,
    export_subcontractor_invoices_to_csv,
    export_submittals_to_csv,
    export_submittals_to_jsonl,
    export_tax_codes_to_csv,
    export_vendors_to_csv,
    export_vendors_to_jsonl,
    export_work_order_contracts_to_csv,
    list_available_workflows,
    load_workflow_plan,
    run_workflow_plan,
    sync_documents_to_folder,
    sync_project_to_folder,
    sync_rfis_to_folder,
    sync_submittals_to_folder,
    validate_workflow_plan,
)


class CompaniesClient:
    """Convenience methods for Procore company resources."""

    def list(self) -> list[Company]:
        """List companies available to the authenticated Procore user.

        Returns:
            A list of typed company models.
        """
        return list_companies()

    def find(self, name: str) -> Company:
        """Find one company by name or name fragment.

        Args:
            name: Company name or partial name.

        Returns:
            The matching typed company model.
        """
        return find_company(name)


class ProjectsClient:
    """Convenience methods for Procore project resources."""

    def list(self, company_id: int | None = None) -> list[Project]:
        """List projects for a Procore company.

        Args:
            company_id: Optional Procore company ID. Defaults to
                ``PROCORE_COMPANY_ID``.

        Returns:
            A list of typed project models.
        """
        resolved_company_id = company_id or get_settings().company_id
        return list_projects(company_id=resolved_company_id)

    def get(self, project_id: int) -> Project:
        """Get one project from the configured company.

        Args:
            project_id: Procore project ID.

        Returns:
            The matching typed project model.
        """
        return get_project(project_id=project_id)

    def find(
        self,
        name: str | None = None,
        *,
        number: str | int | None = None,
        company_id: int | None = None,
    ) -> Project:
        """Find one project by name or project number.

        Args:
            name: Project name or name fragment.
            number: Project number.
            company_id: Optional company ID. Defaults to ``PROCORE_COMPANY_ID``.

        Returns:
            The matching typed project model.
        """
        return find_project(name=name, number=number, company_id=company_id)

    def find_contains(self, text: str, *, company_id: int | None = None) -> Project:
        """Find one project whose name or number contains text.

        Args:
            text: Text to search for in project names or numbers.
            company_id: Optional company ID. Defaults to ``PROCORE_COMPANY_ID``.

        Returns:
            The matching typed project model.
        """
        return find_project_contains(text, company_id=company_id)


class RFIsClient:
    """Convenience methods for Procore RFI resources."""

    def list(
        self,
        project_id: int,
        *,
        status: str | None = None,
        updated_after: str | None = None,
        updated_before: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[RFI]:
        """List RFIs for a Procore project.

        Args:
            project_id: Procore project ID.
            status: Optional RFI status filter.
            updated_after: Optional lower bound for updated date filtering.
            updated_before: Optional upper bound for updated date filtering.
            created_after: Optional lower bound for created date filtering.
            created_before: Optional upper bound for created date filtering.
            params: Optional additional query parameters.
            **extra_params: Additional query parameters passed to Procore.

        Returns:
            A list of typed RFI models.
        """
        return list_rfis(
            project_id=project_id,
            status=status,
            updated_after=updated_after,
            updated_before=updated_before,
            created_after=created_after,
            created_before=created_before,
            params=params,
            **extra_params,
        )

    def get(self, project_id: int, rfi_id: int) -> RFI:
        """Get one RFI by project ID and RFI ID.

        Args:
            project_id: Procore project ID.
            rfi_id: Procore RFI ID.

        Returns:
            The matching typed RFI model.
        """
        return get_rfi(project_id=project_id, rfi_id=rfi_id)

    def find(self, project_id: int, *, number: str | int) -> RFI:
        """Find one RFI by number within a project.

        Args:
            project_id: Procore project ID.
            number: RFI number.

        Returns:
            The matching typed RFI model.
        """
        return find_rfi(project_id=project_id, number=number)

    def download_attachments(
        self,
        project_id: int,
        rfi_id: int,
        output_dir: Path | str | None = None,
        *,
        overwrite: bool = False,
    ) -> builtins.list[Path]:
        """Download all attachments from one RFI.

        Args:
            project_id: Procore project ID.
            rfi_id: Procore RFI ID.
            output_dir: Optional local directory for downloaded files.
            overwrite: Whether to overwrite existing files.

        Returns:
            Paths to downloaded files.
        """
        return download_rfi_attachments(
            project_id=project_id,
            rfi_id=rfi_id,
            destination_dir=output_dir,
            overwrite=overwrite,
        )


class SubmittalsClient:
    """Convenience methods for Procore submittal resources."""

    def list(
        self,
        project_id: int,
        *,
        status: str | None = None,
        updated_after: str | None = None,
        updated_before: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        params: Mapping[str, Any] | None = None,
        **extra_params: Any,
    ) -> list[Submittal]:
        """List submittals for a Procore project.

        Args:
            project_id: Procore project ID.
            status: Optional submittal status filter.
            updated_after: Optional lower bound for updated date filtering.
            updated_before: Optional upper bound for updated date filtering.
            created_after: Optional lower bound for created date filtering.
            created_before: Optional upper bound for created date filtering.
            params: Optional additional query parameters.
            **extra_params: Additional query parameters passed to Procore.

        Returns:
            A list of typed submittal models.
        """
        return list_submittals(
            project_id=project_id,
            status=status,
            updated_after=updated_after,
            updated_before=updated_before,
            created_after=created_after,
            created_before=created_before,
            params=params,
            **extra_params,
        )

    def get(self, project_id: int, submittal_id: int) -> Submittal:
        """Get one submittal by project ID and submittal ID.

        Args:
            project_id: Procore project ID.
            submittal_id: Procore submittal ID.

        Returns:
            The matching typed submittal model.
        """
        return get_submittal(project_id=project_id, submittal_id=submittal_id)

    def find(self, project_id: int, *, number: str | int) -> Submittal:
        """Find one submittal by number within a project.

        Args:
            project_id: Procore project ID.
            number: Submittal number.

        Returns:
            The matching typed submittal model.
        """
        return find_submittal(project_id=project_id, number=number)

    def download_attachments(
        self,
        project_id: int,
        submittal_id: int,
        output_dir: Path | str | None = None,
        *,
        overwrite: bool = False,
    ) -> builtins.list[Path]:
        """Download all attachments from one submittal.

        Args:
            project_id: Procore project ID.
            submittal_id: Procore submittal ID.
            output_dir: Optional local directory for downloaded files.
            overwrite: Whether to overwrite existing files.

        Returns:
            Paths to downloaded files.
        """
        return download_submittal_attachments(
            project_id=project_id,
            submittal_id=submittal_id,
            destination_dir=output_dir,
            overwrite=overwrite,
        )


class ObservationsClient:
    """Convenience methods for Procore observation item resources."""

    def list(
        self,
        company_id: int | None,
        project_id: int,
        *,
        status: str | None = None,
        params: Mapping[str, Any] | None = None,
        **filters: Any,
    ) -> list[Observation]:
        """List observation items for a Procore project."""
        return list_observations(
            company_id,
            project_id,
            status=status,
            params=params,
            **filters,
        )

    def get(self, company_id: int | None, project_id: int, observation_id: int) -> Observation:
        """Get one observation item."""
        return get_observation(company_id, project_id, observation_id)

    def find(
        self,
        company_id: int | None,
        project_id: int,
        *,
        number: str | int | None = None,
        title: str | None = None,
        query: str | None = None,
    ) -> Observation:
        """Find one observation item by number, title, or text."""
        return find_observation(
            company_id,
            project_id,
            number=number,
            title=title,
            query=query,
        )


class PunchItemsClient:
    """Convenience methods for Procore punch item resources."""

    def list(
        self,
        company_id: int | None,
        project_id: int,
        *,
        status: str | None = None,
        params: Mapping[str, Any] | None = None,
        **filters: Any,
    ) -> list[PunchItem]:
        """List punch items for a Procore project."""
        return list_punch_items(
            company_id,
            project_id,
            status=status,
            params=params,
            **filters,
        )

    def get(self, company_id: int | None, project_id: int, punch_item_id: int) -> PunchItem:
        """Get one punch item."""
        return get_punch_item(company_id, project_id, punch_item_id)

    def find(
        self,
        company_id: int | None,
        project_id: int,
        *,
        number: str | int | None = None,
        title: str | None = None,
        query: str | None = None,
    ) -> PunchItem:
        """Find one punch item by number, title, or text."""
        return find_punch_item(
            company_id,
            project_id,
            number=number,
            title=title,
            query=query,
        )


class CorrespondenceClient:
    """Convenience methods for Procore Generic Tools and correspondence items."""

    def list_generic_tools(
        self,
        company_id: int | None,
        project_id: int,
        *,
        params: Mapping[str, Any] | None = None,
        **filters: Any,
    ) -> list[GenericTool]:
        """List Generic Tool metadata for a Procore project."""
        return list_generic_tools(company_id, project_id, params=params, **filters)

    def get_generic_tool(
        self,
        company_id: int | None,
        project_id: int,
        generic_tool_id: int,
    ) -> GenericTool:
        """Get one Generic Tool metadata resource."""
        return get_generic_tool(company_id, project_id, generic_tool_id)

    def list(
        self,
        company_id: int | None,
        project_id: int,
        generic_tool_id: int,
        *,
        status: str | None = None,
        params: Mapping[str, Any] | None = None,
        **filters: Any,
    ) -> list[Correspondence]:
        """List correspondence items for one Generic Tool."""
        return list_correspondences(
            company_id,
            project_id,
            generic_tool_id,
            status=status,
            params=params,
            **filters,
        )

    def get(
        self,
        company_id: int | None,
        project_id: int,
        correspondence_id: int,
    ) -> Correspondence:
        """Get one correspondence item."""
        return get_correspondence(company_id, project_id, correspondence_id)

    def find(
        self,
        company_id: int | None,
        project_id: int,
        generic_tool_id: int,
        *,
        number: str | int | None = None,
        title: str | None = None,
        query: str | None = None,
    ) -> Correspondence:
        """Find one correspondence item by number, title, subject, or text."""
        return find_correspondence(
            company_id,
            project_id,
            generic_tool_id,
            number=number,
            title=title,
            query=query,
        )


class MeetingsClient:
    """Convenience methods for Procore meeting resources."""

    def list(
        self,
        company_id: int | None,
        project_id: int,
        *,
        status: str | None = None,
        params: Mapping[str, Any] | None = None,
        **filters: Any,
    ) -> list[Meeting]:
        """List meetings for a Procore project."""
        return list_meetings(company_id, project_id, status=status, params=params, **filters)

    def get(self, company_id: int | None, project_id: int, meeting_id: int) -> Meeting:
        """Get one meeting."""
        return get_meeting(company_id, project_id, meeting_id)

    def find(
        self,
        company_id: int | None,
        project_id: int,
        *,
        number: str | int | None = None,
        title: str | None = None,
        query: str | None = None,
    ) -> Meeting:
        """Find one meeting by number, title, or text."""
        return find_meeting(
            company_id,
            project_id,
            number=number,
            title=title,
            query=query,
        )


class InspectionsClient:
    """Convenience methods for checklist-backed Procore inspection resources."""

    def list(
        self,
        company_id: int | None,
        project_id: int,
        *,
        status: str | None = None,
        params: Mapping[str, Any] | None = None,
        **filters: Any,
    ) -> list[Inspection]:
        """List inspections for a Procore project."""
        return list_inspections(company_id, project_id, status=status, params=params, **filters)

    def get(self, company_id: int | None, project_id: int, inspection_id: int) -> Inspection:
        """Get one inspection."""
        return get_inspection(company_id, project_id, inspection_id)

    def find(
        self,
        company_id: int | None,
        project_id: int,
        *,
        number: str | int | None = None,
        title: str | None = None,
        query: str | None = None,
    ) -> Inspection:
        """Find one inspection by number, title, or text."""
        return find_inspection(
            company_id,
            project_id,
            number=number,
            title=title,
            query=query,
        )


class IncidentsClient:
    """Convenience methods for Procore incident resources."""

    def list(
        self,
        company_id: int | None,
        project_id: int,
        *,
        status: str | None = None,
        params: Mapping[str, Any] | None = None,
        **filters: Any,
    ) -> list[Incident]:
        """List incidents for a Procore project."""
        return list_incidents(company_id, project_id, status=status, params=params, **filters)

    def get(self, company_id: int | None, project_id: int, incident_id: int) -> Incident:
        """Get one incident."""
        return get_incident(company_id, project_id, incident_id)

    def configuration(
        self,
        company_id: int | None,
        project_id: int,
    ) -> IncidentConfiguration:
        """Get project incident configuration."""
        return get_project_incident_configuration(company_id, project_id)

    def find(
        self,
        company_id: int | None,
        project_id: int,
        *,
        number: str | int | None = None,
        title: str | None = None,
        query: str | None = None,
    ) -> Incident:
        """Find one incident by number, title, or text."""
        return find_incident(
            company_id,
            project_id,
            number=number,
            title=title,
            query=query,
        )


class DocumentsClient:
    """Convenience methods for Procore document resources."""

    def list_folders(
        self,
        project_id: int,
        parent_id: int | None = None,
        *,
        params: Mapping[str, Any] | None = None,
        company_id: int | None = None,
        **filters: Any,
    ) -> list[DocumentFolder]:
        """List document folders for a Procore project.

        Args:
            project_id: Procore project ID.
            parent_id: Optional parent folder ID filter.
            params: Optional additional query parameters.
            company_id: Optional company ID sent as ``Procore-Company-Id``.
            **filters: Additional query parameters passed to Procore.

        Returns:
            A list of typed document folder models.
        """
        return list_document_folders(
            project_id=project_id,
            parent_id=parent_id,
            params=params,
            company_id=company_id,
            **filters,
        )

    def get_folder(
        self,
        project_id: int,
        folder_id: int,
        *,
        company_id: int | None = None,
    ) -> DocumentFolder:
        """Get one document folder.

        Args:
            project_id: Procore project ID.
            folder_id: Procore document folder ID.
            company_id: Optional company ID sent as ``Procore-Company-Id``.

        Returns:
            The matching typed document folder model.
        """
        return get_document_folder(
            project_id=project_id,
            folder_id=folder_id,
            company_id=company_id,
        )

    def find_folder(self, project_id: int, name: str) -> DocumentFolder:
        """Find one document folder by name.

        Args:
            project_id: Procore project ID.
            name: Folder name or name fragment.

        Returns:
            The matching typed document folder model.
        """
        return find_document_folder(project_id=project_id, name=name)

    def list(
        self,
        project_id: int,
        folder_id: int | None = None,
        *,
        params: Mapping[str, Any] | None = None,
        recursive: bool = False,
        company_id: int | None = None,
        **filters: Any,
    ) -> list[Document]:
        """List documents for a Procore project.

        Args:
            project_id: Procore project ID.
            folder_id: Optional document folder ID filter.
            params: Optional additional query parameters.
            recursive: Whether to traverse discovered child folders.
            company_id: Optional company ID sent as ``Procore-Company-Id``.
            **filters: Additional query parameters passed to Procore.

        Returns:
            A list of typed document models.
        """
        return list_documents(
            project_id=project_id,
            folder_id=folder_id,
            params=params,
            recursive=recursive,
            company_id=company_id,
            **filters,
        )

    def get(
        self,
        project_id: int,
        document_id: int,
        *,
        company_id: int | None = None,
    ) -> Document:
        """Get one document.

        Args:
            project_id: Procore project ID.
            document_id: Procore document ID.
            company_id: Optional company ID sent as ``Procore-Company-Id``.

        Returns:
            The matching typed document model.
        """
        return get_document(
            project_id=project_id,
            document_id=document_id,
            company_id=company_id,
        )

    def find(
        self,
        project_id: int,
        *,
        name: str | None = None,
        filename: str | None = None,
    ) -> Document:
        """Find one document by name or filename.

        Args:
            project_id: Procore project ID.
            name: Document name or name fragment.
            filename: Document filename or filename fragment.

        Returns:
            The matching typed document model.
        """
        return find_document(project_id=project_id, name=name, filename=filename)

    def download(
        self,
        project_id: int,
        document_id: int,
        output_dir: Path | str = "downloads/documents",
        filename: str | None = None,
        *,
        company_id: int | None = None,
        overwrite: bool = False,
    ) -> Path:
        """Download one document.

        Args:
            project_id: Procore project ID.
            document_id: Procore document ID.
            output_dir: Local folder where the document should be saved.
            filename: Optional local filename.
            company_id: Optional company ID sent as ``Procore-Company-Id``.
            overwrite: Whether to overwrite an existing file.

        Returns:
            The saved document path.
        """
        return download_document(
            project_id=project_id,
            document_id=document_id,
            output_dir=output_dir,
            filename=filename,
            company_id=company_id,
            overwrite=overwrite,
        )


class DrawingsClient:
    """Convenience methods for Procore drawing resources."""

    def list_areas(
        self,
        project_id: int,
        company_id: int | None = None,
        **filters: Any,
    ) -> list[DrawingArea]:
        """List drawing areas for a Procore project.

        Args:
            project_id: Procore project ID.
            company_id: Optional company ID sent as ``Procore-Company-Id``.
            **filters: Additional query parameters passed to Procore.

        Returns:
            A list of typed drawing area models.
        """
        return list_drawing_areas(project_id, company_id=company_id, **filters)

    def get_area(
        self,
        project_id: int,
        drawing_area_id: int,
        company_id: int | None = None,
    ) -> DrawingArea:
        """Get one drawing area.

        Args:
            project_id: Procore project ID.
            drawing_area_id: Procore drawing area ID.
            company_id: Optional company ID sent as ``Procore-Company-Id``.

        Returns:
            The matching typed drawing area model.
        """
        return get_drawing_area(project_id, drawing_area_id, company_id=company_id)

    def list_disciplines(
        self,
        project_id: int,
        company_id: int | None = None,
        **filters: Any,
    ) -> list[DrawingDiscipline]:
        """List drawing disciplines for a Procore project.

        Args:
            project_id: Procore project ID.
            company_id: Optional company ID sent as ``Procore-Company-Id``.
            **filters: Additional query parameters passed to Procore.

        Returns:
            A list of typed drawing discipline models.
        """
        return list_drawing_disciplines(project_id, company_id=company_id, **filters)

    def list(
        self,
        project_id: int,
        company_id: int | None = None,
        drawing_area_id: int | None = None,
        discipline_id: int | None = None,
        current: bool | None = None,
        **filters: Any,
    ) -> builtins.list[Drawing]:
        """List drawings for a Procore project.

        Args:
            project_id: Procore project ID.
            company_id: Optional company ID sent as ``Procore-Company-Id``.
            drawing_area_id: Optional drawing area filter.
            discipline_id: Optional drawing discipline filter.
            current: Optional filter for current drawing revisions.
            **filters: Additional query parameters passed to Procore.

        Returns:
            A list of typed drawing models.
        """
        return list_drawings(
            project_id,
            company_id=company_id,
            drawing_area_id=drawing_area_id,
            discipline_id=discipline_id,
            current=current,
            **filters,
        )

    def get(
        self,
        project_id: int,
        drawing_id: int,
        company_id: int | None = None,
        drawing_area_id: int | None = None,
    ) -> Drawing:
        """Get one drawing.

        Args:
            project_id: Procore project ID.
            drawing_id: Procore drawing ID.
            company_id: Optional company ID sent as ``Procore-Company-Id``.
            drawing_area_id: Optional drawing area ID. When omitted, the
                service searches drawing areas to locate the drawing.

        Returns:
            The matching typed drawing model.
        """
        return get_drawing(
            project_id,
            drawing_id,
            company_id=company_id,
            drawing_area_id=drawing_area_id,
        )

    def find(
        self,
        project_id: int,
        *,
        number: str | int | None = None,
        title: str | None = None,
        company_id: int | None = None,
    ) -> Drawing:
        """Find one drawing by number or title.

        Args:
            project_id: Procore project ID.
            number: Drawing number or number fragment.
            title: Drawing title or title fragment.
            company_id: Optional company ID sent as ``Procore-Company-Id``.

        Returns:
            The matching typed drawing model.
        """
        return find_drawing(project_id, number=number, title=title, company_id=company_id)

    def find_contains(
        self,
        project_id: int,
        text: str,
        company_id: int | None = None,
    ) -> builtins.list[Drawing]:
        """Find drawings whose number or title contains text.

        Args:
            project_id: Procore project ID.
            text: Search text.
            company_id: Optional company ID sent as ``Procore-Company-Id``.

        Returns:
            Matching typed drawing models.
        """
        return find_drawings_contains(project_id, text, company_id=company_id)

    def download(
        self,
        project_id: int,
        drawing_id: int,
        output_dir: Path | str = "downloads/drawings",
        filename: str | None = None,
        *,
        overwrite: bool = False,
        company_id: int | None = None,
        drawing_area_id: int | None = None,
    ) -> Path:
        """Download one drawing.

        Args:
            project_id: Procore project ID.
            drawing_id: Procore drawing ID.
            output_dir: Local folder where the drawing should be saved.
            filename: Optional local filename.
            overwrite: Whether to overwrite an existing file.
            company_id: Optional company ID sent as ``Procore-Company-Id``.
            drawing_area_id: Optional drawing area ID. When omitted, the
                service searches drawing areas to locate the drawing.

        Returns:
            The saved drawing path.
        """
        return download_drawing(
            project_id,
            drawing_id,
            output_dir=output_dir,
            filename=filename,
            overwrite=overwrite,
            company_id=company_id,
            drawing_area_id=drawing_area_id,
        )


class SpecificationsClient:
    """Convenience methods for Procore specification resources."""

    def list_sets(
        self,
        project_id: int,
        company_id: int | None = None,
        **filters: Any,
    ) -> list[SpecificationSet]:
        """List specification sets for a Procore project."""
        return list_specification_sets(project_id, company_id=company_id, **filters)

    def list_sections(
        self,
        project_id: int,
        company_id: int | None = None,
        specification_area_id: int | None = None,
        specification_set_id: int | None = None,
        division_id: int | None = None,
        sort: str | None = None,
        **filters: Any,
    ) -> list[SpecificationSection]:
        """List specification sections for a Procore project."""
        return list_specification_sections(
            project_id,
            company_id=company_id,
            specification_area_id=specification_area_id,
            specification_set_id=specification_set_id,
            division_id=division_id,
            sort=sort,
            **filters,
        )

    def get_section(
        self,
        project_id: int,
        specification_section_id: int,
        company_id: int | None = None,
    ) -> SpecificationSection:
        """Get one specification section."""
        return get_specification_section(
            project_id,
            specification_section_id,
            company_id=company_id,
        )

    def find_section(
        self,
        project_id: int,
        *,
        number: str | int | None = None,
        title: str | None = None,
        query: str | None = None,
        company_id: int | None = None,
    ) -> SpecificationSection:
        """Find one specification section by number, title, or search text."""
        return find_specification_section(
            project_id,
            number=number,
            title=title,
            query=query,
            company_id=company_id,
        )

    def list_revisions(
        self,
        project_id: int,
        company_id: int | None = None,
        specification_section_id: int | None = None,
        page: int | None = None,
        per_page: int | None = None,
        **filters: Any,
    ) -> list[SpecificationSectionRevision]:
        """List specification section revisions for a Procore project."""
        return list_specification_section_revisions(
            project_id,
            company_id=company_id,
            specification_section_id=specification_section_id,
            page=page,
            per_page=per_page,
            **filters,
        )

    def get_revision(
        self,
        project_id: int,
        revision_id: int,
        company_id: int | None = None,
    ) -> SpecificationSectionRevision:
        """Get one specification section revision."""
        return get_specification_section_revision(
            project_id,
            revision_id,
            company_id=company_id,
        )

    def download_revision(
        self,
        project_id: int,
        revision_id: int,
        output_dir: Path | str = "downloads/specifications",
        *,
        company_id: int | None = None,
        overwrite: bool = False,
    ) -> Path:
        """Download one specification section revision."""
        return download_specification_section_revision(
            project_id,
            revision_id,
            output_dir=output_dir,
            company_id=company_id,
            overwrite=overwrite,
        )


class PhotosClient:
    """Convenience methods for Procore photo resources."""

    def list_albums(
        self,
        project_id: int,
        company_id: int | None = None,
        **filters: Any,
    ) -> list[PhotoAlbum]:
        """List photo albums for a Procore project."""
        return list_photo_albums(project_id, company_id=company_id, **filters)

    def get_album(
        self,
        project_id: int,
        album_id: int,
        company_id: int | None = None,
    ) -> PhotoAlbum:
        """Get one photo album."""
        return get_photo_album(project_id, album_id, company_id=company_id)

    def find_album(
        self,
        project_id: int,
        name: str | None = None,
        company_id: int | None = None,
    ) -> PhotoAlbum:
        """Find one photo album by name."""
        return find_photo_album(project_id, name=name, company_id=company_id)

    def list(
        self,
        project_id: int,
        company_id: int | None = None,
        album_id: int | None = None,
        **filters: Any,
    ) -> list[PhotoImage]:
        """List photos for a Procore project or album."""
        return list_photos(project_id, company_id=company_id, album_id=album_id, **filters)

    def get(
        self,
        project_id: int,
        photo_id: int,
        company_id: int | None = None,
    ) -> PhotoImage:
        """Get one photo."""
        return get_photo(project_id, photo_id, company_id=company_id)

    def find(
        self,
        project_id: int,
        photo_id: int | None = None,
        filename: str | None = None,
        description: str | None = None,
        query: str | None = None,
        company_id: int | None = None,
    ) -> PhotoImage:
        """Find one photo."""
        return find_photo(
            project_id,
            photo_id=photo_id,
            filename=filename,
            description=description,
            query=query,
            company_id=company_id,
        )

    def download(
        self,
        project_id: int,
        photo_id: int,
        output_dir: Path | str = "downloads/photos",
        company_id: int | None = None,
        *,
        overwrite: bool = False,
        filename: str | None = None,
    ) -> Path:
        """Download one photo."""
        return download_photo(
            project_id,
            photo_id,
            output_dir=output_dir,
            company_id=company_id,
            overwrite=overwrite,
            filename=filename,
        )

    def download_album(
        self,
        project_id: int,
        album_id: int,
        output_dir: Path | str = "downloads/photos",
        company_id: int | None = None,
        *,
        overwrite: bool = False,
        limit: int | None = None,
    ) -> PhotoAlbumDownloadResult:
        """Download photos from one album."""
        return download_photo_album(
            project_id,
            album_id,
            output_dir=output_dir,
            company_id=company_id,
            overwrite=overwrite,
            limit=limit,
        )


class DailyLogsClient:
    """Convenience methods for Procore Daily Logs resources."""

    def counts(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[DailyLogCount]:
        """Return Daily Log counts."""
        return get_daily_log_counts(project_id, company_id=company_id, **filters)

    def headers(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[DailyLogHeader]:
        """Return Daily Log headers."""
        return list_daily_log_headers(project_id, company_id=company_id, **filters)

    def get_header(
        self,
        project_id: int,
        header_id: int | None = None,
        log_date: str | None = None,
        company_id: int | None = None,
    ) -> DailyLogHeader:
        """Return one Daily Log header."""
        return get_daily_log_header(
            project_id, header_id=header_id, log_date=log_date, company_id=company_id
        )

    def list(
        self, project_id: int, log_type: str, company_id: int | None = None, **filters: Any
    ) -> builtins.list[DailyLogEntry]:
        """Return Daily Log entries for a supported log type."""
        return list_daily_logs(project_id, log_type, company_id=company_id, **filters)

    def get(
        self,
        project_id: int,
        log_type: str,
        log_id: int,
        company_id: int | None = None,
        **filters: Any,
    ) -> DailyLogEntry:
        """Return one Daily Log entry."""
        return get_daily_log(project_id, log_type, log_id, company_id=company_id, **filters)

    def list_for_date(
        self,
        project_id: int,
        company_id: int | None = None,
        log_date: str | None = None,
        log_types: Sequence[str] | None = None,
    ) -> DailyLogsByType:
        """Return multiple Daily Log types for one date."""
        return list_daily_logs_for_date(
            project_id, company_id=company_id, log_date=log_date, log_types=log_types
        )

    def delay_types(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[DelayLogType]:
        """Return delay log types."""
        return list_delay_log_types(project_id, company_id=company_id, **filters)

    def manpower(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[DailyLogEntry]:
        """Return manpower logs."""
        return list_manpower_logs(project_id, company_id=company_id, **filters)

    def notes(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[DailyLogEntry]:
        """Return notes logs."""
        return list_notes_logs(project_id, company_id=company_id, **filters)

    def daily_construction_reports(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[DailyLogEntry]:
        """Return daily construction report logs."""
        return list_daily_construction_report_logs(project_id, company_id=company_id, **filters)

    def delays(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[DailyLogEntry]:
        """Return delay logs."""
        return list_delay_logs(project_id, company_id=company_id, **filters)

    def deliveries(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[DailyLogEntry]:
        """Return delivery logs."""
        return list_delivery_logs(project_id, company_id=company_id, **filters)

    def calls(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[DailyLogEntry]:
        """Return call logs."""
        return list_call_logs(project_id, company_id=company_id, **filters)

    def accidents(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[DailyLogEntry]:
        """Return accident logs."""
        return list_accident_logs(project_id, company_id=company_id, **filters)

    def dumpsters(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[DailyLogEntry]:
        """Return dumpster logs."""
        return list_dumpster_logs(project_id, company_id=company_id, **filters)

    def visitors(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[DailyLogEntry]:
        """Return visitor logs."""
        return list_visitor_logs(project_id, company_id=company_id, **filters)

    def productivity(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[DailyLogEntry]:
        """Return productivity logs."""
        return list_productivity_logs(project_id, company_id=company_id, **filters)

    def plan_revisions(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[DailyLogEntry]:
        """Return plan revision logs."""
        return list_plan_revision_logs(project_id, company_id=company_id, **filters)


class CompanyUsersClient:
    """Convenience methods for read-only company directory users."""

    def list(
        self,
        company_id: int | None = None,
        *,
        active: bool | None = None,
        **filters: Any,
    ) -> list[CompanyUser]:
        """List company directory users."""
        return list_company_users(company_id, active=active, **filters)

    def inactive(self, company_id: int | None = None, **filters: Any) -> builtins.list[CompanyUser]:
        """List inactive company directory users."""
        return list_company_inactive_users(company_id, **filters)

    def get(self, user_id: int, company_id: int | None = None) -> CompanyUser:
        """Get one company directory user."""
        return get_company_user(company_id, user_id)

    def find(
        self,
        company_id: int | None = None,
        *,
        name: str | None = None,
        email: str | None = None,
        query: str | None = None,
    ) -> CompanyUser:
        """Find one company directory user by name, email, or text."""
        return find_company_user(company_id, name=name, email=email, query=query)


class ProjectUsersClient:
    """Convenience methods for read-only project directory users."""

    def list(
        self,
        project_id: int,
        company_id: int | None = None,
        *,
        active: bool | None = None,
        **filters: Any,
    ) -> list[ProjectUser]:
        """List project directory users."""
        return list_project_users(company_id, project_id, active=active, **filters)

    def get(self, project_id: int, user_id: int, company_id: int | None = None) -> ProjectUser:
        """Get one project directory user."""
        return get_project_user(company_id, project_id, user_id)

    def find(
        self,
        project_id: int,
        company_id: int | None = None,
        *,
        name: str | None = None,
        email: str | None = None,
        query: str | None = None,
    ) -> ProjectUser:
        """Find one project directory user by name, email, or text."""
        return find_project_user(company_id, project_id, name=name, email=email, query=query)


class VendorsClient:
    """Convenience methods for read-only vendor directory resources."""

    def list(self, company_id: int | None = None, **filters: Any) -> list[Vendor]:
        """List company vendors."""
        return list_vendors(company_id, **filters)

    def list_project(
        self,
        project_id: int,
        company_id: int | None = None,
        **filters: Any,
    ) -> builtins.list[Vendor]:
        """List vendors filtered by project when Procore supports that filter."""
        return list_project_vendors(company_id, project_id, **filters)

    def get(self, vendor_id: int, company_id: int | None = None) -> Vendor:
        """Get one vendor."""
        return get_vendor(company_id, vendor_id)

    def find(
        self,
        company_id: int | None = None,
        *,
        name: str | None = None,
        number: str | int | None = None,
        query: str | None = None,
    ) -> Vendor:
        """Find one vendor by name, number, or text."""
        return find_vendor(company_id, name=name, number=number, query=query)


class DepartmentsClient:
    """Convenience methods for read-only company departments."""

    def list(self, company_id: int | None = None, **filters: Any) -> list[Department]:
        """List company departments."""
        return list_departments(company_id, **filters)

    def get(self, department_id: int, company_id: int | None = None) -> Department:
        """Get one company department."""
        return get_department(company_id, department_id)

    def find(
        self,
        company_id: int | None = None,
        *,
        name: str | None = None,
        code: str | None = None,
        query: str | None = None,
    ) -> Department:
        """Find one department by name, code, or text."""
        return find_department(company_id, name=name, code=code, query=query)


class DistributionGroupsClient:
    """Convenience methods for read-only project distribution groups."""

    def list(
        self,
        project_id: int,
        company_id: int | None = None,
        **filters: Any,
    ) -> list[DistributionGroup]:
        """List project distribution groups."""
        return list_project_distribution_groups(company_id, project_id, **filters)

    def get(
        self,
        project_id: int,
        distribution_group_id: int,
        company_id: int | None = None,
    ) -> DistributionGroup:
        """Get one project distribution group."""
        return get_project_distribution_group(company_id, project_id, distribution_group_id)

    def find(
        self,
        project_id: int,
        company_id: int | None = None,
        *,
        name: str | None = None,
        query: str | None = None,
    ) -> DistributionGroup:
        """Find one project distribution group by name or text."""
        return find_project_distribution_group(company_id, project_id, name=name, query=query)


class LocationsClient:
    """Convenience methods for read-only project locations."""

    def list(
        self,
        project_id: int,
        company_id: int | None = None,
        **filters: Any,
    ) -> list[Location]:
        """List project locations."""
        return list_locations(company_id, project_id, **filters)

    def get(self, project_id: int, location_id: int, company_id: int | None = None) -> Location:
        """Get one project location."""
        return get_location(company_id, project_id, location_id)

    def find(
        self,
        project_id: int,
        company_id: int | None = None,
        *,
        name: str | None = None,
        code: str | None = None,
        query: str | None = None,
    ) -> Location:
        """Find one project location by name, code, or text."""
        return find_location(company_id, project_id, name=name, code=code, query=query)


class ChangeEventsClient:
    """Convenience methods for read-only change events."""

    def list(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[ChangeEvent]:
        """List project change events."""
        return list_change_events(company_id, project_id, **filters)

    def get(
        self, project_id: int, change_event_id: int, company_id: int | None = None
    ) -> ChangeEvent:
        """Get one project change event."""
        return get_change_event(company_id, project_id, change_event_id)

    def find(
        self,
        project_id: int,
        company_id: int | None = None,
        *,
        number: str | int | None = None,
        name: str | None = None,
    ) -> ChangeEvent:
        """Find one project change event by number, title, or name."""
        return find_change_event(project_id, company_id=company_id, number=number, name=name)

    def statuses(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[ChangeEventStatus]:
        """List project change event statuses."""
        return list_change_event_statuses(company_id, project_id, **filters)

    def types(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[ChangeEventType]:
        """List project change event types."""
        return list_change_event_types(company_id, project_id, **filters)

    def settings(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> ChangeEventSettings:
        """Get project change event settings."""
        return get_change_event_settings(company_id, project_id, **filters)


class PrimeChangeOrdersClient:
    """Convenience methods for read-only prime change orders."""

    def list(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[PrimeChangeOrder]:
        """List project prime change orders."""
        return list_prime_change_orders(company_id, project_id, **filters)

    def get(
        self,
        project_id: int,
        prime_change_order_id: int,
        company_id: int | None = None,
    ) -> PrimeChangeOrder:
        """Get one prime change order."""
        return get_prime_change_order(company_id, project_id, prime_change_order_id)

    def find(
        self,
        project_id: int,
        company_id: int | None = None,
        *,
        number: str | int | None = None,
        name: str | None = None,
    ) -> PrimeChangeOrder:
        """Find one prime change order by number, title, or name."""
        return find_prime_change_order(project_id, company_id=company_id, number=number, name=name)


class CommitmentChangeOrdersClient:
    """Convenience methods for read-only commitment change orders."""

    def list(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[CommitmentChangeOrder]:
        """List project commitment change orders."""
        return list_commitment_change_orders(company_id, project_id, **filters)

    def get(
        self,
        project_id: int,
        commitment_change_order_id: int,
        company_id: int | None = None,
    ) -> CommitmentChangeOrder:
        """Get one commitment change order."""
        return get_commitment_change_order(
            company_id,
            project_id,
            commitment_change_order_id,
        )


class ChangeOrderPackagesClient:
    """Convenience methods for read-only change order packages."""

    def list(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[ChangeOrderPackage]:
        """List project change order packages."""
        return list_change_order_packages(company_id, project_id, **filters)

    def get(
        self,
        project_id: int,
        change_order_package_id: int,
        company_id: int | None = None,
    ) -> ChangeOrderPackage:
        """Get one change order package."""
        return get_change_order_package(company_id, project_id, change_order_package_id)


class DirectCostsClient:
    """Convenience methods for read-only direct costs."""

    def list(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[DirectCost]:
        """List project direct costs."""
        return list_direct_costs(company_id, project_id, **filters)

    def get(
        self, project_id: int, direct_cost_id: int, company_id: int | None = None
    ) -> DirectCost:
        """Get one direct cost."""
        return get_direct_cost(company_id, project_id, direct_cost_id)

    def find(
        self,
        project_id: int,
        company_id: int | None = None,
        *,
        number: str | int | None = None,
        name: str | None = None,
    ) -> DirectCost:
        """Find one direct cost by number, title, or name."""
        return find_direct_cost(project_id, company_id=company_id, number=number, name=name)


class BudgetClient:
    """Convenience methods for read-only budget views and rows."""

    def views(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[BudgetView]:
        """List project budget views."""
        return list_budget_views(company_id, project_id, **filters)

    def get_view(
        self, project_id: int, budget_view_id: int, company_id: int | None = None
    ) -> BudgetView:
        """Get one budget view."""
        return get_budget_view(company_id, project_id, budget_view_id)

    def detail_columns(
        self,
        project_id: int,
        budget_view_id: int,
        company_id: int | None = None,
        **filters: Any,
    ) -> builtins.list[BudgetDetailColumn]:
        """List budget detail columns."""
        return list_budget_detail_columns(company_id, project_id, budget_view_id, **filters)

    def details(
        self,
        project_id: int,
        budget_view_id: int,
        company_id: int | None = None,
        **filters: Any,
    ) -> builtins.list[BudgetDetailRow]:
        """List budget detail rows."""
        return list_budget_details(company_id, project_id, budget_view_id, **filters)

    def summary_rows(
        self,
        project_id: int,
        budget_view_id: int,
        company_id: int | None = None,
        **filters: Any,
    ) -> builtins.list[BudgetSummaryRow]:
        """List budget summary rows."""
        return list_budget_view_summary_rows(company_id, project_id, budget_view_id, **filters)


class CostCodesClient:
    """Convenience methods for read-only cost and WBS codes."""

    def list(self, company_id: int | None = None, **filters: Any) -> builtins.list[CostCode]:
        """List company cost codes."""
        return list_cost_codes(company_id, **filters)

    def standard(
        self,
        standard_cost_code_list_id: int,
        company_id: int | None = None,
        **filters: Any,
    ) -> builtins.list[CostCode]:
        """List cost codes for one standard cost code list."""
        return list_standard_cost_codes(company_id, standard_cost_code_list_id, **filters)

    def wbs(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[WbsCode]:
        """List project WBS codes."""
        return list_wbs_codes(company_id, project_id, **filters)


class CommitmentsClient:
    """Convenience methods for read-only commitments."""

    def list(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[Commitment]:
        """List project commitments."""
        return list_commitments(company_id, project_id, **filters)

    def get(self, project_id: int, commitment_id: int, company_id: int | None = None) -> Commitment:
        """Get one commitment."""
        return get_commitment(company_id, project_id, commitment_id)

    def find(
        self,
        project_id: int,
        company_id: int | None = None,
        *,
        number: str | int | None = None,
        name: str | None = None,
    ) -> Commitment:
        """Find one commitment by number, title, or name."""
        return find_commitment(project_id, company_id=company_id, number=number, name=name)


class PrimeContractsClient:
    """Convenience methods for read-only prime contracts."""

    def list(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[PrimeContract]:
        """List project prime contracts."""
        return list_prime_contracts(company_id, project_id, **filters)

    def get(
        self, project_id: int, prime_contract_id: int, company_id: int | None = None
    ) -> PrimeContract:
        """Get one prime contract."""
        return get_prime_contract(company_id, project_id, prime_contract_id)

    def find(
        self,
        project_id: int,
        company_id: int | None = None,
        *,
        number: str | int | None = None,
        name: str | None = None,
    ) -> PrimeContract:
        """Find one prime contract by number, title, or name."""
        return find_prime_contract(project_id, company_id=company_id, number=number, name=name)

    def line_items(
        self,
        project_id: int,
        prime_contract_id: int,
        company_id: int | None = None,
        **filters: Any,
    ) -> builtins.list[PrimeContractLineItem]:
        """List line items for one prime contract."""
        return list_prime_contract_line_items(company_id, project_id, prime_contract_id, **filters)

    def summary(
        self, project_id: int, prime_contract_id: int, company_id: int | None = None
    ) -> PrimeContractSummary:
        """Get read-only summary data for one prime contract."""
        return get_prime_contract_summary(company_id, project_id, prime_contract_id)


class CommitmentContractsClient:
    """Convenience methods for read-only commitment contracts."""

    def list(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[CommitmentContract]:
        """List project commitment contracts."""
        return list_commitment_contracts(company_id, project_id, **filters)

    def get(
        self, project_id: int, commitment_contract_id: int, company_id: int | None = None
    ) -> CommitmentContract:
        """Get one commitment contract."""
        return get_commitment_contract(company_id, project_id, commitment_contract_id)

    def find(
        self,
        project_id: int,
        company_id: int | None = None,
        *,
        number: str | int | None = None,
        name: str | None = None,
    ) -> CommitmentContract:
        """Find one commitment contract by number, title, or name."""
        return find_commitment_contract(project_id, company_id=company_id, number=number, name=name)


class PurchaseOrderContractsClient:
    """Convenience methods for read-only purchase order contracts."""

    def list(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[PurchaseOrderContract]:
        """List project purchase order contracts."""
        return list_purchase_order_contracts(company_id, project_id, **filters)

    def get(
        self, project_id: int, purchase_order_contract_id: int, company_id: int | None = None
    ) -> PurchaseOrderContract:
        """Get one purchase order contract."""
        return get_purchase_order_contract(company_id, project_id, purchase_order_contract_id)

    def find(
        self,
        project_id: int,
        company_id: int | None = None,
        *,
        number: str | int | None = None,
        name: str | None = None,
    ) -> PurchaseOrderContract:
        """Find one purchase order contract by number, title, or name."""
        return find_purchase_order_contract(
            project_id, company_id=company_id, number=number, name=name
        )


class WorkOrderContractsClient:
    """Convenience methods for read-only work order contracts."""

    def list(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[WorkOrderContract]:
        """List project work order contracts."""
        return list_work_order_contracts(company_id, project_id, **filters)

    def get(
        self, project_id: int, work_order_contract_id: int, company_id: int | None = None
    ) -> WorkOrderContract:
        """Get one work order contract."""
        return get_work_order_contract(company_id, project_id, work_order_contract_id)

    def find(
        self,
        project_id: int,
        company_id: int | None = None,
        *,
        number: str | int | None = None,
        name: str | None = None,
    ) -> WorkOrderContract:
        """Find one work order contract by number, title, or name."""
        return find_work_order_contract(project_id, company_id=company_id, number=number, name=name)


class OwnerInvoicesClient:
    """Convenience methods for read-only owner invoices/payment applications."""

    def list(
        self,
        project_id: int,
        prime_contract_id: int,
        company_id: int | None = None,
        **filters: Any,
    ) -> builtins.list[OwnerInvoice]:
        """List owner invoices for one prime contract."""
        return list_owner_invoices(company_id, project_id, prime_contract_id, **filters)

    def get(
        self,
        project_id: int,
        prime_contract_id: int,
        owner_invoice_id: int,
        company_id: int | None = None,
    ) -> OwnerInvoice:
        """Get one owner invoice."""
        return get_owner_invoice(company_id, project_id, prime_contract_id, owner_invoice_id)

    def find(
        self,
        project_id: int,
        prime_contract_id: int,
        company_id: int | None = None,
        *,
        number: str | int | None = None,
        name: str | None = None,
    ) -> OwnerInvoice:
        """Find one owner invoice by number, title, or name."""
        return find_owner_invoice(
            project_id,
            prime_contract_id,
            company_id=company_id,
            number=number,
            name=name,
        )

    def line_items(
        self,
        project_id: int,
        prime_contract_id: int,
        owner_invoice_id: int,
        company_id: int | None = None,
        **filters: Any,
    ) -> builtins.list[OwnerInvoiceLineItem]:
        """List line items for one owner invoice."""
        return list_owner_invoice_line_items(
            company_id,
            project_id,
            prime_contract_id,
            owner_invoice_id,
            **filters,
        )


class SubcontractorInvoicesClient:
    """Convenience methods for read-only subcontractor invoices/requisitions."""

    def list(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[SubcontractorInvoice]:
        """List subcontractor invoices for a project."""
        return list_subcontractor_invoices(company_id, project_id, **filters)

    def get(
        self, project_id: int, subcontractor_invoice_id: int, company_id: int | None = None
    ) -> SubcontractorInvoice:
        """Get one subcontractor invoice."""
        return get_subcontractor_invoice(company_id, project_id, subcontractor_invoice_id)

    def find(
        self,
        project_id: int,
        company_id: int | None = None,
        *,
        number: str | int | None = None,
        name: str | None = None,
    ) -> SubcontractorInvoice:
        """Find one subcontractor invoice by number, title, or name."""
        return find_subcontractor_invoice(
            project_id, company_id=company_id, number=number, name=name
        )

    def contract_items(
        self, project_id: int, requisition_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[RequisitionContractItem]:
        """List contract items for one requisition."""
        return list_requisition_contract_items(company_id, project_id, requisition_id, **filters)

    def contract_detail_items(
        self, project_id: int, requisition_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[RequisitionContractDetailItem]:
        """List contract detail items for one requisition."""
        return list_requisition_contract_detail_items(
            company_id, project_id, requisition_id, **filters
        )

    def change_order_items(
        self, project_id: int, requisition_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[RequisitionChangeOrderItem]:
        """List change order items for one requisition."""
        return list_requisition_change_order_items(
            company_id, project_id, requisition_id, **filters
        )


class ContractPaymentsClient:
    """Convenience methods for read-only contract payments."""

    def list(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[ContractPayment]:
        """List project contract payments."""
        return list_contract_payments(company_id, project_id, **filters)

    def get(
        self, project_id: int, contract_payment_id: int, company_id: int | None = None
    ) -> ContractPayment:
        """Get one contract payment."""
        return get_contract_payment(company_id, project_id, contract_payment_id)

    def find(
        self,
        project_id: int,
        company_id: int | None = None,
        *,
        number: str | int | None = None,
        name: str | None = None,
    ) -> ContractPayment:
        """Find one contract payment by number, title, or name."""
        return find_contract_payment(project_id, company_id=company_id, number=number, name=name)


class BillingPeriodsClient:
    """Convenience methods for read-only billing periods."""

    def list(
        self, project_id: int, company_id: int | None = None, **filters: Any
    ) -> builtins.list[BillingPeriod]:
        """List project billing periods."""
        return list_billing_periods(company_id, project_id, **filters)

    def get(
        self, project_id: int, billing_period_id: int, company_id: int | None = None
    ) -> BillingPeriod:
        """Get one billing period."""
        return get_billing_period(company_id, project_id, billing_period_id)


class CostTypesClient:
    """Convenience methods for read-only company cost types."""

    def list(self, company_id: int | None = None, **filters: Any) -> builtins.list[CostType]:
        """List company cost types."""
        return list_cost_types(company_id, **filters)


class TaxCodesClient:
    """Convenience methods for read-only company tax codes."""

    def list(self, company_id: int | None = None, **filters: Any) -> builtins.list[TaxCode]:
        """List company tax codes."""
        return list_tax_codes(company_id, **filters)


class AutomationClient:
    """Convenience methods for AI-ready automation workflow packages."""

    def build_package(
        self,
        input_data: AutomationInput | None = None,
        *,
        company_id: int | None = None,
        project_id: int | None = None,
        project_name: str | None = None,
        project_number: str | None = None,
        item_type: Literal["rfi", "submittal"] | None = None,
        item_id: int | None = None,
        item_number: str | None = None,
        download_attachments: bool = True,
        output_dir: Path | str | None = None,
    ) -> WorkflowPackage:
        """Build an automation package from a typed input model.

        Args:
            input_data: Optional workflow package input. When omitted, keyword
                arguments are used to build one.
            company_id: Optional company ID used for project search.
            project_id: Optional project ID.
            project_name: Optional project name or name fragment.
            project_number: Optional project number.
            item_type: Workflow target type, such as ``rfi`` or ``submittal``.
            item_id: Optional item ID.
            item_number: Optional item number.
            download_attachments: Whether to download attachments.
            output_dir: Optional attachment output directory.

        Returns:
            A resolved workflow package.
        """
        if input_data is None:
            if item_type is None:
                raise ValidationError(
                    "item_type is required when build_package is called without input_data."
                )
            input_data = AutomationInput(
                company_id=company_id,
                project_id=project_id,
                project_name=project_name,
                project_number=project_number,
                item_type=item_type,
                item_id=item_id,
                item_number=item_number,
                download_attachments=download_attachments,
                output_dir=output_dir,
            )
        return build_workflow_package(input_data)

    def build_rfi_package(
        self,
        *,
        company_id: int | None = None,
        project_id: int | None = None,
        project_name: str | None = None,
        project_number: str | None = None,
        rfi_id: int | None = None,
        number: str | None = None,
        download_attachments: bool = True,
        output_dir: Path | str | None = None,
    ) -> WorkflowPackage:
        """Build an automation package for one RFI.

        Args:
            company_id: Optional company ID used for project search.
            project_id: Optional project ID.
            project_name: Optional project name or name fragment.
            project_number: Optional project number.
            rfi_id: Optional RFI ID.
            number: Optional RFI number.
            download_attachments: Whether to download attachments.
            output_dir: Optional attachment output directory.

        Returns:
            A resolved RFI workflow package.
        """
        return build_rfi_package(
            company_id=company_id,
            project_id=project_id,
            project_name=project_name,
            project_number=project_number,
            rfi_id=rfi_id,
            number=number,
            download_attachments=download_attachments,
            output_dir=output_dir,
        )

    def build_submittal_package(
        self,
        *,
        company_id: int | None = None,
        project_id: int | None = None,
        project_name: str | None = None,
        project_number: str | None = None,
        submittal_id: int | None = None,
        number: str | None = None,
        download_attachments: bool = True,
        output_dir: Path | str | None = None,
    ) -> WorkflowPackage:
        """Build an automation package for one submittal.

        Args:
            company_id: Optional company ID used for project search.
            project_id: Optional project ID.
            project_name: Optional project name or name fragment.
            project_number: Optional project number.
            submittal_id: Optional submittal ID.
            number: Optional submittal number.
            download_attachments: Whether to download attachments.
            output_dir: Optional attachment output directory.

        Returns:
            A resolved submittal workflow package.
        """
        return build_submittal_package(
            company_id=company_id,
            project_id=project_id,
            project_name=project_name,
            project_number=project_number,
            submittal_id=submittal_id,
            number=number,
            download_attachments=download_attachments,
            output_dir=output_dir,
        )


class WorkflowsClient:
    """Convenience methods for local exports and folder sync workflows."""

    def load_workflow_plan(self, path: Path | str) -> WorkflowPlan:
        """Load a local workflow plan from disk."""
        return load_workflow_plan(path)

    def validate_workflow_plan(
        self,
        path_or_plan: Path | str | WorkflowPlan | Mapping[str, object],
    ) -> WorkflowPlan:
        """Validate a local workflow plan without executing it."""
        if isinstance(path_or_plan, (str, Path)):
            return load_workflow_plan(path_or_plan)
        return validate_workflow_plan(path_or_plan)

    def run_workflow_plan(
        self,
        path_or_plan: Path | str | WorkflowPlan | Mapping[str, object],
        output_dir: Path | str | None = None,
        *,
        dry_run: bool = False,
        continue_on_error: bool = True,
    ) -> WorkflowRunResult:
        """Run or dry-run a local workflow automation plan."""
        return run_workflow_plan(
            path_or_plan,
            output_dir=output_dir,
            dry_run=dry_run,
            continue_on_error=continue_on_error,
        )

    def list_available_workflows(self) -> list[str]:
        """Return local workflow names supported by the automation runner."""
        return list_available_workflows()

    def build_ai_review_export(
        self,
        package_dir: Path | str,
        output_dir: Path | str | None = None,
        *,
        export_name: str | None = None,
        format: str = "markdown",
        include_json: bool = True,
        include_prompt: bool = True,
        include_checklists: bool = True,
        max_chunk_chars: int = 12000,
        source_extensions: Sequence[str] | str | None = None,
        exclude_patterns: Sequence[str] | str | None = None,
        overwrite: bool = False,
    ) -> AIExportResult:
        """Build a local AI-friendly review export from a package folder."""
        return build_ai_review_export(
            package_dir,
            output_dir=output_dir,
            export_name=export_name,
            format=format,
            include_json=include_json,
            include_prompt=include_prompt,
            include_checklists=include_checklists,
            max_chunk_chars=max_chunk_chars,
            source_extensions=source_extensions,
            exclude_patterns=exclude_patterns,
            overwrite=overwrite,
        )

    def build_ai_prompt_pack(
        self,
        package_dir: Path | str,
        output_dir: Path | str | None = None,
        *,
        review_type: str = "general",
        max_chunk_chars: int = 12000,
        overwrite: bool = False,
    ) -> AIExportResult:
        """Build a prompt-focused local AI export from a package folder."""
        return build_ai_prompt_pack(
            package_dir,
            output_dir=output_dir,
            review_type=review_type,
            max_chunk_chars=max_chunk_chars,
            overwrite=overwrite,
        )

    def export_rfis_to_csv(
        self,
        project_id: int,
        output_path: Path | str,
        *,
        status: str | None = None,
        updated_after: str | None = None,
        updated_before: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        params: dict[str, object] | None = None,
        **extra_params: Any,
    ) -> Path:
        """Export RFIs to CSV.

        Args:
            project_id: Procore project ID.
            output_path: CSV path to create.
            status: Optional status filter.
            updated_after: Optional lower bound for updated date filtering.
            updated_before: Optional upper bound for updated date filtering.
            created_after: Optional lower bound for created date filtering.
            created_before: Optional upper bound for created date filtering.
            params: Optional additional query parameters.
            **extra_params: Additional Procore query parameters.

        Returns:
            The created CSV path.
        """
        return export_rfis_to_csv(
            project_id,
            output_path,
            status=status,
            updated_after=updated_after,
            updated_before=updated_before,
            created_after=created_after,
            created_before=created_before,
            params=params,
            **extra_params,
        )

    def export_submittals_to_csv(
        self,
        project_id: int,
        output_path: Path | str,
        *,
        status: str | None = None,
        updated_after: str | None = None,
        updated_before: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        params: dict[str, object] | None = None,
        **extra_params: Any,
    ) -> Path:
        """Export submittals to CSV.

        Args:
            project_id: Procore project ID.
            output_path: CSV path to create.
            status: Optional status filter.
            updated_after: Optional lower bound for updated date filtering.
            updated_before: Optional upper bound for updated date filtering.
            created_after: Optional lower bound for created date filtering.
            created_before: Optional upper bound for created date filtering.
            params: Optional additional query parameters.
            **extra_params: Additional Procore query parameters.

        Returns:
            The created CSV path.
        """
        return export_submittals_to_csv(
            project_id,
            output_path,
            status=status,
            updated_after=updated_after,
            updated_before=updated_before,
            created_after=created_after,
            created_before=created_before,
            params=params,
            **extra_params,
        )

    def export_rfis_to_jsonl(
        self,
        project_id: int,
        output_path: Path | str,
        *,
        status: str | None = None,
        **filters: Any,
    ) -> Path:
        """Export RFIs to newline-delimited JSON."""
        return export_rfis_to_jsonl(project_id, output_path, status=status, **filters)

    def export_submittals_to_jsonl(
        self,
        project_id: int,
        output_path: Path | str,
        *,
        status: str | None = None,
        **filters: Any,
    ) -> Path:
        """Export submittals to newline-delimited JSON."""
        return export_submittals_to_jsonl(project_id, output_path, status=status, **filters)

    def export_observations_to_csv(
        self,
        company_id: int | None,
        project_id: int,
        output_path: Path | str,
        **filters: Any,
    ) -> Path:
        """Export observations to CSV."""
        return export_observations_to_csv(company_id, project_id, output_path, **filters)

    def export_observations_to_jsonl(
        self,
        company_id: int | None,
        project_id: int,
        output_path: Path | str,
        **filters: Any,
    ) -> Path:
        """Export observations to newline-delimited JSON."""
        return export_observations_to_jsonl(company_id, project_id, output_path, **filters)

    def export_punch_items_to_csv(
        self,
        company_id: int | None,
        project_id: int,
        output_path: Path | str,
        **filters: Any,
    ) -> Path:
        """Export punch items to CSV."""
        return export_punch_items_to_csv(company_id, project_id, output_path, **filters)

    def export_punch_items_to_jsonl(
        self,
        company_id: int | None,
        project_id: int,
        output_path: Path | str,
        **filters: Any,
    ) -> Path:
        """Export punch items to newline-delimited JSON."""
        return export_punch_items_to_jsonl(company_id, project_id, output_path, **filters)

    def export_correspondences_to_csv(
        self,
        company_id: int | None,
        project_id: int,
        generic_tool_id: int,
        output_path: Path | str,
        **filters: Any,
    ) -> Path:
        """Export Generic Tool correspondence items to CSV."""
        return export_correspondences_to_csv(
            company_id,
            project_id,
            generic_tool_id,
            output_path,
            **filters,
        )

    def export_correspondences_to_jsonl(
        self,
        company_id: int | None,
        project_id: int,
        generic_tool_id: int,
        output_path: Path | str,
        **filters: Any,
    ) -> Path:
        """Export Generic Tool correspondence items to newline-delimited JSON."""
        return export_correspondences_to_jsonl(
            company_id,
            project_id,
            generic_tool_id,
            output_path,
            **filters,
        )

    def export_meetings_to_csv(
        self,
        company_id: int | None,
        project_id: int,
        output_path: Path | str,
        **filters: Any,
    ) -> Path:
        """Export meetings to CSV."""
        return export_meetings_to_csv(company_id, project_id, output_path, **filters)

    def export_meetings_to_jsonl(
        self,
        company_id: int | None,
        project_id: int,
        output_path: Path | str,
        **filters: Any,
    ) -> Path:
        """Export meetings to newline-delimited JSON."""
        return export_meetings_to_jsonl(company_id, project_id, output_path, **filters)

    def export_inspections_to_csv(
        self,
        company_id: int | None,
        project_id: int,
        output_path: Path | str,
        **filters: Any,
    ) -> Path:
        """Export inspections to CSV."""
        return export_inspections_to_csv(company_id, project_id, output_path, **filters)

    def export_inspections_to_jsonl(
        self,
        company_id: int | None,
        project_id: int,
        output_path: Path | str,
        **filters: Any,
    ) -> Path:
        """Export inspections to newline-delimited JSON."""
        return export_inspections_to_jsonl(company_id, project_id, output_path, **filters)

    def export_incidents_to_csv(
        self,
        company_id: int | None,
        project_id: int,
        output_path: Path | str,
        **filters: Any,
    ) -> Path:
        """Export incidents to CSV."""
        return export_incidents_to_csv(company_id, project_id, output_path, **filters)

    def export_incidents_to_jsonl(
        self,
        company_id: int | None,
        project_id: int,
        output_path: Path | str,
        **filters: Any,
    ) -> Path:
        """Export incidents to newline-delimited JSON."""
        return export_incidents_to_jsonl(company_id, project_id, output_path, **filters)

    def export_company_users_to_csv(
        self,
        company_id: int | None,
        output_path: Path | str,
        **filters: Any,
    ) -> Path:
        """Export company users to CSV."""
        return export_company_users_to_csv(company_id, output_path, **filters)

    def export_company_users_to_jsonl(
        self,
        company_id: int | None,
        output_path: Path | str,
        **filters: Any,
    ) -> Path:
        """Export company users to newline-delimited JSON."""
        return export_company_users_to_jsonl(company_id, output_path, **filters)

    def export_project_users_to_csv(
        self,
        company_id: int | None,
        project_id: int,
        output_path: Path | str,
        **filters: Any,
    ) -> Path:
        """Export project users to CSV."""
        return export_project_users_to_csv(company_id, project_id, output_path, **filters)

    def export_project_users_to_jsonl(
        self,
        company_id: int | None,
        project_id: int,
        output_path: Path | str,
        **filters: Any,
    ) -> Path:
        """Export project users to newline-delimited JSON."""
        return export_project_users_to_jsonl(company_id, project_id, output_path, **filters)

    def export_vendors_to_csv(
        self,
        company_id: int | None,
        output_path: Path | str,
        **filters: Any,
    ) -> Path:
        """Export vendors to CSV."""
        return export_vendors_to_csv(company_id, output_path, **filters)

    def export_vendors_to_jsonl(
        self,
        company_id: int | None,
        output_path: Path | str,
        **filters: Any,
    ) -> Path:
        """Export vendors to newline-delimited JSON."""
        return export_vendors_to_jsonl(company_id, output_path, **filters)

    def export_departments_to_csv(
        self,
        company_id: int | None,
        output_path: Path | str,
        **filters: Any,
    ) -> Path:
        """Export departments to CSV."""
        return export_departments_to_csv(company_id, output_path, **filters)

    def export_departments_to_jsonl(
        self,
        company_id: int | None,
        output_path: Path | str,
        **filters: Any,
    ) -> Path:
        """Export departments to newline-delimited JSON."""
        return export_departments_to_jsonl(company_id, output_path, **filters)

    def export_distribution_groups_to_csv(
        self,
        company_id: int | None,
        project_id: int,
        output_path: Path | str,
        **filters: Any,
    ) -> Path:
        """Export distribution groups to CSV."""
        return export_distribution_groups_to_csv(company_id, project_id, output_path, **filters)

    def export_distribution_groups_to_jsonl(
        self,
        company_id: int | None,
        project_id: int,
        output_path: Path | str,
        **filters: Any,
    ) -> Path:
        """Export distribution groups to newline-delimited JSON."""
        return export_distribution_groups_to_jsonl(
            company_id,
            project_id,
            output_path,
            **filters,
        )

    def export_locations_to_csv(
        self,
        company_id: int | None,
        project_id: int,
        output_path: Path | str,
        **filters: Any,
    ) -> Path:
        """Export locations to CSV."""
        return export_locations_to_csv(company_id, project_id, output_path, **filters)

    def export_locations_to_jsonl(
        self,
        company_id: int | None,
        project_id: int,
        output_path: Path | str,
        **filters: Any,
    ) -> Path:
        """Export locations to newline-delimited JSON."""
        return export_locations_to_jsonl(company_id, project_id, output_path, **filters)

    def export_change_events_to_csv(
        self, company_id: int | None, project_id: int, output_path: Path | str, **filters: Any
    ) -> Path:
        """Export change events to CSV."""
        return export_change_events_to_csv(company_id, project_id, output_path, **filters)

    def export_change_events_to_jsonl(
        self, company_id: int | None, project_id: int, output_path: Path | str, **filters: Any
    ) -> Path:
        """Export change events to newline-delimited JSON."""
        return export_change_events_to_jsonl(company_id, project_id, output_path, **filters)

    def export_prime_change_orders_to_csv(
        self, company_id: int | None, project_id: int, output_path: Path | str, **filters: Any
    ) -> Path:
        """Export prime change orders to CSV."""
        return export_prime_change_orders_to_csv(company_id, project_id, output_path, **filters)

    def export_prime_change_orders_to_jsonl(
        self, company_id: int | None, project_id: int, output_path: Path | str, **filters: Any
    ) -> Path:
        """Export prime change orders to newline-delimited JSON."""
        return export_prime_change_orders_to_jsonl(company_id, project_id, output_path, **filters)

    def export_commitment_change_orders_to_csv(
        self, company_id: int | None, project_id: int, output_path: Path | str, **filters: Any
    ) -> Path:
        """Export commitment change orders to CSV."""
        return export_commitment_change_orders_to_csv(
            company_id, project_id, output_path, **filters
        )

    def export_change_order_packages_to_csv(
        self, company_id: int | None, project_id: int, output_path: Path | str, **filters: Any
    ) -> Path:
        """Export change order packages to CSV."""
        return export_change_order_packages_to_csv(company_id, project_id, output_path, **filters)

    def export_direct_costs_to_csv(
        self, company_id: int | None, project_id: int, output_path: Path | str, **filters: Any
    ) -> Path:
        """Export direct costs to CSV."""
        return export_direct_costs_to_csv(company_id, project_id, output_path, **filters)

    def export_direct_costs_to_jsonl(
        self, company_id: int | None, project_id: int, output_path: Path | str, **filters: Any
    ) -> Path:
        """Export direct costs to newline-delimited JSON."""
        return export_direct_costs_to_jsonl(company_id, project_id, output_path, **filters)

    def export_budget_views_to_csv(
        self, company_id: int | None, project_id: int, output_path: Path | str, **filters: Any
    ) -> Path:
        """Export budget views to CSV."""
        return export_budget_views_to_csv(company_id, project_id, output_path, **filters)

    def export_budget_details_to_csv(
        self,
        company_id: int | None,
        project_id: int,
        budget_view_id: int,
        output_path: Path | str,
        **filters: Any,
    ) -> Path:
        """Export budget detail rows to CSV."""
        return export_budget_details_to_csv(
            company_id,
            project_id,
            budget_view_id,
            output_path,
            **filters,
        )

    def export_budget_summary_rows_to_csv(
        self,
        company_id: int | None,
        project_id: int,
        budget_view_id: int,
        output_path: Path | str,
        **filters: Any,
    ) -> Path:
        """Export budget summary rows to CSV."""
        return export_budget_summary_rows_to_csv(
            company_id,
            project_id,
            budget_view_id,
            output_path,
            **filters,
        )

    def export_cost_codes_to_csv(
        self, company_id: int | None, output_path: Path | str, **filters: Any
    ) -> Path:
        """Export cost codes to CSV."""
        return export_cost_codes_to_csv(company_id, output_path, **filters)

    def export_commitments_to_csv(
        self, company_id: int | None, project_id: int, output_path: Path | str, **filters: Any
    ) -> Path:
        """Export commitments to CSV."""
        return export_commitments_to_csv(company_id, project_id, output_path, **filters)

    def sync_rfis_to_folder(
        self,
        project_id: int,
        output_dir: Path | str,
        *,
        status: str | None = None,
        download_attachments: bool = True,
        overwrite: bool = False,
        create_tracker: bool = True,
        create_markdown: bool = True,
        dry_run: bool = False,
        incremental: bool = False,
        **filters: Any,
    ) -> SyncResult:
        """Sync RFIs into a local folder tree."""
        return sync_rfis_to_folder(
            project_id,
            output_dir,
            status=status,
            download_attachments=download_attachments,
            overwrite=overwrite,
            create_tracker=create_tracker,
            create_markdown=create_markdown,
            dry_run=dry_run,
            incremental=incremental,
            **filters,
        )

    def sync_submittals_to_folder(
        self,
        project_id: int,
        output_dir: Path | str,
        *,
        status: str | None = None,
        download_attachments: bool = True,
        overwrite: bool = False,
        create_tracker: bool = True,
        create_markdown: bool = True,
        dry_run: bool = False,
        incremental: bool = False,
        **filters: Any,
    ) -> SyncResult:
        """Sync submittals into a local folder tree."""
        return sync_submittals_to_folder(
            project_id,
            output_dir,
            status=status,
            download_attachments=download_attachments,
            overwrite=overwrite,
            create_tracker=create_tracker,
            create_markdown=create_markdown,
            dry_run=dry_run,
            incremental=incremental,
            **filters,
        )

    def sync_documents_to_folder(
        self,
        project_id: int,
        output_dir: Path | str,
        *,
        folder_id: int | None = None,
        recursive: bool = False,
        overwrite: bool = False,
        dry_run: bool = False,
        incremental: bool = False,
        create_tracker: bool = True,
        create_markdown: bool = True,
        **filters: Any,
    ) -> SyncResult:
        """Sync documents into a local folder tree."""
        return sync_documents_to_folder(
            project_id,
            output_dir,
            folder_id=folder_id,
            recursive=recursive,
            overwrite=overwrite,
            dry_run=dry_run,
            incremental=incremental,
            create_tracker=create_tracker,
            create_markdown=create_markdown,
            **filters,
        )

    def sync_project_to_folder(
        self,
        project_id: int,
        output_dir: Path | str,
        *,
        include_rfis: bool = True,
        include_submittals: bool = True,
        status: str | None = None,
        download_attachments: bool = True,
        overwrite: bool = False,
        create_tracker: bool = True,
        create_markdown: bool = True,
        dry_run: bool = False,
        incremental: bool = False,
        **filters: Any,
    ) -> ProjectSyncResult:
        """Sync RFIs and/or submittals into one project folder."""
        return sync_project_to_folder(
            project_id,
            output_dir,
            include_rfis=include_rfis,
            include_submittals=include_submittals,
            status=status,
            download_attachments=download_attachments,
            overwrite=overwrite,
            create_tracker=create_tracker,
            create_markdown=create_markdown,
            dry_run=dry_run,
            incremental=incremental,
            **filters,
        )

    def build_project_context_package(
        self,
        project_id: int,
        output_dir: Path | str | None = None,
        *,
        company_id: int | None = None,
        include: Sequence[str] | str | None = None,
        exclude: Sequence[str] | str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        log_date: str | None = None,
        max_items: int | None = None,
        download_files: bool = False,
        overwrite: bool = False,
        continue_on_error: bool = True,
    ) -> ProjectContextResult:
        """Build an AI-ready read-only project context package."""
        return build_project_context_package(
            project_id,
            company_id=company_id,
            output_dir=output_dir,
            include=include,
            exclude=exclude,
            start_date=start_date,
            end_date=end_date,
            log_date=log_date,
            max_items=max_items,
            download_files=download_files,
            overwrite=overwrite,
            continue_on_error=continue_on_error,
        )

    def build_enhanced_rfi_package(
        self,
        project_id: int,
        *,
        rfi_id: int | None = None,
        rfi_number: str | None = None,
        company_id: int | None = None,
        output_dir: Path | str | None = None,
        include_related: bool = True,
        related_sections: Sequence[str] | str | None = None,
        exclude_related: Sequence[str] | str | None = None,
        search_terms: Sequence[str] | str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        log_date: str | None = None,
        max_related_items: int = 25,
        download_files: bool = False,
        overwrite: bool = False,
        continue_on_error: bool = True,
    ) -> EnhancedRFIPackageResult:
        """Build an enhanced AI-ready RFI review package."""
        return build_enhanced_rfi_package(
            project_id,
            rfi_id=rfi_id,
            rfi_number=rfi_number,
            company_id=company_id,
            output_dir=output_dir,
            include_related=include_related,
            related_sections=related_sections,
            exclude_related=exclude_related,
            search_terms=search_terms,
            start_date=start_date,
            end_date=end_date,
            log_date=log_date,
            max_related_items=max_related_items,
            download_files=download_files,
            overwrite=overwrite,
            continue_on_error=continue_on_error,
        )

    def build_enhanced_submittal_package(
        self,
        project_id: int,
        *,
        submittal_id: int | None = None,
        submittal_number: str | None = None,
        company_id: int | None = None,
        output_dir: Path | str | None = None,
        include_related: bool = True,
        related_sections: Sequence[str] | str | None = None,
        exclude_related: Sequence[str] | str | None = None,
        search_terms: Sequence[str] | str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        log_date: str | None = None,
        max_related_items: int = 25,
        download_files: bool = False,
        overwrite: bool = False,
        continue_on_error: bool = True,
    ) -> EnhancedSubmittalPackageResult:
        """Build an enhanced AI-ready submittal review package."""
        return build_enhanced_submittal_package(
            project_id,
            submittal_id=submittal_id,
            submittal_number=submittal_number,
            company_id=company_id,
            output_dir=output_dir,
            include_related=include_related,
            related_sections=related_sections,
            exclude_related=exclude_related,
            search_terms=search_terms,
            start_date=start_date,
            end_date=end_date,
            log_date=log_date,
            max_related_items=max_related_items,
            download_files=download_files,
            overwrite=overwrite,
            continue_on_error=continue_on_error,
        )


class Procore:
    """Beginner-friendly object-oriented entry point for PyProcore.

    The grouped clients call the same service functions that PyProcore already
    exposes. Use this interface when you prefer discoverable dot notation such
    as ``client.projects.list(company_id=123456)``.
    """

    def __init__(self) -> None:
        """Create grouped service clients."""
        self.companies = CompaniesClient()
        self.projects = ProjectsClient()
        self.rfis = RFIsClient()
        self.submittals = SubmittalsClient()
        self.observations = ObservationsClient()
        self.punch_items = PunchItemsClient()
        self.correspondence = CorrespondenceClient()
        self.meetings = MeetingsClient()
        self.inspections = InspectionsClient()
        self.incidents = IncidentsClient()
        self.documents = DocumentsClient()
        self.drawings = DrawingsClient()
        self.specifications = SpecificationsClient()
        self.photos = PhotosClient()
        self.daily_logs = DailyLogsClient()
        self.company_users = CompanyUsersClient()
        self.project_users = ProjectUsersClient()
        self.vendors = VendorsClient()
        self.departments = DepartmentsClient()
        self.distribution_groups = DistributionGroupsClient()
        self.locations = LocationsClient()
        self.change_events = ChangeEventsClient()
        self.prime_change_orders = PrimeChangeOrdersClient()
        self.commitment_change_orders = CommitmentChangeOrdersClient()
        self.change_order_packages = ChangeOrderPackagesClient()
        self.direct_costs = DirectCostsClient()
        self.budget = BudgetClient()
        self.cost_codes = CostCodesClient()
        self.commitments = CommitmentsClient()
        self.prime_contracts = PrimeContractsClient()
        self.commitment_contracts = CommitmentContractsClient()
        self.purchase_order_contracts = PurchaseOrderContractsClient()
        self.work_order_contracts = WorkOrderContractsClient()
        self.owner_invoices = OwnerInvoicesClient()
        self.payment_applications = self.owner_invoices
        self.subcontractor_invoices = SubcontractorInvoicesClient()
        self.requisitions = self.subcontractor_invoices
        self.contract_payments = ContractPaymentsClient()
        self.billing_periods = BillingPeriodsClient()
        self.cost_types = CostTypesClient()
        self.tax_codes = TaxCodesClient()
        self.automation = AutomationClient()
        self.workflows = WorkflowsClient()


__all__ = [
    "AutomationClient",
    "BillingPeriodsClient",
    "BudgetClient",
    "ChangeEventsClient",
    "ChangeOrderPackagesClient",
    "CompaniesClient",
    "CompanyUsersClient",
    "CommitmentChangeOrdersClient",
    "CommitmentContractsClient",
    "CommitmentsClient",
    "CorrespondenceClient",
    "ContractPaymentsClient",
    "CostCodesClient",
    "CostTypesClient",
    "DailyLogsClient",
    "DepartmentsClient",
    "DirectCostsClient",
    "DistributionGroupsClient",
    "DocumentsClient",
    "DrawingsClient",
    "IncidentsClient",
    "InspectionsClient",
    "LocationsClient",
    "MeetingsClient",
    "ObservationsClient",
    "Procore",
    "ProjectsClient",
    "ProjectUsersClient",
    "PhotosClient",
    "PrimeChangeOrdersClient",
    "PrimeContractsClient",
    "PunchItemsClient",
    "PurchaseOrderContractsClient",
    "RFIsClient",
    "SpecificationsClient",
    "SubcontractorInvoicesClient",
    "SubmittalsClient",
    "TaxCodesClient",
    "VendorsClient",
    "WorkOrderContractsClient",
    "WorkflowsClient",
]
