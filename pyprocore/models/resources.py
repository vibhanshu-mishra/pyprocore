"""Typed Pydantic models for common Procore resources."""

from __future__ import annotations

from typing import Any

from pydantic import Field, HttpUrl

from pyprocore.models.base import ProcoreModel


class Status(ProcoreModel):
    """Status metadata returned by Procore resources."""

    id: int | None = None
    name: str | None = None
    status: str | None = None


class User(ProcoreModel):
    """Procore user summary."""

    id: int | None = None
    name: str | None = None
    login: str | None = None
    email_address: str | None = None


class Attachment(ProcoreModel):
    """Attachment metadata with a signed download URL."""

    id: int | None = None
    name: str | None = None
    filename: str | None = None
    file_name: str | None = None
    url: str | HttpUrl | None = None
    content_type: str | None = None


class Company(ProcoreModel):
    """Procore company resource."""

    id: int
    name: str | None = None


class Project(ProcoreModel):
    """Procore project resource."""

    id: int
    name: str | None = None
    project_number: str | None = None
    active: bool | None = None
    company: Company | None = None


class ProjectTool(ProcoreModel):
    """Flexible read-only Project Tool metadata resource."""

    id: int | None = None
    name: str | None = None
    title: str | None = None
    label: str | None = None
    slug: str | None = None
    active: bool | None = None
    enabled: bool | None = None
    configurable: bool | None = None
    mobile: bool | None = None
    tool_type: str | None = None
    type: str | None = None


class RFIQuestion(ProcoreModel):
    """Question nested under a Procore RFI."""

    id: int | None = None
    body: str | None = None
    plain_text_body: str | None = None
    attachments: list[Attachment] = Field(default_factory=list)


class RFI(ProcoreModel):
    """Procore RFI resource."""

    id: int
    number: str | int | None = None
    subject: str | None = None
    status: Status | str | None = None
    assignee: User | None = None
    created_by: User | None = None
    questions: list[RFIQuestion] = Field(default_factory=list)


class Submittal(ProcoreModel):
    """Procore submittal resource."""

    id: int
    number: str | int | None = None
    title: str | None = None
    status: Status | str | None = None
    responsible_contractor: dict[str, Any] | None = None
    attachments: list[Attachment] = Field(default_factory=list)


class Observation(ProcoreModel):
    """Flexible Procore observation item resource."""

    id: int | None = None
    number: str | int | None = None
    title: str | None = None
    name: str | None = None
    description: str | None = None
    status: Status | str | None = None
    type: str | None = None
    observation_type: str | dict[str, Any] | None = None
    priority: str | Status | None = None
    assignee: User | dict[str, Any] | None = None
    created_by: User | dict[str, Any] | None = None
    due_date: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    attachments: list[Attachment] = Field(default_factory=list)


class PunchItem(ProcoreModel):
    """Flexible Procore punch item resource."""

    id: int | None = None
    number: str | int | None = None
    title: str | None = None
    name: str | None = None
    description: str | None = None
    status: Status | str | None = None
    type: str | None = None
    priority: str | Status | None = None
    assignee: User | dict[str, Any] | None = None
    assigned_to: User | dict[str, Any] | None = None
    created_by: User | dict[str, Any] | None = None
    due_date: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    attachments: list[Attachment] = Field(default_factory=list)


class GenericTool(ProcoreModel):
    """Flexible Procore Generic Tool metadata resource."""

    id: int | None = None
    name: str | None = None
    title: str | None = None
    tool_type: str | None = None
    type: str | None = None
    slug: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class Correspondence(ProcoreModel):
    """Flexible Procore correspondence or Generic Tool Item resource."""

    id: int | None = None
    number: str | int | None = None
    subject: str | None = None
    title: str | None = None
    name: str | None = None
    description: str | None = None
    status: Status | str | None = None
    generic_tool_id: int | None = None
    generic_tool: GenericTool | dict[str, Any] | None = None
    assignee: User | dict[str, Any] | None = None
    created_by: User | dict[str, Any] | None = None
    due_date: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    attachments: list[Attachment] = Field(default_factory=list)


