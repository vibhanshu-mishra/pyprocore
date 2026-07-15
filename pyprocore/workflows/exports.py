"""CSV and JSONL export helpers for Procore workflow automation."""

from __future__ import annotations

import csv
import json
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from pyprocore.models import (
    RFI,
    ActionPlan,
    ActionPlanChangeHistoryEvent,
    BillingPeriod,
    BudgetDetailRow,
    BudgetSummaryRow,
    BudgetView,
    CalendarItem,
    ChangeEvent,
    ChangeOrderPackage,
    Commitment,
    CommitmentChangeOrder,
    CommitmentContract,
    CompanyUser,
    ContractPayment,
    CoordinationIssue,
    CoordinationIssueActivity,
    CoordinationIssueChangeHistoryEvent,
    CoordinationIssueFilterOption,
    Correspondence,
    CostType,
    Department,
    DirectCost,
    DistributionGroup,
    Document,
    Form,
    FormTemplate,
    Incident,
    Inspection,
    Location,
    Meeting,
    Observation,
    OwnerInvoice,
    OwnerInvoiceLineItem,
    PrimeChangeOrder,
    PrimeContract,
    PrimeContractLineItem,
    ProjectUser,
    PunchItem,
    PurchaseOrderContract,
    RequisitionChangeOrderItem,
    RequisitionContractDetailItem,
    RequisitionContractItem,
    ScheduleResourceAssignment,
    SubcontractorInvoice,
    Submittal,
    Task,
    TaskRequestedChange,
    TaxCode,
    Vendor,
    WorkOrderContract,
)
from pyprocore.services.contracts import (
    list_billing_periods,
    list_commitment_contracts,
    list_contract_payments,
    list_cost_types,
    list_owner_invoice_line_items,
    list_owner_invoices,
    list_prime_contract_line_items,
    list_prime_contracts,
    list_purchase_order_contracts,
    list_requisition_change_order_items,
    list_requisition_contract_detail_items,
    list_requisition_contract_items,
    list_subcontractor_invoices,
    list_tax_codes,
    list_work_order_contracts,
)
from pyprocore.services.correspondence import list_correspondences
from pyprocore.services.directory import (
    list_company_users,
    list_departments,
    list_locations,
    list_project_distribution_groups,
    list_project_users,
    list_vendors,
)
from pyprocore.services.financials import (
    list_budget_details,
    list_budget_view_summary_rows,
    list_budget_views,
    list_change_events,
    list_change_order_packages,
    list_commitment_change_orders,
    list_commitments,
    list_cost_codes,
    list_direct_costs,
    list_prime_change_orders,
)
from pyprocore.services.observations import list_observations
from pyprocore.services.operations import list_incidents, list_inspections, list_meetings
from pyprocore.services.project_management import (
    list_action_plan_change_history_events,
    list_action_plans,
    list_calendar_items,
    list_coordination_issue_activity_feed,
    list_coordination_issue_change_history,
    list_coordination_issue_filter_options,
    list_coordination_issues,
    list_form_templates,
    list_forms,
    list_schedule_resource_assignments,
    list_task_requested_changes,
    list_tasks,
)
from pyprocore.services.punch_items import list_punch_items
from pyprocore.services.rfis import list_rfis
from pyprocore.services.submittals import list_submittals
from pyprocore.workflows.utils import (
    attachment_count,
    get_value,
    item_title,
    model_to_dict,
    scalar_text,
)

RFI_CSV_HEADERS = [
    "id",
    "number",
    "subject",
    "status",
    "created_at",
    "updated_at",
    "due_date",
    "ball_in_court",
    "responsible_contractor",
    "assignee",
    "question_count",
    "attachment_count",
]

SUBMITTAL_CSV_HEADERS = [
    "id",
    "number",
    "title",
    "status",
    "created_at",
    "updated_at",
    "due_date",
    "ball_in_court",
    "responsible_contractor",
    "attachment_count",
]

DOCUMENT_CSV_HEADERS = [
    "id",
    "name",
    "filename",
    "folder_id",
    "content_type",
    "file_size",
    "created_at",
    "updated_at",
    "download_url",
]

OBSERVATION_CSV_HEADERS = [
    "id",
    "number",
    "title",
    "status",
    "type",
    "priority",
    "created_at",
    "updated_at",
    "due_date",
    "assignee",
    "created_by",
    "attachment_count",
]

PUNCH_ITEM_CSV_HEADERS = [
    "id",
    "number",
    "title",
    "status",
    "type",
    "priority",
    "created_at",
    "updated_at",
    "due_date",
    "assignee",
    "created_by",
    "attachment_count",
]

CORRESPONDENCE_CSV_HEADERS = [
    "id",
    "number",
    "subject",
    "title",
    "status",
    "generic_tool_id",
    "created_at",
    "updated_at",
    "due_date",
    "assignee",
    "created_by",
    "attachment_count",
]

MEETING_CSV_HEADERS = [
    "id",
    "number",
    "title",
    "status",
    "meeting_date",
    "location",
    "created_at",
    "updated_at",
    "created_by",
    "attachment_count",
]

INSPECTION_CSV_HEADERS = [
    "id",
    "number",
    "title",
    "status",
    "type",
    "created_at",
    "updated_at",
    "due_date",
    "assignee",
    "created_by",
    "item_count",
    "attachment_count",
]

INCIDENT_CSV_HEADERS = [
    "id",
    "number",
    "title",
    "status",
    "type",
    "severity",
    "incident_date",
    "location",
    "created_at",
    "updated_at",
    "reported_by",
    "created_by",
    "attachment_count",
]

COMPANY_USER_CSV_HEADERS = [
    "id",
    "name",
    "email",
    "login",
    "active",
    "job_title",
    "phone",
    "vendor",
    "created_at",
    "updated_at",
]

PROJECT_USER_CSV_HEADERS = [
    "id",
    "name",
    "email",
    "login",
    "active",
    "job_title",
    "phone",
    "project_id",
    "permission_template",
    "role",
    "created_at",
    "updated_at",
]

VENDOR_CSV_HEADERS = [
    "id",
    "name",
    "legal_name",
    "trade_name",
    "vendor_number",
    "active",
    "phone",
    "email",
    "website",
    "company_id",
    "created_at",
    "updated_at",
]

DEPARTMENT_CSV_HEADERS = [
    "id",
    "name",
    "code",
    "description",
    "active",
    "company_id",
    "created_at",
    "updated_at",
]

DISTRIBUTION_GROUP_CSV_HEADERS = [
    "id",
    "name",
    "description",
    "project_id",
    "member_count",
    "created_at",
    "updated_at",
]

LOCATION_CSV_HEADERS = [
    "id",
    "name",
    "full_name",
    "path",
    "code",
    "parent_id",
    "project_id",
    "created_at",
    "updated_at",
]

FINANCIAL_CSV_HEADERS = [
    "id",
    "number",
    "title",
    "name",
    "status",
    "amount",
    "created_at",
    "updated_at",
]

BUDGET_VIEW_CSV_HEADERS = [
    "id",
    "name",
    "description",
    "project_id",
    "created_at",
    "updated_at",
]

BUDGET_ROW_CSV_HEADERS = [
    "id",
    "name",
    "cost_code",
    "cost_type",
    "project_id",
]

COST_CODE_CSV_HEADERS = [
    "id",
    "code",
    "name",
    "full_code",
    "description",
    "company_id",
]


def export_rfis_to_csv(
    project_id: int,
    output_path: Path | str,
    *,
    status: str | None = None,
    updated_after: str | None = None,
    updated_before: str | None = None,
    created_after: str | None = None,
    created_before: str | None = None,
    params: Mapping[str, Any] | None = None,
    **extra_params: Any,
) -> Path:
    """Export project RFIs to a CSV file.

    Args:
        project_id: Procore project ID.
        output_path: CSV path to create.
        status: Optional status filter.
        updated_after: Optional lower bound for updated date filtering.
        updated_before: Optional upper bound for updated date filtering.
        created_after: Optional lower bound for created date filtering.
        created_before: Optional upper bound for created date filtering.
        params: Additional query parameters passed to the RFI service.
        **extra_params: Additional Procore query parameters.

    Returns:
        The created CSV path.
    """
    rfis = _load_rfis(
        project_id,
        status=status,
        updated_after=updated_after,
        updated_before=updated_before,
        created_after=created_after,
        created_before=created_before,
        params=params,
        **extra_params,
    )
    return write_rfis_csv(rfis, output_path)