class Meeting(ProcoreModel):
    """Flexible Procore meeting resource."""

    id: int | None = None
    number: str | int | None = None
    title: str | None = None
    name: str | None = None
    description: str | None = None
    status: Status | str | None = None
    meeting_date: str | None = None
    date: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    location: str | dict[str, Any] | None = None
    created_by: User | dict[str, Any] | None = None
    created_at: str | None = None
    updated_at: str | None = None
    attachments: list[Attachment] = Field(default_factory=list)


class InspectionItem(ProcoreModel):
    """Flexible inspection checklist item resource."""

    id: int | None = None
    number: str | int | None = None
    title: str | None = None
    name: str | None = None
    description: str | None = None
    status: Status | str | None = None
    response: str | dict[str, Any] | None = None
    comments: str | None = None
    attachments: list[Attachment] = Field(default_factory=list)


class Inspection(ProcoreModel):
    """Flexible Procore inspection/checklist resource.

    Some Procore APIs expose inspections through checklist/checklists
    terminology. PyProcore keeps the public model name user-friendly while
    preserving unknown checklist payload fields.
    """

    id: int | None = None
    number: str | int | None = None
    title: str | None = None
    name: str | None = None
    description: str | None = None
    status: Status | str | None = None
    type: str | dict[str, Any] | None = None
    inspection_type: str | dict[str, Any] | None = None
    checklist_type: str | dict[str, Any] | None = None
    assignee: User | dict[str, Any] | None = None
    created_by: User | dict[str, Any] | None = None
    due_date: str | None = None
    performed_on: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    items: list[InspectionItem] = Field(default_factory=list)
    checklist_items: list[InspectionItem] = Field(default_factory=list)
    attachments: list[Attachment] = Field(default_factory=list)


class Incident(ProcoreModel):
    """Flexible Procore incident resource."""

    id: int | None = None
    number: str | int | None = None
    title: str | None = None
    name: str | None = None
    description: str | None = None
    status: Status | str | None = None
    type: str | dict[str, Any] | None = None
    incident_type: str | dict[str, Any] | None = None
    severity: str | Status | None = None
    location: str | dict[str, Any] | None = None
    occurred_at: str | None = None
    incident_date: str | None = None
    reported_by: User | dict[str, Any] | None = None
    created_by: User | dict[str, Any] | None = None
    created_at: str | None = None
    updated_at: str | None = None
    attachments: list[Attachment] = Field(default_factory=list)


class IncidentConfiguration(ProcoreModel):
    """Flexible Procore project incident configuration resource."""

    id: int | None = None
    project_id: int | None = None
    enabled: bool | None = None
    incident_types: list[dict[str, Any]] = Field(default_factory=list)
    statuses: list[dict[str, Any]] = Field(default_factory=list)
    severity_levels: list[dict[str, Any]] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None


class CompanyUser(ProcoreModel):
    """Flexible Procore company directory user resource."""

    id: int | None = None
    name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    login: str | None = None
    email_address: str | None = None
    email: str | None = None
    job_title: str | None = None
    phone: str | None = None
    business_phone: str | None = None
    mobile_phone: str | None = None
    active: bool | None = None
    vendor: dict[str, Any] | None = None
    company: Company | dict[str, Any] | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ProjectUser(CompanyUser):
    """Flexible Procore project directory user resource."""

    project_id: int | None = None
    permission_template: str | dict[str, Any] | None = None
    role: str | dict[str, Any] | None = None


class Vendor(ProcoreModel):
    """Flexible Procore vendor/company directory resource."""

    id: int | None = None
    name: str | None = None
    legal_name: str | None = None
    trade_name: str | None = None
    vendor_number: str | int | None = None
    number: str | int | None = None
    active: bool | None = None
    address: str | dict[str, Any] | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    company_id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class Department(ProcoreModel):
    """Flexible Procore department resource."""

    id: int | None = None
    name: str | None = None
    code: str | int | None = None
    description: str | None = None
    active: bool | None = None
    company_id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class DistributionGroup(ProcoreModel):
    """Flexible Procore project distribution group resource."""

    id: int | None = None
    name: str | None = None
    description: str | None = None
    project_id: int | None = None
    users: list[CompanyUser | dict[str, Any]] = Field(default_factory=list)
    members: list[CompanyUser | dict[str, Any]] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None


class Location(ProcoreModel):
    """Flexible Procore project location resource."""

    id: int | None = None
    name: str | None = None
    full_name: str | None = None
    path: str | None = None
    code: str | int | None = None
    description: str | None = None
    parent_id: int | None = None
    parent: dict[str, Any] | None = None
    children: list["Location"] = Field(default_factory=list)
    project_id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ChangeEvent(ProcoreModel):
    """Flexible read-only Procore change event resource."""

    id: int | None = None
    number: str | int | None = None
    title: str | None = None
    name: str | None = None
    description: str | None = None
    status: str | Status | None = None
    type: str | dict[str, Any] | None = None
    change_event_type: str | dict[str, Any] | None = None
    scope: str | None = None
    reason: str | dict[str, Any] | None = None
    estimated_cost: float | int | str | None = None
    amount: float | int | str | None = None
    project_id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ChangeEventStatus(ProcoreModel):
    """Flexible read-only Procore change event status resource."""

    id: int | None = None
    name: str | None = None
    status: str | None = None
    label: str | None = None
    position: int | None = None


class ChangeEventType(ProcoreModel):
    """Flexible read-only Procore change event type resource."""

    id: int | None = None
    name: str | None = None
    type: str | None = None
    description: str | None = None
    position: int | None = None


class ChangeEventSettings(ProcoreModel):
    """Flexible read-only Procore change event settings resource."""

    id: int | None = None
    project_id: int | None = None
    enabled: bool | None = None
    settings: dict[str, Any] | None = None
    configuration: dict[str, Any] | None = None


class PrimeChangeOrder(ProcoreModel):
    """Flexible read-only Procore prime change order resource."""

    id: int | None = None
    number: str | int | None = None
    title: str | None = None
    name: str | None = None
    description: str | None = None
    status: str | Status | None = None
    amount: float | int | str | None = None
    contract_id: int | None = None
    project_id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class CommitmentChangeOrder(ProcoreModel):
    """Flexible read-only Procore commitment change order resource."""

    id: int | None = None
    number: str | int | None = None
    title: str | None = None
    name: str | None = None
    description: str | None = None
    status: str | Status | None = None
    amount: float | int | str | None = None
    commitment_id: int | None = None
    contract_id: int | None = None
    project_id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ChangeOrderPackage(ProcoreModel):
    """Flexible read-only Procore change order package resource."""

    id: int | None = None
    number: str | int | None = None
    title: str | None = None
    name: str | None = None
    description: str | None = None
    status: str | Status | None = None
    project_id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class DirectCost(ProcoreModel):
    """Flexible read-only Procore direct cost resource."""

    id: int | None = None
    number: str | int | None = None
    title: str | None = None
    name: str | None = None
    description: str | None = None
    status: str | Status | None = None
    amount: float | int | str | None = None
    cost_code: str | dict[str, Any] | None = None
    vendor: str | dict[str, Any] | None = None
    project_id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class BudgetView(ProcoreModel):
    """Flexible read-only Procore budget view resource."""

    id: int | None = None
    name: str | None = None
    description: str | None = None
    project_id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class BudgetDetailColumn(ProcoreModel):
    """Flexible read-only Procore budget detail column resource."""

    id: int | None = None
    name: str | None = None
    label: str | None = None
    field: str | None = None
    column_type: str | None = None
    position: int | None = None


class BudgetDetailRow(ProcoreModel):
    """Flexible read-only Procore budget detail row resource."""

    id: int | None = None
    name: str | None = None
    cost_code: str | dict[str, Any] | None = None
    cost_type: str | dict[str, Any] | None = None
    values: dict[str, Any] | None = None
    project_id: int | None = None


class BudgetSummaryRow(ProcoreModel):
    """Flexible read-only Procore budget summary row resource."""

    id: int | None = None
    name: str | None = None
    group: str | None = None
    values: dict[str, Any] | None = None
    project_id: int | None = None


class CostCode(ProcoreModel):
    """Flexible read-only Procore cost code resource."""

    id: int | None = None
    code: str | int | None = None
    name: str | None = None
    full_code: str | None = None
    description: str | None = None
    parent_id: int | None = None
    company_id: int | None = None