def export_submittals_to_csv(
    project_id: int,
    output_path: Path | str,
    *,
    status: str | None = None,
    updated_after: str | None = None,
    updated_before: str | None = None,
    created_after: str | None = None,
    created_before: str | None = None,
    params: Mapping[str, Any] | None = None,
    **extra_params: Any,
) -> Path:
    """Export project submittals to a CSV file.

    Args:
        project_id: Procore project ID.
        output_path: CSV path to create.
        status: Optional status filter.
        updated_after: Optional lower bound for updated date filtering.
        updated_before: Optional upper bound for updated date filtering.
        created_after: Optional lower bound for created date filtering.
        created_before: Optional upper bound for created date filtering.
        params: Additional query parameters passed to the submittal service.
        **extra_params: Additional Procore query parameters.

    Returns:
        The created CSV path.
    """
    submittals = _load_submittals(
        project_id,
        status=status,
        updated_after=updated_after,
        updated_before=updated_before,
        created_after=created_after,
        created_before=created_before,
        params=params,
        **extra_params,
    )
    return write_submittals_csv(submittals, output_path)


def export_rfis_to_jsonl(
    project_id: int,
    output_path: Path | str,
    *,
    status: str | None = None,
    updated_after: str | None = None,
    updated_before: str | None = None,
    created_after: str | None = None,
    created_before: str | None = None,
    params: Mapping[str, Any] | None = None,
    **extra_params: Any,
) -> Path:
    """Export project RFIs to newline-delimited JSON.

    Args:
        project_id: Procore project ID.
        output_path: JSONL path to create.
        status: Optional status filter.
        updated_after: Optional lower bound for updated date filtering.
        updated_before: Optional upper bound for updated date filtering.
        created_after: Optional lower bound for created date filtering.
        created_before: Optional upper bound for created date filtering.
        params: Additional query parameters passed to the RFI service.
        **extra_params: Additional Procore query parameters.

    Returns:
        The created JSONL path.
    """
    rfis = _load_rfis(
        project_id,
        status=status,
        updated_after=updated_after,
        updated_before=updated_before,
        created_after=created_after,
        created_before=created_before,
        params=params,
        **extra_params,
    )
    return _write_jsonl(rfis, output_path)


def export_submittals_to_jsonl(
    project_id: int,
    output_path: Path | str,
    *,
    status: str | None = None,
    updated_after: str | None = None,
    updated_before: str | None = None,
    created_after: str | None = None,
    created_before: str | None = None,
    params: Mapping[str, Any] | None = None,
    **extra_params: Any,
) -> Path:
    """Export project submittals to newline-delimited JSON.

    Args:
        project_id: Procore project ID.
        output_path: JSONL path to create.
        status: Optional status filter.
        updated_after: Optional lower bound for updated date filtering.
        updated_before: Optional upper bound for updated date filtering.
        created_after: Optional lower bound for created date filtering.
        created_before: Optional upper bound for created date filtering.
        params: Additional query parameters passed to the submittal service.
        **extra_params: Additional Procore query parameters.

    Returns:
        The created JSONL path.
    """
    submittals = _load_submittals(
        project_id,
        status=status,
        updated_after=updated_after,
        updated_before=updated_before,
        created_after=created_after,
        created_before=created_before,
        params=params,
        **extra_params,
    )
    return _write_jsonl(submittals, output_path)