class WbsCode(ProcoreModel):
    """Flexible read-only Procore WBS code resource."""

    id: int | None = None
    code: str | int | None = None
    name: str | None = None
    full_code: str | None = None
    description: str | None = None
    project_id: int | None = None


class Commitment(ProcoreModel):
    """Flexible read-only Procore commitment/commitment contract resource."""

    id: int | None = None
    number: str | int | None = None
    title: str | None = None
    name: str | None = None
    description: str | None = None
    status: str | Status | None = None
    amount: float | int | str | None = None
    vendor: str | dict[str, Any] | None = None
    project_id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class PrimeContract(ProcoreModel):
    """Flexible read-only Procore prime contract resource."""

    id: int | None = None
    number: str | int | None = None
    title: str | None = None
    name: str | None = None
    description: str | None = None
    status: str | Status | None = None
    amount: float | int | str | None = None
    contract_amount: float | int | str | None = None
    project_id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class PrimeContractLineItem(ProcoreModel):
    """Flexible read-only Procore prime contract line item resource."""

    id: int | None = None
    number: str | int | None = None
    name: str | None = None
    description: str | None = None
    amount: float | int | str | None = None
    cost_code: str | dict[str, Any] | None = None
    cost_type: str | dict[str, Any] | None = None
    prime_contract_id: int | None = None
    project_id: int | None = None


class PrimeContractSummary(ProcoreModel):
    """Flexible read-only Procore prime contract summary resource."""

    id: int | None = None
    prime_contract_id: int | None = None
    project_id: int | None = None
    summary: dict[str, Any] | None = None
    values: dict[str, Any] | None = None
    total: float | int | str | None = None


class CommitmentContract(ProcoreModel):
    """Flexible read-only Procore commitment contract resource."""

    id: int | None = None
    number: str | int | None = None
    title: str | None = None
    name: str | None = None
    description: str | None = None
    status: str | Status | None = None
    amount: float | int | str | None = None
    vendor: str | dict[str, Any] | None = None
    project_id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class PurchaseOrderContract(ProcoreModel):
    """Flexible read-only Procore purchase order contract resource."""

    id: int | None = None
    number: str | int | None = None
    title: str | None = None
    name: str | None = None
    description: str | None = None
    status: str | Status | None = None
    amount: float | int | str | None = None
    vendor: str | dict[str, Any] | None = None
    project_id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class WorkOrderContract(ProcoreModel):
    """Flexible read-only Procore work order contract resource."""

    id: int | None = None
    number: str | int | None = None
    title: str | None = None
    name: str | None = None
    description: str | None = None
    status: str | Status | None = None
    amount: float | int | str | None = None
    vendor: str | dict[str, Any] | None = None
    project_id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class OwnerInvoice(ProcoreModel):
    """Flexible read-only Procore owner invoice/payment application resource."""

    id: int | None = None
    number: str | int | None = None
    title: str | None = None
    name: str | None = None
    status: str | Status | None = None
    amount: float | int | str | None = None
    billing_period_id: int | None = None
    prime_contract_id: int | None = None
    project_id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class OwnerInvoiceLineItem(ProcoreModel):
    """Flexible read-only Procore owner invoice line item resource."""

    id: int | None = None
    number: str | int | None = None
    name: str | None = None
    description: str | None = None
    amount: float | int | str | None = None
    owner_invoice_id: int | None = None
    prime_contract_id: int | None = None
    project_id: int | None = None


class SubcontractorInvoice(ProcoreModel):
    """Flexible read-only Procore subcontractor invoice/requisition resource."""

    id: int | None = None
    number: str | int | None = None
    title: str | None = None
    name: str | None = None
    status: str | Status | None = None
    amount: float | int | str | None = None
    billing_period_id: int | None = None
    contract_id: int | None = None
    project_id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class RequisitionContractItem(ProcoreModel):
    """Flexible read-only Procore requisition contract item resource."""

    id: int | None = None
    number: str | int | None = None
    name: str | None = None
    description: str | None = None
    amount: float | int | str | None = None
    requisition_id: int | None = None
    project_id: int | None = None


class RequisitionContractDetailItem(ProcoreModel):
    """Flexible read-only Procore requisition contract detail item resource."""

    id: int | None = None
    number: str | int | None = None
    name: str | None = None
    description: str | None = None
    amount: float | int | str | None = None
    requisition_id: int | None = None
    project_id: int | None = None


class RequisitionChangeOrderItem(ProcoreModel):
    """Flexible read-only Procore requisition change order item resource."""

    id: int | None = None
    number: str | int | None = None
    name: str | None = None
    description: str | None = None
    amount: float | int | str | None = None
    requisition_id: int | None = None
    project_id: int | None = None


class ContractPayment(ProcoreModel):
    """Flexible read-only Procore contract payment resource."""

    id: int | None = None
    number: str | int | None = None
    title: str | None = None
    name: str | None = None
    status: str | Status | None = None
    amount: float | int | str | None = None
    contract_id: int | None = None
    project_id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class BillingPeriod(ProcoreModel):
    """Flexible read-only Procore billing period resource."""

    id: int | None = None
    name: str | None = None
    status: str | Status | None = None
    start_date: str | None = None
    end_date: str | None = None
    billing_date: str | None = None
    project_id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class CostType(ProcoreModel):
    """Flexible read-only Procore cost type reference resource."""

    id: int | None = None
    name: str | None = None
    code: str | int | None = None
    description: str | None = None
    company_id: int | None = None


class TaxCode(ProcoreModel):
    """Flexible read-only Procore tax code reference resource."""

    id: int | None = None
    name: str | None = None
    code: str | int | None = None
    description: str | None = None
    rate: float | int | str | None = None
    company_id: int | None = None


class ProjectSchedule(ProcoreModel):
    """Read-only Procore project schedule metadata."""

    id: int | None = None
    name: str | None = None
    title: str | None = None
    project_id: int | None = None
    status: str | Status | None = None
    schedule_type: str | None = None
    integration_type: str | None = None
    data_date: str | None = None
    start_date: str | None = None
    finish_date: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ScheduleSettings(ProcoreModel):
    """Read-only Procore project schedule settings."""

    id: int | None = None
    project_id: int | None = None
    calendar_id: int | None = None
    schedule_type: str | None = None
    integration_type: str | None = None
    settings: dict[str, Any] | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ScheduleType(ProcoreModel):
    """Read-only Procore schedule type metadata."""

    id: int | None = None
    name: str | None = None
    type: str | None = None
    display_name: str | None = None
    description: str | None = None


class ScheduleIntegration(ProcoreModel):
    """Read-only Procore schedule integration metadata."""

    id: int | None = None
    name: str | None = None
    type: str | None = None
    provider: str | None = None
    status: str | Status | None = None
    last_synced_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ScheduleImportStatus(ProcoreModel):
    """Read-only status for the latest project schedule import."""

    id: int | None = None
    project_id: int | None = None
    status: str | Status | None = None
    state: str | None = None
    message: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ScheduleResourceAssignment(ProcoreModel):
    """Read-only Procore schedule resource assignment."""

    id: int | None = None
    project_id: int | None = None
    task_id: int | None = None
    resource_id: int | None = None
    resource_name: str | None = None
    resource_type: str | None = None
    name: str | None = None
    quantity: float | int | None = None
    unit: str | None = None
    start_date: str | None = None
    finish_date: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class Task(ProcoreModel):
    """Read-only Procore task or schedule task resource."""

    id: int | None = None
    number: str | int | None = None
    name: str | None = None
    title: str | None = None
    subject: str | None = None
    description: str | None = None
    status: str | Status | None = None
    priority: str | None = None
    start_date: str | None = None
    due_date: str | None = None
    finish_date: str | None = None
    completed_at: str | None = None
    assignee: str | User | None = None
    assignee_id: int | None = None
    created_by: str | User | None = None
    created_at: str | None = None
    updated_at: str | None = None


class TaskRequestedChange(ProcoreModel):
    """Read-only requested change for a Procore task."""

    id: int | None = None
    task_id: int | None = None
    number: str | int | None = None
    title: str | None = None
    description: str | None = None
    status: str | Status | None = None
    requested_by: str | User | None = None
    created_at: str | None = None
    updated_at: str | None = None