def export_observations_to_csv(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project observations to a CSV file."""
    observations = list_observations(company_id, project_id, **filters)
    return write_observations_csv(observations, output_path)


def export_observations_to_jsonl(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project observations to newline-delimited JSON."""
    observations = list_observations(company_id, project_id, **filters)
    return _write_jsonl(observations, output_path)


def export_punch_items_to_csv(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project punch items to a CSV file."""
    punch_items = list_punch_items(company_id, project_id, **filters)
    return write_punch_items_csv(punch_items, output_path)


def export_punch_items_to_jsonl(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project punch items to newline-delimited JSON."""
    punch_items = list_punch_items(company_id, project_id, **filters)
    return _write_jsonl(punch_items, output_path)


def export_correspondences_to_csv(
    company_id: int | None,
    project_id: int,
    generic_tool_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export Generic Tool correspondence items to a CSV file."""
    correspondences = list_correspondences(company_id, project_id, generic_tool_id, **filters)
    return write_correspondences_csv(correspondences, output_path)


def export_correspondences_to_jsonl(
    company_id: int | None,
    project_id: int,
    generic_tool_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export Generic Tool correspondence items to newline-delimited JSON."""
    correspondences = list_correspondences(company_id, project_id, generic_tool_id, **filters)
    return _write_jsonl(correspondences, output_path)


def export_meetings_to_csv(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project meetings to a CSV file."""
    meetings = list_meetings(company_id, project_id, **filters)
    return write_meetings_csv(meetings, output_path)


def export_meetings_to_jsonl(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project meetings to newline-delimited JSON."""
    meetings = list_meetings(company_id, project_id, **filters)
    return _write_jsonl(meetings, output_path)


def export_inspections_to_csv(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project inspections to a CSV file."""
    inspections = list_inspections(company_id, project_id, **filters)
    return write_inspections_csv(inspections, output_path)


def export_inspections_to_jsonl(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project inspections to newline-delimited JSON."""
    inspections = list_inspections(company_id, project_id, **filters)
    return _write_jsonl(inspections, output_path)


def export_incidents_to_csv(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project incidents to a CSV file."""
    incidents = list_incidents(company_id, project_id, **filters)
    return write_incidents_csv(incidents, output_path)


def export_incidents_to_jsonl(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project incidents to newline-delimited JSON."""
    incidents = list_incidents(company_id, project_id, **filters)
    return _write_jsonl(incidents, output_path)


def export_company_users_to_csv(
    company_id: int | None,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export company directory users to a CSV file."""
    users = list_company_users(company_id, **filters)
    return write_company_users_csv(users, output_path)


def export_company_users_to_jsonl(
    company_id: int | None,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export company directory users to newline-delimited JSON."""
    users = list_company_users(company_id, **filters)
    return _write_jsonl(users, output_path)


def export_project_users_to_csv(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project directory users to a CSV file."""
    users = list_project_users(company_id, project_id, **filters)
    return write_project_users_csv(users, output_path)


def export_project_users_to_jsonl(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project directory users to newline-delimited JSON."""
    users = list_project_users(company_id, project_id, **filters)
    return _write_jsonl(users, output_path)


def export_vendors_to_csv(
    company_id: int | None,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export vendors to a CSV file."""
    vendors = list_vendors(company_id, **filters)
    return write_vendors_csv(vendors, output_path)


def export_vendors_to_jsonl(
    company_id: int | None,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export vendors to newline-delimited JSON."""
    vendors = list_vendors(company_id, **filters)
    return _write_jsonl(vendors, output_path)


def export_departments_to_csv(
    company_id: int | None,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export company departments to a CSV file."""
    departments = list_departments(company_id, **filters)
    return write_departments_csv(departments, output_path)


def export_departments_to_jsonl(
    company_id: int | None,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export company departments to newline-delimited JSON."""
    departments = list_departments(company_id, **filters)
    return _write_jsonl(departments, output_path)


def export_distribution_groups_to_csv(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project distribution groups to a CSV file."""
    groups = list_project_distribution_groups(company_id, project_id, **filters)
    return write_distribution_groups_csv(groups, output_path)


def export_distribution_groups_to_jsonl(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project distribution groups to newline-delimited JSON."""
    groups = list_project_distribution_groups(company_id, project_id, **filters)
    return _write_jsonl(groups, output_path)


def export_locations_to_csv(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project locations to a CSV file."""
    locations = list_locations(company_id, project_id, **filters)
    return write_locations_csv(locations, output_path)


def export_locations_to_jsonl(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project locations to newline-delimited JSON."""
    locations = list_locations(company_id, project_id, **filters)
    return _write_jsonl(locations, output_path)


def export_change_events_to_csv(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project change events to a CSV file."""
    return write_change_events_csv(
        list_change_events(company_id, project_id, **filters),
        output_path,
    )


def export_change_events_to_jsonl(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project change events to newline-delimited JSON."""
    return _write_jsonl(list_change_events(company_id, project_id, **filters), output_path)


def export_prime_change_orders_to_csv(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project prime change orders to a CSV file."""
    return write_prime_change_orders_csv(
        list_prime_change_orders(company_id, project_id, **filters),
        output_path,
    )


def export_prime_change_orders_to_jsonl(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project prime change orders to newline-delimited JSON."""
    return _write_jsonl(
        list_prime_change_orders(company_id, project_id, **filters),
        output_path,
    )


def export_commitment_change_orders_to_csv(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project commitment change orders to a CSV file."""
    return write_commitment_change_orders_csv(
        list_commitment_change_orders(company_id, project_id, **filters),
        output_path,
    )


def export_commitment_change_orders_to_jsonl(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project commitment change orders to newline-delimited JSON."""
    return _write_jsonl(
        list_commitment_change_orders(company_id, project_id, **filters),
        output_path,
    )


def export_change_order_packages_to_csv(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project change order packages to a CSV file."""
    return write_change_order_packages_csv(
        list_change_order_packages(company_id, project_id, **filters),
        output_path,
    )


def export_change_order_packages_to_jsonl(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project change order packages to newline-delimited JSON."""
    return _write_jsonl(
        list_change_order_packages(company_id, project_id, **filters),
        output_path,
    )


def export_direct_costs_to_csv(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project direct costs to a CSV file."""
    return write_direct_costs_csv(
        list_direct_costs(company_id, project_id, **filters),
        output_path,
    )


def export_direct_costs_to_jsonl(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project direct costs to newline-delimited JSON."""
    return _write_jsonl(list_direct_costs(company_id, project_id, **filters), output_path)


def export_budget_views_to_csv(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project budget views to a CSV file."""
    return write_budget_views_csv(
        list_budget_views(company_id, project_id, **filters),
        output_path,
    )


def export_budget_views_to_jsonl(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project budget views to newline-delimited JSON."""
    return _write_jsonl(list_budget_views(company_id, project_id, **filters), output_path)


def export_budget_details_to_csv(
    company_id: int | None,
    project_id: int,
    budget_view_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project budget detail rows to a CSV file."""
    return write_budget_details_csv(
        list_budget_details(company_id, project_id, budget_view_id, **filters),
        output_path,
    )


def export_budget_details_to_jsonl(
    company_id: int | None,
    project_id: int,
    budget_view_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project budget detail rows to newline-delimited JSON."""
    return _write_jsonl(
        list_budget_details(company_id, project_id, budget_view_id, **filters),
        output_path,
    )


def export_budget_summary_rows_to_csv(
    company_id: int | None,
    project_id: int,
    budget_view_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project budget summary rows to a CSV file."""
    return write_budget_summary_rows_csv(
        list_budget_view_summary_rows(company_id, project_id, budget_view_id, **filters),
        output_path,
    )


def export_budget_summary_rows_to_jsonl(
    company_id: int | None,
    project_id: int,
    budget_view_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project budget summary rows to newline-delimited JSON."""
    return _write_jsonl(
        list_budget_view_summary_rows(company_id, project_id, budget_view_id, **filters),
        output_path,
    )


def export_cost_codes_to_csv(
    company_id: int | None,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export company cost codes to a CSV file."""
    return write_cost_codes_csv(list_cost_codes(company_id, **filters), output_path)


def export_cost_codes_to_jsonl(
    company_id: int | None,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export company cost codes to newline-delimited JSON."""
    return _write_jsonl(list_cost_codes(company_id, **filters), output_path)


def export_commitments_to_csv(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project commitments to a CSV file."""
    return write_commitments_csv(
        list_commitments(company_id, project_id, **filters),
        output_path,
    )


def export_commitments_to_jsonl(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project commitments to newline-delimited JSON."""
    return _write_jsonl(list_commitments(company_id, project_id, **filters), output_path)


def export_prime_contracts_to_csv(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project prime contracts to a CSV file."""
    return write_prime_contracts_csv(
        list_prime_contracts(company_id, project_id, **filters),
        output_path,
    )


def export_prime_contracts_to_jsonl(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project prime contracts to newline-delimited JSON."""
    return _write_jsonl(list_prime_contracts(company_id, project_id, **filters), output_path)


def export_prime_contract_line_items_to_csv(
    company_id: int | None,
    project_id: int,
    prime_contract_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export prime contract line items to a CSV file."""
    return write_prime_contract_line_items_csv(
        list_prime_contract_line_items(
            company_id,
            project_id,
            prime_contract_id,
            **filters,
        ),
        output_path,
    )


def export_prime_contract_line_items_to_jsonl(
    company_id: int | None,
    project_id: int,
    prime_contract_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export prime contract line items to newline-delimited JSON."""
    return _write_jsonl(
        list_prime_contract_line_items(company_id, project_id, prime_contract_id, **filters),
        output_path,
    )


def export_commitment_contracts_to_csv(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project commitment contracts to a CSV file."""
    return write_commitment_contracts_csv(
        list_commitment_contracts(company_id, project_id, **filters),
        output_path,
    )


def export_commitment_contracts_to_jsonl(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project commitment contracts to newline-delimited JSON."""
    return _write_jsonl(
        list_commitment_contracts(company_id, project_id, **filters),
        output_path,
    )


def export_purchase_order_contracts_to_csv(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project purchase order contracts to a CSV file."""
    return write_purchase_order_contracts_csv(
        list_purchase_order_contracts(company_id, project_id, **filters),
        output_path,
    )


def export_purchase_order_contracts_to_jsonl(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project purchase order contracts to newline-delimited JSON."""
    return _write_jsonl(
        list_purchase_order_contracts(company_id, project_id, **filters),
        output_path,
    )


def export_work_order_contracts_to_csv(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project work order contracts to a CSV file."""
    return write_work_order_contracts_csv(
        list_work_order_contracts(company_id, project_id, **filters),
        output_path,
    )


def export_work_order_contracts_to_jsonl(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project work order contracts to newline-delimited JSON."""
    return _write_jsonl(
        list_work_order_contracts(company_id, project_id, **filters),
        output_path,
    )


def export_owner_invoices_to_csv(
    company_id: int | None,
    project_id: int,
    prime_contract_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export owner invoices/payment applications to a CSV file."""
    return write_owner_invoices_csv(
        list_owner_invoices(company_id, project_id, prime_contract_id, **filters),
        output_path,
    )


def export_owner_invoices_to_jsonl(
    company_id: int | None,
    project_id: int,
    prime_contract_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export owner invoices/payment applications to newline-delimited JSON."""
    return _write_jsonl(
        list_owner_invoices(company_id, project_id, prime_contract_id, **filters),
        output_path,
    )


def export_owner_invoice_line_items_to_csv(
    company_id: int | None,
    project_id: int,
    prime_contract_id: int,
    owner_invoice_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export owner invoice line items to a CSV file."""
    return write_owner_invoice_line_items_csv(
        list_owner_invoice_line_items(
            company_id,
            project_id,
            prime_contract_id,
            owner_invoice_id,
            **filters,
        ),
        output_path,
    )


def export_owner_invoice_line_items_to_jsonl(
    company_id: int | None,
    project_id: int,
    prime_contract_id: int,
    owner_invoice_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export owner invoice line items to newline-delimited JSON."""
    return _write_jsonl(
        list_owner_invoice_line_items(
            company_id,
            project_id,
            prime_contract_id,
            owner_invoice_id,
            **filters,
        ),
        output_path,
    )


def export_subcontractor_invoices_to_csv(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export subcontractor invoices/requisitions to a CSV file."""
    return write_subcontractor_invoices_csv(
        list_subcontractor_invoices(company_id, project_id, **filters),
        output_path,
    )


def export_subcontractor_invoices_to_jsonl(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export subcontractor invoices/requisitions to newline-delimited JSON."""
    return _write_jsonl(
        list_subcontractor_invoices(company_id, project_id, **filters),
        output_path,
    )


def export_requisition_contract_items_to_csv(
    company_id: int | None,
    project_id: int,
    requisition_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export requisition contract items to a CSV file."""
    return write_requisition_contract_items_csv(
        list_requisition_contract_items(company_id, project_id, requisition_id, **filters),
        output_path,
    )


def export_requisition_contract_items_to_jsonl(
    company_id: int | None,
    project_id: int,
    requisition_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export requisition contract items to newline-delimited JSON."""
    return _write_jsonl(
        list_requisition_contract_items(company_id, project_id, requisition_id, **filters),
        output_path,
    )


def export_requisition_contract_detail_items_to_csv(
    company_id: int | None,
    project_id: int,
    requisition_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export requisition contract detail items to a CSV file."""
    return write_requisition_contract_detail_items_csv(
        list_requisition_contract_detail_items(
            company_id,
            project_id,
            requisition_id,
            **filters,
        ),
        output_path,
    )


def export_requisition_contract_detail_items_to_jsonl(
    company_id: int | None,
    project_id: int,
    requisition_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export requisition contract detail items to newline-delimited JSON."""
    return _write_jsonl(
        list_requisition_contract_detail_items(
            company_id,
            project_id,
            requisition_id,
            **filters,
        ),
        output_path,
    )


def export_requisition_change_order_items_to_csv(
    company_id: int | None,
    project_id: int,
    requisition_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export requisition change order items to a CSV file."""
    return write_requisition_change_order_items_csv(
        list_requisition_change_order_items(company_id, project_id, requisition_id, **filters),
        output_path,
    )


def export_requisition_change_order_items_to_jsonl(
    company_id: int | None,
    project_id: int,
    requisition_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export requisition change order items to newline-delimited JSON."""
    return _write_jsonl(
        list_requisition_change_order_items(company_id, project_id, requisition_id, **filters),
        output_path,
    )


def export_contract_payments_to_csv(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export contract payments to a CSV file."""
    return write_contract_payments_csv(
        list_contract_payments(company_id, project_id, **filters),
        output_path,
    )


def export_contract_payments_to_jsonl(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export contract payments to newline-delimited JSON."""
    return _write_jsonl(list_contract_payments(company_id, project_id, **filters), output_path)


def export_billing_periods_to_csv(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export billing periods to a CSV file."""
    return write_billing_periods_csv(
        list_billing_periods(company_id, project_id, **filters),
        output_path,
    )


def export_billing_periods_to_jsonl(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export billing periods to newline-delimited JSON."""
    return _write_jsonl(list_billing_periods(company_id, project_id, **filters), output_path)


def export_cost_types_to_csv(
    company_id: int | None,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export company cost types to a CSV file."""
    return write_cost_types_csv(list_cost_types(company_id, **filters), output_path)


def export_cost_types_to_jsonl(
    company_id: int | None,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export company cost types to newline-delimited JSON."""
    return _write_jsonl(list_cost_types(company_id, **filters), output_path)


def export_tax_codes_to_csv(
    company_id: int | None,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export company tax codes to a CSV file."""
    return write_tax_codes_csv(list_tax_codes(company_id, **filters), output_path)


def export_tax_codes_to_jsonl(
    company_id: int | None,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export company tax codes to newline-delimited JSON."""
    return _write_jsonl(list_tax_codes(company_id, **filters), output_path)


def export_schedule_resource_assignments_to_csv(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export schedule resource assignments to a CSV file."""
    return write_schedule_resource_assignments_csv(
        list_schedule_resource_assignments(company_id, project_id, **filters),
        output_path,
    )


def export_schedule_resource_assignments_to_jsonl(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export schedule resource assignments to newline-delimited JSON."""
    return _write_jsonl(
        list_schedule_resource_assignments(company_id, project_id, **filters),
        output_path,
    )


def export_tasks_to_csv(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project tasks to a CSV file."""
    return write_tasks_csv(list_tasks(company_id, project_id, **filters), output_path)


def export_tasks_to_jsonl(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project tasks to newline-delimited JSON."""
    return _write_jsonl(list_tasks(company_id, project_id, **filters), output_path)


def export_task_requested_changes_to_csv(
    company_id: int | None,
    project_id: int,
    task_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export read-only task requested changes to a CSV file."""
    return write_task_requested_changes_csv(
        list_task_requested_changes(company_id, project_id, task_id, **filters),
        output_path,
    )


def export_task_requested_changes_to_jsonl(
    company_id: int | None,
    project_id: int,
    task_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export read-only task requested changes to newline-delimited JSON."""
    return _write_jsonl(
        list_task_requested_changes(company_id, project_id, task_id, **filters),
        output_path,
    )


def export_calendar_items_to_csv(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project calendar items to a CSV file."""
    return write_calendar_items_csv(
        list_calendar_items(company_id, project_id, **filters),
        output_path,
    )


def export_calendar_items_to_jsonl(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project calendar items to newline-delimited JSON."""
    return _write_jsonl(list_calendar_items(company_id, project_id, **filters), output_path)


def export_coordination_issues_to_csv(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project coordination issues to a CSV file."""
    return write_coordination_issues_csv(
        list_coordination_issues(company_id, project_id, **filters),
        output_path,
    )


def export_coordination_issues_to_jsonl(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project coordination issues to newline-delimited JSON."""
    return _write_jsonl(list_coordination_issues(company_id, project_id, **filters), output_path)


def export_coordination_issue_change_history_to_csv(
    company_id: int | None,
    project_id: int,
    coordination_issue_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export read-only coordination issue change history to a CSV file."""
    return write_coordination_issue_change_history_csv(
        list_coordination_issue_change_history(
            company_id,
            project_id,
            coordination_issue_id,
            **filters,
        ),
        output_path,
    )


def export_coordination_issue_change_history_to_jsonl(
    company_id: int | None,
    project_id: int,
    coordination_issue_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export read-only coordination issue change history to newline-delimited JSON."""
    return _write_jsonl(
        list_coordination_issue_change_history(
            company_id,
            project_id,
            coordination_issue_id,
            **filters,
        ),
        output_path,
    )


def export_coordination_issue_activity_feed_to_csv(
    company_id: int | None,
    project_id: int,
    coordination_issue_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export read-only coordination issue activity feed entries to a CSV file."""
    return write_coordination_issue_activity_feed_csv(
        list_coordination_issue_activity_feed(
            company_id,
            project_id,
            coordination_issue_id,
            **filters,
        ),
        output_path,
    )


def export_coordination_issue_activity_feed_to_jsonl(
    company_id: int | None,
    project_id: int,
    coordination_issue_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export read-only coordination issue activity feed entries to JSONL."""
    return _write_jsonl(
        list_coordination_issue_activity_feed(
            company_id,
            project_id,
            coordination_issue_id,
            **filters,
        ),
        output_path,
    )


def export_coordination_issue_filter_options_to_csv(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export read-only coordination issue filter options to a CSV file."""
    return write_coordination_issue_filter_options_csv(
        list_coordination_issue_filter_options(company_id, project_id, **filters),
        output_path,
    )


def export_coordination_issue_filter_options_to_jsonl(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export read-only coordination issue filter options to newline-delimited JSON."""
    return _write_jsonl(
        list_coordination_issue_filter_options(company_id, project_id, **filters),
        output_path,
    )


def export_forms_to_csv(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project forms to a CSV file."""
    return write_forms_csv(list_forms(company_id, project_id, **filters), output_path)


def export_forms_to_jsonl(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project forms to newline-delimited JSON."""
    return _write_jsonl(list_forms(company_id, project_id, **filters), output_path)


def export_form_templates_to_csv(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project form templates to a CSV file."""
    return write_form_templates_csv(
        list_form_templates(company_id, project_id, **filters),
        output_path,
    )


def export_form_templates_to_jsonl(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project form templates to newline-delimited JSON."""
    return _write_jsonl(list_form_templates(company_id, project_id, **filters), output_path)


def export_action_plans_to_csv(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project action plans to a CSV file."""
    return write_action_plans_csv(
        list_action_plans(company_id, project_id, **filters),
        output_path,
    )


def export_action_plans_to_jsonl(
    company_id: int | None,
    project_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export project action plans to newline-delimited JSON."""
    return _write_jsonl(list_action_plans(company_id, project_id, **filters), output_path)


def export_action_plan_change_history_to_csv(
    company_id: int | None,
    project_id: int,
    action_plan_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export read-only action plan change history events to a CSV file."""
    return write_action_plan_change_history_csv(
        list_action_plan_change_history_events(company_id, project_id, action_plan_id, **filters),
        output_path,
    )


def export_action_plan_change_history_to_jsonl(
    company_id: int | None,
    project_id: int,
    action_plan_id: int,
    output_path: Path | str,
    **filters: Any,
) -> Path:
    """Export read-only action plan change history events to newline-delimited JSON."""
    return _write_jsonl(
        list_action_plan_change_history_events(company_id, project_id, action_plan_id, **filters),
        output_path,
    )


def write_rfis_csv(rfis: Sequence[RFI], output_path: Path | str) -> Path:
    """Write already-loaded RFIs to a CSV file."""
    return _write_csv(rfis, output_path, RFI_CSV_HEADERS, _rfi_row)


def write_submittals_csv(submittals: Sequence[Submittal], output_path: Path | str) -> Path:
    """Write already-loaded submittals to a CSV file."""
    return _write_csv(submittals, output_path, SUBMITTAL_CSV_HEADERS, _submittal_row)


def write_documents_csv(documents: Sequence[Document], output_path: Path | str) -> Path:
    """Write already-loaded documents to a CSV file."""
    return _write_csv(documents, output_path, DOCUMENT_CSV_HEADERS, _document_row)


def write_observations_csv(observations: Sequence[Observation], output_path: Path | str) -> Path:
    """Write already-loaded observations to a CSV file."""
    return _write_csv(observations, output_path, OBSERVATION_CSV_HEADERS, _observation_row)


def write_punch_items_csv(punch_items: Sequence[PunchItem], output_path: Path | str) -> Path:
    """Write already-loaded punch items to a CSV file."""
    return _write_csv(punch_items, output_path, PUNCH_ITEM_CSV_HEADERS, _punch_item_row)


def write_correspondences_csv(
    correspondences: Sequence[Correspondence],
    output_path: Path | str,
) -> Path:
    """Write already-loaded correspondences to a CSV file."""
    return _write_csv(
        correspondences,
        output_path,
        CORRESPONDENCE_CSV_HEADERS,
        _correspondence_row,
    )


def write_meetings_csv(meetings: Sequence[Meeting], output_path: Path | str) -> Path:
    """Write already-loaded meetings to a CSV file."""
    return _write_csv(meetings, output_path, MEETING_CSV_HEADERS, _meeting_row)


def write_inspections_csv(
    inspections: Sequence[Inspection],
    output_path: Path | str,
) -> Path:
    """Write already-loaded inspections to a CSV file."""
    return _write_csv(inspections, output_path, INSPECTION_CSV_HEADERS, _inspection_row)


def write_incidents_csv(incidents: Sequence[Incident], output_path: Path | str) -> Path:
    """Write already-loaded incidents to a CSV file."""
    return _write_csv(incidents, output_path, INCIDENT_CSV_HEADERS, _incident_row)


def write_company_users_csv(users: Sequence[CompanyUser], output_path: Path | str) -> Path:
    """Write already-loaded company users to a CSV file."""
    return _write_csv(users, output_path, COMPANY_USER_CSV_HEADERS, _company_user_row)


def write_project_users_csv(users: Sequence[ProjectUser], output_path: Path | str) -> Path:
    """Write already-loaded project users to a CSV file."""
    return _write_csv(users, output_path, PROJECT_USER_CSV_HEADERS, _project_user_row)


def write_vendors_csv(vendors: Sequence[Vendor], output_path: Path | str) -> Path:
    """Write already-loaded vendors to a CSV file."""
    return _write_csv(vendors, output_path, VENDOR_CSV_HEADERS, _vendor_row)


def write_departments_csv(
    departments: Sequence[Department],
    output_path: Path | str,
) -> Path:
    """Write already-loaded departments to a CSV file."""
    return _write_csv(departments, output_path, DEPARTMENT_CSV_HEADERS, _department_row)


def write_distribution_groups_csv(
    groups: Sequence[DistributionGroup],
    output_path: Path | str,
) -> Path:
    """Write already-loaded distribution groups to a CSV file."""
    return _write_csv(
        groups,
        output_path,
        DISTRIBUTION_GROUP_CSV_HEADERS,
        _distribution_group_row,
    )


def write_locations_csv(locations: Sequence[Location], output_path: Path | str) -> Path:
    """Write already-loaded locations to a CSV file."""
    return _write_csv(locations, output_path, LOCATION_CSV_HEADERS, _location_row)


def write_change_events_csv(
    items: Sequence[ChangeEvent],
    output_path: Path | str,
) -> Path:
    """Write already-loaded change events to a CSV file."""
    return _write_csv(items, output_path, FINANCIAL_CSV_HEADERS, _financial_row)


def write_prime_change_orders_csv(
    items: Sequence[PrimeChangeOrder],
    output_path: Path | str,
) -> Path:
    """Write already-loaded prime change orders to a CSV file."""
    return _write_csv(items, output_path, FINANCIAL_CSV_HEADERS, _financial_row)


def write_commitment_change_orders_csv(
    items: Sequence[CommitmentChangeOrder],
    output_path: Path | str,
) -> Path:
    """Write already-loaded commitment change orders to a CSV file."""
    return _write_csv(items, output_path, FINANCIAL_CSV_HEADERS, _financial_row)


def write_change_order_packages_csv(
    items: Sequence[ChangeOrderPackage],
    output_path: Path | str,
) -> Path:
    """Write already-loaded change order packages to a CSV file."""
    return _write_csv(items, output_path, FINANCIAL_CSV_HEADERS, _financial_row)


def write_direct_costs_csv(items: Sequence[DirectCost], output_path: Path | str) -> Path:
    """Write already-loaded direct costs to a CSV file."""
    return _write_csv(items, output_path, FINANCIAL_CSV_HEADERS, _financial_row)


def write_budget_views_csv(items: Sequence[BudgetView], output_path: Path | str) -> Path:
    """Write already-loaded budget views to a CSV file."""
    return _write_csv(items, output_path, BUDGET_VIEW_CSV_HEADERS, _budget_view_row)


def write_budget_details_csv(
    items: Sequence[BudgetDetailRow],
    output_path: Path | str,
) -> Path:
    """Write already-loaded budget detail rows to a CSV file."""
    return _write_csv(items, output_path, BUDGET_ROW_CSV_HEADERS, _budget_row)


def write_budget_summary_rows_csv(
    items: Sequence[BudgetSummaryRow],
    output_path: Path | str,
) -> Path:
    """Write already-loaded budget summary rows to a CSV file."""
    return _write_csv(items, output_path, BUDGET_ROW_CSV_HEADERS, _budget_row)


def write_cost_codes_csv(items: Sequence[object], output_path: Path | str) -> Path:
    """Write already-loaded cost codes to a CSV file."""
    return _write_csv(items, output_path, COST_CODE_CSV_HEADERS, _cost_code_row)


def write_commitments_csv(items: Sequence[Commitment], output_path: Path | str) -> Path:
    """Write already-loaded commitments to a CSV file."""
    return _write_csv(items, output_path, FINANCIAL_CSV_HEADERS, _financial_row)


def write_prime_contracts_csv(
    items: Sequence[PrimeContract],
    output_path: Path | str,
) -> Path:
    """Write already-loaded prime contracts to a CSV file."""
    return _write_csv(items, output_path, FINANCIAL_CSV_HEADERS, _financial_row)


def write_prime_contract_line_items_csv(
    items: Sequence[PrimeContractLineItem],
    output_path: Path | str,
) -> Path:
    """Write already-loaded prime contract line items to a CSV file."""
    return _write_csv(items, output_path, FINANCIAL_CSV_HEADERS, _financial_row)


def write_commitment_contracts_csv(
    items: Sequence[CommitmentContract],
    output_path: Path | str,
) -> Path:
    """Write already-loaded commitment contracts to a CSV file."""
    return _write_csv(items, output_path, FINANCIAL_CSV_HEADERS, _financial_row)


def write_purchase_order_contracts_csv(
    items: Sequence[PurchaseOrderContract],
    output_path: Path | str,
) -> Path:
    """Write already-loaded purchase order contracts to a CSV file."""
    return _write_csv(items, output_path, FINANCIAL_CSV_HEADERS, _financial_row)


def write_work_order_contracts_csv(
    items: Sequence[WorkOrderContract],
    output_path: Path | str,
) -> Path:
    """Write already-loaded work order contracts to a CSV file."""
    return _write_csv(items, output_path, FINANCIAL_CSV_HEADERS, _financial_row)


def write_owner_invoices_csv(
    items: Sequence[OwnerInvoice],
    output_path: Path | str,
) -> Path:
    """Write already-loaded owner invoices to a CSV file."""
    return _write_csv(items, output_path, FINANCIAL_CSV_HEADERS, _financial_row)


def write_owner_invoice_line_items_csv(
    items: Sequence[OwnerInvoiceLineItem],
    output_path: Path | str,
) -> Path:
    """Write already-loaded owner invoice line items to a CSV file."""
    return _write_csv(items, output_path, FINANCIAL_CSV_HEADERS, _financial_row)


def write_subcontractor_invoices_csv(
    items: Sequence[SubcontractorInvoice],
    output_path: Path | str,
) -> Path:
    """Write already-loaded subcontractor invoices to a CSV file."""
    return _write_csv(items, output_path, FINANCIAL_CSV_HEADERS, _financial_row)


def write_requisition_contract_items_csv(
    items: Sequence[RequisitionContractItem],
    output_path: Path | str,
) -> Path:
    """Write already-loaded requisition contract items to a CSV file."""
    return _write_csv(items, output_path, FINANCIAL_CSV_HEADERS, _financial_row)


def write_requisition_contract_detail_items_csv(
    items: Sequence[RequisitionContractDetailItem],
    output_path: Path | str,
) -> Path:
    """Write already-loaded requisition contract detail items to a CSV file."""
    return _write_csv(items, output_path, FINANCIAL_CSV_HEADERS, _financial_row)


def write_requisition_change_order_items_csv(
    items: Sequence[RequisitionChangeOrderItem],
    output_path: Path | str,
) -> Path:
    """Write already-loaded requisition change order items to a CSV file."""
    return _write_csv(items, output_path, FINANCIAL_CSV_HEADERS, _financial_row)


def write_contract_payments_csv(
    items: Sequence[ContractPayment],
    output_path: Path | str,
) -> Path:
    """Write already-loaded contract payments to a CSV file."""
    return _write_csv(items, output_path, FINANCIAL_CSV_HEADERS, _financial_row)


def write_billing_periods_csv(
    items: Sequence[BillingPeriod],
    output_path: Path | str,
) -> Path:
    """Write already-loaded billing periods to a CSV file."""
    return _write_csv(items, output_path, FINANCIAL_CSV_HEADERS, _financial_row)


def write_cost_types_csv(items: Sequence[CostType], output_path: Path | str) -> Path:
    """Write already-loaded cost types to a CSV file."""
    return _write_csv(items, output_path, COST_CODE_CSV_HEADERS, _cost_code_row)


def write_tax_codes_csv(items: Sequence[TaxCode], output_path: Path | str) -> Path:
    """Write already-loaded tax codes to a CSV file."""
    return _write_csv(items, output_path, COST_CODE_CSV_HEADERS, _cost_code_row)


def write_schedule_resource_assignments_csv(
    items: Sequence[ScheduleResourceAssignment],
    output_path: Path | str,
) -> Path:
    """Write already-loaded schedule resource assignments to a CSV file."""
    return _write_csv(items, output_path, FINANCIAL_CSV_HEADERS, _financial_row)


def write_tasks_csv(items: Sequence[Task], output_path: Path | str) -> Path:
    """Write already-loaded tasks to a CSV file."""
    return _write_csv(items, output_path, FINANCIAL_CSV_HEADERS, _financial_row)


def write_task_requested_changes_csv(
    items: Sequence[TaskRequestedChange],
    output_path: Path | str,
) -> Path:
    """Write already-loaded task requested changes to a CSV file."""
    return _write_csv(items, output_path, FINANCIAL_CSV_HEADERS, _financial_row)


def write_calendar_items_csv(items: Sequence[CalendarItem], output_path: Path | str) -> Path:
    """Write already-loaded calendar items to a CSV file."""
    return _write_csv(items, output_path, FINANCIAL_CSV_HEADERS, _financial_row)


def write_coordination_issues_csv(
    items: Sequence[CoordinationIssue],
    output_path: Path | str,
) -> Path:
    """Write already-loaded coordination issues to a CSV file."""
    return _write_csv(items, output_path, FINANCIAL_CSV_HEADERS, _financial_row)


def write_coordination_issue_change_history_csv(
    items: Sequence[CoordinationIssueChangeHistoryEvent],
    output_path: Path | str,
) -> Path:
    """Write already-loaded coordination issue change history to a CSV file."""
    return _write_csv(items, output_path, FINANCIAL_CSV_HEADERS, _financial_row)


def write_coordination_issue_activity_feed_csv(
    items: Sequence[CoordinationIssueActivity],
    output_path: Path | str,
) -> Path:
    """Write already-loaded coordination issue activity feed entries to a CSV file."""
    return _write_csv(items, output_path, FINANCIAL_CSV_HEADERS, _financial_row)


def write_coordination_issue_filter_options_csv(
    items: Sequence[CoordinationIssueFilterOption],
    output_path: Path | str,
) -> Path:
    """Write already-loaded coordination issue filter options to a CSV file."""
    return _write_csv(items, output_path, FINANCIAL_CSV_HEADERS, _financial_row)


def write_forms_csv(items: Sequence[Form], output_path: Path | str) -> Path:
    """Write already-loaded forms to a CSV file."""
    return _write_csv(items, output_path, FINANCIAL_CSV_HEADERS, _financial_row)


def write_form_templates_csv(items: Sequence[FormTemplate], output_path: Path | str) -> Path:
    """Write already-loaded form templates to a CSV file."""
    return _write_csv(items, output_path, FINANCIAL_CSV_HEADERS, _financial_row)


def write_action_plans_csv(items: Sequence[ActionPlan], output_path: Path | str) -> Path:
    """Write already-loaded action plans to a CSV file."""
    return _write_csv(items, output_path, FINANCIAL_CSV_HEADERS, _financial_row)


def write_action_plan_change_history_csv(
    items: Sequence[ActionPlanChangeHistoryEvent],
    output_path: Path | str,
) -> Path:
    """Write already-loaded action plan change history events to a CSV file."""
    return _write_csv(items, output_path, FINANCIAL_CSV_HEADERS, _financial_row)


def _load_rfis(
    project_id: int,
    *,
    status: str | None,
    updated_after: str | None,
    updated_before: str | None,
    created_after: str | None,
    created_before: str | None,
    params: Mapping[str, Any] | None,
    **extra_params: Any,
) -> list[RFI]:
    """Load RFIs using the existing service layer."""
    return list_rfis(
        project_id,
        status=status,
        updated_after=updated_after,
        updated_before=updated_before,
        created_after=created_after,
        created_before=created_before,
        params=params,
        **extra_params,
    )


def _load_submittals(
    project_id: int,
    *,
    status: str | None,
    updated_after: str | None,
    updated_before: str | None,
    created_after: str | None,
    created_before: str | None,
    params: Mapping[str, Any] | None,
    **extra_params: Any,
) -> list[Submittal]:
    """Load submittals using the existing service layer."""
    return list_submittals(
        project_id,
        status=status,
        updated_after=updated_after,
        updated_before=updated_before,
        created_after=created_after,
        created_before=created_before,
        params=params,
        **extra_params,
    )


def _write_csv(
    items: Sequence[object],
    output_path: Path | str,
    headers: list[str],
    row_builder: Callable[[object], dict[str, object]],
) -> Path:
    """Write workflow items to CSV and return the saved path."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=headers)
        writer.writeheader()
        for item in items:
            writer.writerow(row_builder(item))

    return path


def _write_jsonl(items: Sequence[object], output_path: Path | str) -> Path:
    """Write workflow items to newline-delimited JSON and return the path."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file_handle:
        for item in items:
            file_handle.write(json.dumps(model_to_dict(item), default=str, sort_keys=True))
            file_handle.write("\n")

    return path


def _rfi_row(rfi: object) -> dict[str, object]:
    """Convert one RFI model into a CSV row."""
    questions = get_value(rfi, "questions") or []
    question_count = len(questions) if isinstance(questions, Sequence) else 0
    return {
        "id": scalar_text(get_value(rfi, "id")),
        "number": scalar_text(get_value(rfi, "number")),
        "subject": item_title(rfi),
        "status": scalar_text(get_value(rfi, "status")),
        "created_at": scalar_text(get_value(rfi, "created_at")),
        "updated_at": scalar_text(get_value(rfi, "updated_at")),
        "due_date": scalar_text(get_value(rfi, "due_date")),
        "ball_in_court": scalar_text(get_value(rfi, "ball_in_court")),
        "responsible_contractor": scalar_text(get_value(rfi, "responsible_contractor")),
        "assignee": scalar_text(get_value(rfi, "assignee")),
        "question_count": question_count,
        "attachment_count": attachment_count(rfi, item_type="rfi"),
    }


def _submittal_row(submittal: object) -> dict[str, object]:
    """Convert one submittal model into a CSV row."""
    return {
        "id": scalar_text(get_value(submittal, "id")),
        "number": scalar_text(get_value(submittal, "number")),
        "title": item_title(submittal),
        "status": scalar_text(get_value(submittal, "status")),
        "created_at": scalar_text(get_value(submittal, "created_at")),
        "updated_at": scalar_text(get_value(submittal, "updated_at")),
        "due_date": scalar_text(get_value(submittal, "due_date")),
        "ball_in_court": scalar_text(get_value(submittal, "ball_in_court")),
        "responsible_contractor": scalar_text(get_value(submittal, "responsible_contractor")),
        "attachment_count": attachment_count(submittal, item_type="submittal"),
    }


def _document_row(document: object) -> dict[str, object]:
    """Convert one document model into a CSV row."""
    return {
        "id": scalar_text(get_value(document, "id")),
        "name": scalar_text(get_value(document, "name")),
        "filename": scalar_text(get_value(document, "filename", "file_name")),
        "folder_id": scalar_text(get_value(document, "folder_id")),
        "content_type": scalar_text(get_value(document, "content_type")),
        "file_size": scalar_text(get_value(document, "file_size")),
        "created_at": scalar_text(get_value(document, "created_at")),
        "updated_at": scalar_text(get_value(document, "updated_at")),
        "download_url": scalar_text(get_value(document, "download_url", "url")),
    }


def _observation_row(observation: object) -> dict[str, object]:
    """Convert one observation model into a CSV row."""
    return {
        "id": scalar_text(get_value(observation, "id")),
        "number": scalar_text(get_value(observation, "number")),
        "title": item_title(observation),
        "status": scalar_text(get_value(observation, "status")),
        "type": scalar_text(get_value(observation, "type", "observation_type")),
        "priority": scalar_text(get_value(observation, "priority")),
        "created_at": scalar_text(get_value(observation, "created_at")),
        "updated_at": scalar_text(get_value(observation, "updated_at")),
        "due_date": scalar_text(get_value(observation, "due_date")),
        "assignee": scalar_text(get_value(observation, "assignee")),
        "created_by": scalar_text(get_value(observation, "created_by")),
        "attachment_count": attachment_count(observation, item_type="observation"),
    }


def _punch_item_row(punch_item: object) -> dict[str, object]:
    """Convert one punch item model into a CSV row."""
    return {
        "id": scalar_text(get_value(punch_item, "id")),
        "number": scalar_text(get_value(punch_item, "number")),
        "title": item_title(punch_item),
        "status": scalar_text(get_value(punch_item, "status")),
        "type": scalar_text(get_value(punch_item, "type")),
        "priority": scalar_text(get_value(punch_item, "priority")),
        "created_at": scalar_text(get_value(punch_item, "created_at")),
        "updated_at": scalar_text(get_value(punch_item, "updated_at")),
        "due_date": scalar_text(get_value(punch_item, "due_date")),
        "assignee": scalar_text(get_value(punch_item, "assignee", "assigned_to")),
        "created_by": scalar_text(get_value(punch_item, "created_by")),
        "attachment_count": attachment_count(punch_item, item_type="punch_item"),
    }


def _correspondence_row(correspondence: object) -> dict[str, object]:
    """Convert one correspondence model into a CSV row."""
    return {
        "id": scalar_text(get_value(correspondence, "id")),
        "number": scalar_text(get_value(correspondence, "number")),
        "subject": scalar_text(get_value(correspondence, "subject")),
        "title": item_title(correspondence),
        "status": scalar_text(get_value(correspondence, "status")),
        "generic_tool_id": scalar_text(get_value(correspondence, "generic_tool_id")),
        "created_at": scalar_text(get_value(correspondence, "created_at")),
        "updated_at": scalar_text(get_value(correspondence, "updated_at")),
        "due_date": scalar_text(get_value(correspondence, "due_date")),
        "assignee": scalar_text(get_value(correspondence, "assignee")),
        "created_by": scalar_text(get_value(correspondence, "created_by")),
        "attachment_count": attachment_count(correspondence, item_type="correspondence"),
    }


def _meeting_row(meeting: object) -> dict[str, object]:
    """Convert one meeting model into a CSV row."""
    return {
        "id": scalar_text(get_value(meeting, "id")),
        "number": scalar_text(get_value(meeting, "number")),
        "title": item_title(meeting),
        "status": scalar_text(get_value(meeting, "status")),
        "meeting_date": scalar_text(get_value(meeting, "meeting_date", "date")),
        "location": scalar_text(get_value(meeting, "location")),
        "created_at": scalar_text(get_value(meeting, "created_at")),
        "updated_at": scalar_text(get_value(meeting, "updated_at")),
        "created_by": scalar_text(get_value(meeting, "created_by")),
        "attachment_count": attachment_count(meeting, item_type="meeting"),
    }


def _inspection_row(inspection: object) -> dict[str, object]:
    """Convert one inspection model into a CSV row."""
    items = get_value(inspection, "items", "checklist_items") or []
    item_count = len(items) if isinstance(items, Sequence) else 0
    return {
        "id": scalar_text(get_value(inspection, "id")),
        "number": scalar_text(get_value(inspection, "number")),
        "title": item_title(inspection),
        "status": scalar_text(get_value(inspection, "status")),
        "type": scalar_text(get_value(inspection, "inspection_type", "checklist_type", "type")),
        "created_at": scalar_text(get_value(inspection, "created_at")),
        "updated_at": scalar_text(get_value(inspection, "updated_at")),
        "due_date": scalar_text(get_value(inspection, "due_date")),
        "assignee": scalar_text(get_value(inspection, "assignee")),
        "created_by": scalar_text(get_value(inspection, "created_by")),
        "item_count": item_count,
        "attachment_count": attachment_count(inspection, item_type="inspection"),
    }


def _incident_row(incident: object) -> dict[str, object]:
    """Convert one incident model into a CSV row."""
    return {
        "id": scalar_text(get_value(incident, "id")),
        "number": scalar_text(get_value(incident, "number")),
        "title": item_title(incident),
        "status": scalar_text(get_value(incident, "status")),
        "type": scalar_text(get_value(incident, "incident_type", "type")),
        "severity": scalar_text(get_value(incident, "severity")),
        "incident_date": scalar_text(get_value(incident, "incident_date", "occurred_at")),
        "location": scalar_text(get_value(incident, "location")),
        "created_at": scalar_text(get_value(incident, "created_at")),
        "updated_at": scalar_text(get_value(incident, "updated_at")),
        "reported_by": scalar_text(get_value(incident, "reported_by")),
        "created_by": scalar_text(get_value(incident, "created_by")),
        "attachment_count": attachment_count(incident, item_type="incident"),
    }


def _company_user_row(user: object) -> dict[str, object]:
    """Convert one company user model into a CSV row."""
    return {
        "id": scalar_text(get_value(user, "id")),
        "name": scalar_text(get_value(user, "name")),
        "email": scalar_text(get_value(user, "email", "email_address")),
        "login": scalar_text(get_value(user, "login")),
        "active": scalar_text(get_value(user, "active")),
        "job_title": scalar_text(get_value(user, "job_title")),
        "phone": scalar_text(get_value(user, "phone", "business_phone", "mobile_phone")),
        "vendor": scalar_text(get_value(user, "vendor")),
        "created_at": scalar_text(get_value(user, "created_at")),
        "updated_at": scalar_text(get_value(user, "updated_at")),
    }


def _project_user_row(user: object) -> dict[str, object]:
    """Convert one project user model into a CSV row."""
    return {
        "id": scalar_text(get_value(user, "id")),
        "name": scalar_text(get_value(user, "name")),
        "email": scalar_text(get_value(user, "email", "email_address")),
        "login": scalar_text(get_value(user, "login")),
        "active": scalar_text(get_value(user, "active")),
        "job_title": scalar_text(get_value(user, "job_title")),
        "phone": scalar_text(get_value(user, "phone", "business_phone", "mobile_phone")),
        "project_id": scalar_text(get_value(user, "project_id")),
        "permission_template": scalar_text(get_value(user, "permission_template")),
        "role": scalar_text(get_value(user, "role")),
        "created_at": scalar_text(get_value(user, "created_at")),
        "updated_at": scalar_text(get_value(user, "updated_at")),
    }


def _vendor_row(vendor: object) -> dict[str, object]:
    """Convert one vendor model into a CSV row."""
    return {
        "id": scalar_text(get_value(vendor, "id")),
        "name": scalar_text(get_value(vendor, "name")),
        "legal_name": scalar_text(get_value(vendor, "legal_name")),
        "trade_name": scalar_text(get_value(vendor, "trade_name")),
        "vendor_number": scalar_text(get_value(vendor, "vendor_number", "number")),
        "active": scalar_text(get_value(vendor, "active")),
        "phone": scalar_text(get_value(vendor, "phone")),
        "email": scalar_text(get_value(vendor, "email")),
        "website": scalar_text(get_value(vendor, "website")),
        "company_id": scalar_text(get_value(vendor, "company_id")),
        "created_at": scalar_text(get_value(vendor, "created_at")),
        "updated_at": scalar_text(get_value(vendor, "updated_at")),
    }


def _department_row(department: object) -> dict[str, object]:
    """Convert one department model into a CSV row."""
    return {
        "id": scalar_text(get_value(department, "id")),
        "name": scalar_text(get_value(department, "name")),
        "code": scalar_text(get_value(department, "code")),
        "description": scalar_text(get_value(department, "description")),
        "active": scalar_text(get_value(department, "active")),
        "company_id": scalar_text(get_value(department, "company_id")),
        "created_at": scalar_text(get_value(department, "created_at")),
        "updated_at": scalar_text(get_value(department, "updated_at")),
    }


def _distribution_group_row(group: object) -> dict[str, object]:
    """Convert one distribution group model into a CSV row."""
    users = get_value(group, "users") or []
    members = get_value(group, "members") or []
    member_count = 0
    if isinstance(users, Sequence):
        member_count = len(users)
    if member_count == 0 and isinstance(members, Sequence):
        member_count = len(members)
    return {
        "id": scalar_text(get_value(group, "id")),
        "name": scalar_text(get_value(group, "name")),
        "description": scalar_text(get_value(group, "description")),
        "project_id": scalar_text(get_value(group, "project_id")),
        "member_count": member_count,
        "created_at": scalar_text(get_value(group, "created_at")),
        "updated_at": scalar_text(get_value(group, "updated_at")),
    }


def _location_row(location: object) -> dict[str, object]:
    """Convert one location model into a CSV row."""
    parent = get_value(location, "parent")
    parent_id = get_value(location, "parent_id")
    if parent_id is None and isinstance(parent, Mapping):
        parent_id = parent.get("id")
    return {
        "id": scalar_text(get_value(location, "id")),
        "name": scalar_text(get_value(location, "name")),
        "full_name": scalar_text(get_value(location, "full_name")),
        "path": scalar_text(get_value(location, "path")),
        "code": scalar_text(get_value(location, "code")),
        "parent_id": scalar_text(parent_id),
        "project_id": scalar_text(get_value(location, "project_id")),
        "created_at": scalar_text(get_value(location, "created_at")),
        "updated_at": scalar_text(get_value(location, "updated_at")),
    }


def _financial_row(item: object) -> dict[str, object]:
    """Convert one financial model into a compact CSV row."""
    return {
        "id": scalar_text(get_value(item, "id")),
        "number": scalar_text(get_value(item, "number")),
        "title": scalar_text(get_value(item, "title")),
        "name": scalar_text(get_value(item, "name")),
        "status": scalar_text(get_value(item, "status")),
        "amount": scalar_text(get_value(item, "amount", "estimated_cost")),
        "created_at": scalar_text(get_value(item, "created_at")),
        "updated_at": scalar_text(get_value(item, "updated_at")),
    }


def _budget_view_row(item: object) -> dict[str, object]:
    """Convert one budget view model into a CSV row."""
    return {
        "id": scalar_text(get_value(item, "id")),
        "name": scalar_text(get_value(item, "name")),
        "description": scalar_text(get_value(item, "description")),
        "project_id": scalar_text(get_value(item, "project_id")),
        "created_at": scalar_text(get_value(item, "created_at")),
        "updated_at": scalar_text(get_value(item, "updated_at")),
    }


def _budget_row(item: object) -> dict[str, object]:
    """Convert one budget row model into a CSV row."""
    return {
        "id": scalar_text(get_value(item, "id")),
        "name": scalar_text(get_value(item, "name")),
        "cost_code": scalar_text(get_value(item, "cost_code")),
        "cost_type": scalar_text(get_value(item, "cost_type")),
        "project_id": scalar_text(get_value(item, "project_id")),
    }


def _cost_code_row(item: object) -> dict[str, object]:
    """Convert one cost code model into a CSV row."""
    return {
        "id": scalar_text(get_value(item, "id")),
        "code": scalar_text(get_value(item, "code")),
        "name": scalar_text(get_value(item, "name")),
        "full_code": scalar_text(get_value(item, "full_code")),
        "description": scalar_text(get_value(item, "description")),
        "company_id": scalar_text(get_value(item, "company_id")),
    }