class CalendarItem(ProcoreModel):
    """Read-only Procore calendar item."""

    id: int | None = None
    number: str | int | None = None
    name: str | None = None
    title: str | None = None
    description: str | None = None
    item_type: str | None = None
    type: str | None = None
    status: str | Status | None = None
    start_date: str | None = None
    end_date: str | None = None
    due_date: str | None = None
    all_day: bool | None = None
    location: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class CoordinationIssue(ProcoreModel):
    """Read-only Procore coordination issue."""

    id: int | None = None
    number: str | int | None = None
    title: str | None = None
    name: str | None = None
    description: str | None = None
    status: str | Status | None = None
    priority: str | None = None
    type: str | None = None
    assignee: str | User | None = None
    assignee_id: int | None = None
    due_date: str | None = None
    created_by: str | User | None = None
    created_at: str | None = None
    updated_at: str | None = None


class CoordinationIssueChangeHistoryEvent(ProcoreModel):
    """Read-only change history event for a coordination issue."""

    id: int | None = None
    coordination_issue_id: int | None = None
    event_type: str | None = None
    field_name: str | None = None
    old_value: str | int | float | bool | None = None
    new_value: str | int | float | bool | None = None
    user: str | User | None = None
    created_at: str | None = None


class CoordinationIssueActivity(ProcoreModel):
    """Read-only activity feed item for a coordination issue."""

    id: int | None = None
    coordination_issue_id: int | None = None
    type: str | None = None
    action: str | None = None
    body: str | None = None
    user: str | User | None = None
    created_at: str | None = None
    updated_at: str | None = None


class CoordinationIssueFilterOption(ProcoreModel):
    """Read-only filter option for coordination issue lists."""

    id: int | None = None
    name: str | None = None
    label: str | None = None
    value: str | int | None = None
    option_type: str | None = None
    type: str | None = None


class Form(ProcoreModel):
    """Read-only Procore form resource."""

    id: int | None = None
    number: str | int | None = None
    name: str | None = None
    title: str | None = None
    description: str | None = None
    status: str | Status | None = None
    template_id: int | None = None
    form_template_id: int | None = None
    created_by: str | User | None = None
    created_at: str | None = None
    updated_at: str | None = None


class FormTemplate(ProcoreModel):
    """Read-only Procore form template."""

    id: int | None = None
    name: str | None = None
    title: str | None = None
    description: str | None = None
    active: bool | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ActionPlan(ProcoreModel):
    """Read-only Procore action plan resource."""

    id: int | None = None
    number: str | int | None = None
    name: str | None = None
    title: str | None = None
    description: str | None = None
    status: str | Status | None = None
    plan_type: str | None = None
    assignee: str | User | None = None
    created_by: str | User | None = None
    due_date: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ActionPlanChangeHistoryEvent(ProcoreModel):
    """Read-only change history event for an action plan."""

    id: int | None = None
    action_plan_id: int | None = None
    event_type: str | None = None
    field_name: str | None = None
    old_value: str | int | float | bool | None = None
    new_value: str | int | float | bool | None = None
    user: str | User | None = None
    created_at: str | None = None


class DocumentFolder(ProcoreModel):
    """Procore document folder resource."""

    id: int | None = None
    name: str | None = None
    type: str | None = None
    item_type: str | None = None
    parent_id: int | None = None
    path: str | None = None
    folders: list["DocumentFolder"] = Field(default_factory=list)
    files: list["Document"] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None


class Document(ProcoreModel):
    """Procore document resource."""

    id: int | None = None
    name: str | None = None
    type: str | None = None
    item_type: str | None = None
    filename: str | None = None
    file_name: str | None = None
    url: str | HttpUrl | None = None
    download_url: str | HttpUrl | None = None
    folder_id: int | None = None
    content_type: str | None = None
    file_size: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class DrawingArea(ProcoreModel):
    """Procore drawing area resource."""

    id: int | None = None
    name: str | None = None
    position: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class DrawingDiscipline(ProcoreModel):
    """Procore drawing discipline resource."""

    id: int | None = None
    name: str | None = None
    abbreviation: str | None = None
    position: int | None = None


class Drawing(ProcoreModel):
    """Procore drawing resource."""

    id: int | None = None
    number: str | int | None = None
    title: str | None = None
    name: str | None = None
    filename: str | None = None
    file_name: str | None = None
    discipline: str | DrawingDiscipline | None = None
    discipline_id: int | None = None
    drawing_area: DrawingArea | str | None = None
    drawing_area_id: int | None = None
    revision_number: str | int | None = None
    current_revision_id: int | None = None
    status: str | Status | None = None
    issued_date: str | None = None
    received_date: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    url: str | HttpUrl | None = None
    download_url: str | HttpUrl | None = None


class PhotoAlbum(ProcoreModel):
    """Procore photo album resource.

    Procore calls photo albums ``image_categories`` in the REST API.
    """

    id: int | None = None
    name: str | None = None
    description: str | None = None
    image_count: int | None = None
    photos_count: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class PhotoImage(ProcoreModel):
    """Procore photo/image resource."""

    id: int | None = None
    name: str | None = None
    filename: str | None = None
    file_name: str | None = None
    image_name: str | None = None
    original_filename: str | None = None
    description: str | None = None
    image_category_id: int | None = None
    private: bool | None = None
    starred: bool | None = None
    taken_at: str | None = None
    exposure_date: str | None = None
    log_date: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    thumbnail_url: str | HttpUrl | None = None
    url: str | HttpUrl | None = None
    download_url: str | HttpUrl | None = None
    file_url: str | HttpUrl | None = None
    original_url: str | HttpUrl | None = None
    full_size_url: str | HttpUrl | None = None


class PhotoAlbumDownloadResult(ProcoreModel):
    """Summary returned after downloading a photo album."""

    album_id: int
    requested: int
    downloaded_files: list[str] = Field(default_factory=list)
    skipped: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class DailyLogCount(ProcoreModel):
    """Procore Daily Log count resource."""

    log_type: str | None = None
    type: str | None = None
    name: str | None = None
    count: int | None = None


class DailyLogHeader(ProcoreModel):
    """Procore Daily Log header resource."""

    id: int | None = None
    log_date: str | None = None
    date: str | None = None
    status: str | Status | None = None
    created_at: str | None = None
    updated_at: str | None = None


class DailyLogEntry(ProcoreModel):
    """Flexible Procore Daily Log entry resource."""

    id: int | None = None
    log_type: str | None = None
    log_date: str | None = None
    date: str | None = None
    comments: str | None = None
    description: str | None = None
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class DelayLogType(ProcoreModel):
    """Procore delay log type resource."""

    id: int | None = None
    name: str | None = None
    description: str | None = None


class DailyLogsByType(ProcoreModel):
    """Daily Log entries grouped by log type for one date."""

    project_id: int
    log_date: str | None = None
    logs: dict[str, list[DailyLogEntry]] = Field(default_factory=dict)
    errors: dict[str, str] = Field(default_factory=dict)


class SpecificationSet(ProcoreModel):
    """Procore specification set resource."""

    id: int | None = None
    name: str | None = None
    description: str | None = None
    issue_date: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class SpecificationSection(ProcoreModel):
    """Procore specification section resource."""

    id: int | None = None
    number: str | int | None = None
    title: str | None = None
    description: str | None = None
    specification_set_id: int | None = None
    specification_area_id: int | None = None
    division_id: int | None = None
    current_revision_id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class SpecificationSectionRevision(ProcoreModel):
    """Procore specification section revision resource."""

    id: int | None = None
    number: str | int | None = None
    title: str | None = None
    description: str | None = None
    revision_number: str | int | None = None
    specification_section_id: int | None = None
    specification_set_id: int | None = None
    specification_area_id: int | None = None
    division_id: int | None = None
    filename: str | None = None
    file_name: str | None = None
    url: str | HttpUrl | None = None
    download_url: str | HttpUrl | None = None
    file_url: str | HttpUrl | None = None
    created_at: str | None = None
    updated_at: str | None = None


class SpecificationRevisionDownload(ProcoreModel):
    """Download metadata for a Procore specification section revision."""

    id: int | None = None
    number: str | int | None = None
    title: str | None = None
    revision_number: str | int | None = None
    filename: str | None = None
    file_name: str | None = None
    name: str | None = None
    url: str | HttpUrl | None = None
    download_url: str | HttpUrl | None = None
    file_url: str | HttpUrl | None = None
