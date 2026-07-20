"""Endpoint path definitions for the Procore REST API."""

from __future__ import annotations

API_V1 = "/rest/v1.0"
API_V1_1 = "/rest/v1.1"
API_V2 = "/rest/v2.0"
API_V2_1 = "/rest/v2.1"

COMPANIES = f"{API_V1}/companies"
PROJECTS = f"{API_V1}/companies/{{company_id}}/projects"
RFIS = f"{API_V1_1}/projects/{{project_id}}/rfis"
RFI = f"{API_V1_1}/projects/{{project_id}}/rfis/{{rfi_id}}"
SUBMITTALS = f"{API_V1_1}/projects/{{project_id}}/submittals"
SUBMITTAL = f"{API_V1_1}/projects/{{project_id}}/submittals/{{submittal_id}}"
# Procore Documents are exposed through the Project Folders and Files API.
# The project is supplied as a query parameter, not as a path segment.
DOCUMENT_FOLDERS = f"{API_V1}/folders"
DOCUMENT_FOLDER = f"{API_V1}/folders/{{folder_id}}"
DOCUMENTS = DOCUMENT_FOLDERS
DOCUMENT = f"{API_V1}/files/{{document_id}}"
# Procore Drawings are organized by project drawing areas. Drawing list and
# item endpoints are drawing-area scoped, while area and revision collections
# are project scoped.
DRAWING_AREAS = f"{API_V1}/projects/{{project_id}}/drawing_areas"
DRAWING_AREA = f"{API_V1}/projects/{{project_id}}/drawing_areas/{{drawing_area_id}}"
DRAWING_DISCIPLINES = f"{API_V1}/projects/{{project_id}}/drawing_disciplines"
DRAWINGS = f"{API_V1}/drawing_areas/{{drawing_area_id}}/drawings"
DRAWING = f"{API_V1}/drawing_areas/{{drawing_area_id}}/drawings/{{drawing_id}}"
DRAWING_REVISIONS = f"{API_V1}/projects/{{project_id}}/drawing_revisions"
IMAGE_CATEGORIES = f"{API_V1}/image_categories"
IMAGE_CATEGORY = f"{API_V1}/image_categories/{{image_category_id}}"
IMAGES = f"{API_V1}/images"
IMAGE = f"{API_V1}/images/{{image_id}}"
DAILY_LOG_COUNTS = f"{API_V1_1}/projects/{{project_id}}/daily_logs/counts"
DAILY_LOG_HEADERS = f"{API_V1}/projects/{{project_id}}/daily_log_headers"
DAILY_LOG_TYPES = {
    "manpower": "manpower_logs",
    "notes": "notes_logs",
    "daily_construction_report": "daily_construction_report_logs",
    "delay": "delay_logs",
    "delivery": "delivery_logs",
    "call": "call_logs",
    "accident": "accident_logs",
    "dumpster": "dumpster_logs",
    "visitor": "visitor_logs",
    "productivity": "productivity_logs",
    "plan_revision": "plan_revision_logs",
}
DELAY_LOG_TYPES = f"{API_V1}/projects/{{project_id}}/daily_logs/delay_log_types"
SPECIFICATION_SETS = f"{API_V2}/companies/{{company_id}}/projects/{{project_id}}/specification_sets"
SPECIFICATION_SET_V1 = (
    f"{API_V1}/projects/{{project_id}}/specification_sets/{{specification_set_id}}"
)
SPECIFICATION_SECTIONS = (
    f"{API_V2_1}/companies/{{company_id}}/projects/{{project_id}}/specification_sections"
)
SPECIFICATION_SECTION_REVISIONS = (
    f"{API_V2_1}/companies/{{company_id}}/projects/{{project_id}}"
    "/specification_section_revisions"
)
SPECIFICATION_SECTION_REVISION = (
    f"{API_V2_1}/companies/{{company_id}}/projects/{{project_id}}"
    "/specification_section_revisions/{revision_id}"
)
SPECIFICATION_SECTION_REVISION_DOWNLOAD = (
    f"{API_V2_1}/companies/{{company_id}}/projects/{{project_id}}"
    "/specification_section_revisions/{revision_id}/download"
)
OBSERVATION_ITEMS = f"{API_V1}/observations/items"
OBSERVATION_ITEM = f"{API_V1}/observations/items/{{observation_id}}"
PUNCH_ITEMS = f"{API_V1}/punch_items"
PUNCH_ITEM = f"{API_V1}/punch_items/{{punch_item_id}}"
GENERIC_TOOLS = f"{API_V1}/generic_tools"
GENERIC_TOOL = f"{API_V1}/generic_tools/{{generic_tool_id}}"
GENERIC_TOOL_ITEMS = f"{API_V1}/generic_tools/{{generic_tool_id}}/generic_tool_items"
GENERIC_TOOL_ITEM = f"{API_V1}/generic_tool_items/{{generic_tool_item_id}}"
MEETINGS = f"{API_V1}/meetings"
MEETING = f"{API_V1}/meetings/{{meeting_id}}"
# Procore inspection-style resources may be exposed through checklist APIs.
CHECKLISTS = f"{API_V1}/checklists"
CHECKLIST = f"{API_V1}/checklists/{{checklist_id}}"
INCIDENTS = f"{API_V1}/incidents"
INCIDENT = f"{API_V1}/incidents/{{incident_id}}"
PROJECT_INCIDENT_CONFIGURATION = f"{API_V1}/projects/{{project_id}}/incident_configuration"
COMPANY_USERS = f"{API_V1}/companies/{{company_id}}/users"
COMPANY_USER = f"{API_V1}/companies/{{company_id}}/users/{{user_id}}"
PROJECT_USERS = f"{API_V1}/projects/{{project_id}}/users"
PROJECT_USER = f"{API_V1}/projects/{{project_id}}/users/{{user_id}}"
PROJECT_TOOLS = f"{API_V1}/projects/{{project_id}}/tools"
PROJECT_TOOL = f"{API_V1}/projects/{{project_id}}/tools/{{tool_id}}"
VENDORS = f"{API_V1}/vendors"
VENDOR = f"{API_V1}/vendors/{{vendor_id}}"
DEPARTMENTS = f"{API_V1}/companies/{{company_id}}/departments"
DEPARTMENT = f"{API_V1}/companies/{{company_id}}/departments/{{department_id}}"
PROJECT_DISTRIBUTION_GROUPS = f"{API_V1}/projects/{{project_id}}/distribution_groups"
PROJECT_DISTRIBUTION_GROUP = (
    f"{API_V1}/projects/{{project_id}}/distribution_groups/{{distribution_group_id}}"
)
LOCATIONS = f"{API_V1}/projects/{{project_id}}/locations"
LOCATION = f"{API_V1}/projects/{{project_id}}/locations/{{location_id}}"
CHANGE_EVENTS = f"{API_V1}/projects/{{project_id}}/change_events"
CHANGE_EVENT = f"{API_V1}/projects/{{project_id}}/change_events/{{change_event_id}}"
CHANGE_EVENT_STATUSES = f"{API_V1}/projects/{{project_id}}/change_event_statuses"
CHANGE_EVENT_TYPES = f"{API_V1}/projects/{{project_id}}/change_event_types"
CHANGE_EVENT_SETTINGS = f"{API_V1}/projects/{{project_id}}/change_event_settings"
PRIME_CHANGE_ORDERS = f"{API_V1}/projects/{{project_id}}/prime_change_orders"
PRIME_CHANGE_ORDER = (
    f"{API_V1}/projects/{{project_id}}/prime_change_orders/{{prime_change_order_id}}"
)
COMMITMENT_CHANGE_ORDERS = f"{API_V1}/projects/{{project_id}}/commitment_change_orders"
COMMITMENT_CHANGE_ORDER = (
    f"{API_V1}/projects/{{project_id}}" "/commitment_change_orders/{commitment_change_order_id}"
)
CHANGE_ORDER_PACKAGES = f"{API_V1}/projects/{{project_id}}/change_order_packages"
CHANGE_ORDER_PACKAGE = (
    f"{API_V1}/projects/{{project_id}}/change_order_packages/{{change_order_package_id}}"
)
DIRECT_COSTS = f"{API_V1}/projects/{{project_id}}/direct_costs"
DIRECT_COST = f"{API_V1}/projects/{{project_id}}/direct_costs/{{direct_cost_id}}"
BUDGET_VIEWS = f"{API_V1}/projects/{{project_id}}/budget_views"
BUDGET_VIEW = f"{API_V1}/projects/{{project_id}}/budget_views/{{budget_view_id}}"
BUDGET_DETAIL_COLUMNS = (
    f"{API_V1}/projects/{{project_id}}/budget_views/{{budget_view_id}}" "/budget_detail_columns"
)
BUDGET_DETAILS = f"{API_V1}/projects/{{project_id}}/budget_views/{{budget_view_id}}/budget_details"
BUDGET_VIEW_SUMMARY_ROWS = (
    f"{API_V1}/projects/{{project_id}}/budget_views/{{budget_view_id}}/summary_rows"
)
COST_CODES = f"{API_V1}/companies/{{company_id}}/cost_codes"
STANDARD_COST_CODES = (
    f"{API_V1}/companies/{{company_id}}"
    "/standard_cost_code_lists/{standard_cost_code_list_id}/cost_codes"
)
WBS_CODES = f"{API_V1}/projects/{{project_id}}/wbs_codes"
COMMITMENTS = f"{API_V1}/projects/{{project_id}}/commitments"
COMMITMENT = f"{API_V1}/projects/{{project_id}}/commitments/{{commitment_id}}"
PRIME_CONTRACTS = f"{API_V1}/projects/{{project_id}}/prime_contracts"
PRIME_CONTRACT = f"{API_V1}/projects/{{project_id}}/prime_contracts/{{prime_contract_id}}"
PRIME_CONTRACT_LINE_ITEMS = (
    f"{API_V1}/projects/{{project_id}}/prime_contracts/{{prime_contract_id}}/line_items"
)
PRIME_CONTRACT_SUMMARY = (
    f"{API_V1}/projects/{{project_id}}/prime_contracts/{{prime_contract_id}}/summary"
)
COMMITMENT_CONTRACTS = f"{API_V1}/projects/{{project_id}}/commitment_contracts"
COMMITMENT_CONTRACT = (
    f"{API_V1}/projects/{{project_id}}/commitment_contracts/{{commitment_contract_id}}"
)
PURCHASE_ORDER_CONTRACTS = f"{API_V1}/projects/{{project_id}}/purchase_order_contracts"
PURCHASE_ORDER_CONTRACT = (
    f"{API_V1}/projects/{{project_id}}" "/purchase_order_contracts/{purchase_order_contract_id}"
)
WORK_ORDER_CONTRACTS = f"{API_V1}/projects/{{project_id}}/work_order_contracts"
WORK_ORDER_CONTRACT = (
    f"{API_V1}/projects/{{project_id}}/work_order_contracts/{{work_order_contract_id}}"
)
OWNER_INVOICES = (
    f"{API_V1}/projects/{{project_id}}/prime_contracts/{{prime_contract_id}}/owner_invoices"
)
OWNER_INVOICE = (
    f"{API_V1}/projects/{{project_id}}/prime_contracts/{{prime_contract_id}}"
    "/owner_invoices/{owner_invoice_id}"
)
OWNER_INVOICE_LINE_ITEMS = (
    f"{API_V1}/projects/{{project_id}}/prime_contracts/{{prime_contract_id}}"
    "/owner_invoices/{owner_invoice_id}/line_items"
)
SUBCONTRACTOR_INVOICES = f"{API_V1}/projects/{{project_id}}/requisitions"
SUBCONTRACTOR_INVOICE = f"{API_V1}/projects/{{project_id}}/requisitions/{{requisition_id}}"
REQUISITION_CONTRACT_ITEMS = (
    f"{API_V1}/projects/{{project_id}}/requisitions/{{requisition_id}}/contract_items"
)
REQUISITION_CONTRACT_DETAIL_ITEMS = (
    f"{API_V1}/projects/{{project_id}}" "/requisitions/{requisition_id}/contract_detail_items"
)
REQUISITION_CHANGE_ORDER_ITEMS = (
    f"{API_V1}/projects/{{project_id}}/requisitions/{{requisition_id}}/change_order_items"
)
CONTRACT_PAYMENTS = f"{API_V1}/projects/{{project_id}}/contract_payments"
CONTRACT_PAYMENT = f"{API_V1}/projects/{{project_id}}/contract_payments/{{contract_payment_id}}"
BILLING_PERIODS = f"{API_V1}/projects/{{project_id}}/billing_periods"
BILLING_PERIOD = f"{API_V1}/projects/{{project_id}}/billing_periods/{{billing_period_id}}"
COST_TYPES = f"{API_V1}/companies/{{company_id}}/cost_types"
TAX_CODES = f"{API_V1}/companies/{{company_id}}/tax_codes"
PROJECT_SCHEDULE = f"{API_V1}/projects/{{project_id}}/schedule"
SCHEDULE_SETTINGS = f"{API_V1}/projects/{{project_id}}/schedule_settings"
SCHEDULE_TYPE = f"{API_V1}/projects/{{project_id}}/schedule_type"
SCHEDULE_INTEGRATION = f"{API_V1}/projects/{{project_id}}/schedule_integration"
SCHEDULE_IMPORT_STATUS = f"{API_V1}/projects/{{project_id}}/schedule_imports/status"
SCHEDULE_RESOURCE_ASSIGNMENTS = f"{API_V1}/projects/{{project_id}}/schedule_resource_assignments"
SCHEDULE_RESOURCE_ASSIGNMENT = (
    f"{API_V1}/projects/{{project_id}}"
    "/schedule_resource_assignments/{schedule_resource_assignment_id}"
)
TASKS = f"{API_V1}/projects/{{project_id}}/tasks"
TASK = f"{API_V1}/projects/{{project_id}}/tasks/{{task_id}}"
TASK_REQUESTED_CHANGES = f"{API_V1}/projects/{{project_id}}/tasks/{{task_id}}/requested_changes"
CALENDAR_ITEMS = f"{API_V1}/projects/{{project_id}}/calendar_items"
CALENDAR_ITEM = f"{API_V1}/projects/{{project_id}}/calendar_items/{{calendar_item_id}}"
COORDINATION_ISSUES = f"{API_V1}/projects/{{project_id}}/coordination_issues"
COORDINATION_ISSUE = (
    f"{API_V1}/projects/{{project_id}}/coordination_issues/{{coordination_issue_id}}"
)
COORDINATION_ISSUE_CHANGE_HISTORY = (
    f"{API_V1}/projects/{{project_id}}/coordination_issues/{{coordination_issue_id}}"
    "/change_history"
)
COORDINATION_ISSUE_ACTIVITY_FEED = (
    f"{API_V1}/projects/{{project_id}}/coordination_issues/{{coordination_issue_id}}"
    "/activity_feed"
)
COORDINATION_ISSUE_FILTER_OPTIONS = (
    f"{API_V1}/projects/{{project_id}}/coordination_issues/filter_options"
)
FORMS = f"{API_V1}/projects/{{project_id}}/forms"
FORM = f"{API_V1}/projects/{{project_id}}/forms/{{form_id}}"
FORM_TEMPLATES = f"{API_V1}/projects/{{project_id}}/form_templates"
ACTION_PLANS = f"{API_V1}/projects/{{project_id}}/action_plans"
ACTION_PLAN = f"{API_V1}/projects/{{project_id}}/action_plans/{{action_plan_id}}"
ACTION_PLAN_CHANGE_HISTORY_EVENTS = (
    f"{API_V1}/projects/{{project_id}}/action_plans/{{action_plan_id}}" "/change_history_events"
)


def companies() -> str:
    """Return the companies collection endpoint."""
    return COMPANIES


def projects(company_id: int) -> str:
    """Return the projects collection endpoint for a company."""
    return PROJECTS.format(company_id=company_id)


def rfis(project_id: int) -> str:
    """Return the RFIs collection endpoint for a project."""
    return RFIS.format(project_id=project_id)


def rfi(project_id: int, rfi_id: int) -> str:
    """Return the endpoint for a single RFI."""
    return RFI.format(project_id=project_id, rfi_id=rfi_id)


def submittals(project_id: int) -> str:
    """Return the submittals collection endpoint for a project."""
    return SUBMITTALS.format(project_id=project_id)


def submittal(project_id: int, submittal_id: int) -> str:
    """Return the endpoint for a single submittal."""
    return SUBMITTAL.format(project_id=project_id, submittal_id=submittal_id)


def document_folders(project_id: int) -> str:
    """Return the project folders collection endpoint.

    Args:
        project_id: Procore project ID. The value is accepted for API
            consistency with service methods; callers pass it as a query
            parameter because Procore's Documents API uses ``/folders``.
    """
    return DOCUMENT_FOLDERS


def document_folder(project_id: int, folder_id: int) -> str:
    """Return the endpoint for a single project document folder."""
    return DOCUMENT_FOLDER.format(folder_id=folder_id)


def documents(project_id: int) -> str:
    """Return the folders/files collection endpoint used to list documents."""
    return DOCUMENTS


def document(project_id: int, document_id: int) -> str:
    """Return the endpoint for a single document file."""
    return DOCUMENT.format(document_id=document_id)


def drawing_areas(project_id: int) -> str:
    """Return the drawing areas collection endpoint for a project."""
    return DRAWING_AREAS.format(project_id=project_id)


def drawing_area(project_id: int, drawing_area_id: int) -> str:
    """Return the endpoint for a single drawing area."""
    return DRAWING_AREA.format(project_id=project_id, drawing_area_id=drawing_area_id)


def drawing_disciplines(project_id: int) -> str:
    """Return the drawing disciplines collection endpoint for a project."""
    return DRAWING_DISCIPLINES.format(project_id=project_id)


def drawings(project_id: int, drawing_area_id: int) -> str:
    """Return the drawings collection endpoint for a drawing area.

    Args:
        project_id: Procore project ID. Accepted for consistency with service
            methods; Procore scopes this endpoint by drawing area.
        drawing_area_id: Procore drawing area ID.
    """
    return DRAWINGS.format(drawing_area_id=drawing_area_id)


def drawing(project_id: int, drawing_area_id: int, drawing_id: int) -> str:
    """Return the endpoint for a single drawing."""
    return DRAWING.format(drawing_area_id=drawing_area_id, drawing_id=drawing_id)


def drawing_revisions(project_id: int) -> str:
    """Return the drawing revisions collection endpoint for a project."""
    return DRAWING_REVISIONS.format(project_id=project_id)


def image_categories() -> str:
    """Return the photo albums/image categories collection endpoint."""
    return IMAGE_CATEGORIES


def image_category(image_category_id: int) -> str:
    """Return the endpoint for one photo album/image category."""
    return IMAGE_CATEGORY.format(image_category_id=image_category_id)


def images() -> str:
    """Return the photos/images collection endpoint."""
    return IMAGES


def image(image_id: int) -> str:
    """Return the endpoint for one photo/image."""
    return IMAGE.format(image_id=image_id)


def daily_log_counts(project_id: int) -> str:
    """Return the daily log counts endpoint for a project."""
    return DAILY_LOG_COUNTS.format(project_id=project_id)


def daily_log_headers(project_id: int) -> str:
    """Return the daily log headers collection endpoint for a project."""
    return DAILY_LOG_HEADERS.format(project_id=project_id)


def daily_log_type(project_id: int, log_type: str) -> str:
    """Return the endpoint for a supported Daily Logs type."""
    normalized = log_type.strip().casefold().replace("-", "_")
    if normalized not in DAILY_LOG_TYPES:
        supported = ", ".join(sorted(DAILY_LOG_TYPES))
        raise ValueError(f"Unsupported daily log type {log_type!r}. Supported types: {supported}")
    return f"{API_V1}/projects/{project_id}/{DAILY_LOG_TYPES[normalized]}"


def delay_log_types(project_id: int) -> str:
    """Return the delay log types endpoint for a project."""
    return DELAY_LOG_TYPES.format(project_id=project_id)


def specification_sets(company_id: int, project_id: int) -> str:
    """Return the specification sets collection endpoint for a project."""
    return SPECIFICATION_SETS.format(company_id=company_id, project_id=project_id)


def specification_set_v1(project_id: int, specification_set_id: int) -> str:
    """Return the legacy v1 specification set show endpoint."""
    return SPECIFICATION_SET_V1.format(
        project_id=project_id,
        specification_set_id=specification_set_id,
    )


def specification_sections(company_id: int, project_id: int) -> str:
    """Return the specification sections collection endpoint for a project."""
    return SPECIFICATION_SECTIONS.format(company_id=company_id, project_id=project_id)


def specification_section_revisions(company_id: int, project_id: int) -> str:
    """Return the specification section revisions collection endpoint."""
    return SPECIFICATION_SECTION_REVISIONS.format(
        company_id=company_id,
        project_id=project_id,
    )


def specification_section_revision(company_id: int, project_id: int, revision_id: int) -> str:
    """Return the endpoint for one specification section revision."""
    return SPECIFICATION_SECTION_REVISION.format(
        company_id=company_id,
        project_id=project_id,
        revision_id=revision_id,
    )


def specification_section_revision_download(
    company_id: int,
    project_id: int,
    revision_id: int,
) -> str:
    """Return the download-info endpoint for one specification revision."""
    return SPECIFICATION_SECTION_REVISION_DOWNLOAD.format(
        company_id=company_id,
        project_id=project_id,
        revision_id=revision_id,
    )


def observations(project_id: int) -> str:
    """Return the observations collection endpoint.

    Args:
        project_id: Procore project ID. Accepted for API consistency; Procore's
            observations list endpoint uses ``project_id`` as a query parameter.
    """
    return OBSERVATION_ITEMS


def observation(project_id: int, observation_id: int) -> str:
    """Return the endpoint for one observation item."""
    return OBSERVATION_ITEM.format(observation_id=observation_id)


def punch_items(project_id: int) -> str:
    """Return the punch items collection endpoint.

    Args:
        project_id: Procore project ID. Accepted for API consistency; Procore's
            punch item list endpoint uses ``project_id`` as a query parameter.
    """
    return PUNCH_ITEMS


def punch_item(project_id: int, punch_item_id: int) -> str:
    """Return the endpoint for one punch item."""
    return PUNCH_ITEM.format(punch_item_id=punch_item_id)


def generic_tools(project_id: int) -> str:
    """Return the Generic Tools collection endpoint.

    Args:
        project_id: Procore project ID. Accepted for API consistency; Procore's
            Generic Tools endpoint uses ``project_id`` as a query parameter.
    """
    return GENERIC_TOOLS


def generic_tool(project_id: int, generic_tool_id: int) -> str:
    """Return the endpoint for one Generic Tool."""
    return GENERIC_TOOL.format(generic_tool_id=generic_tool_id)


def generic_tool_items(project_id: int, generic_tool_id: int) -> str:
    """Return the Generic Tool Items collection endpoint."""
    return GENERIC_TOOL_ITEMS.format(generic_tool_id=generic_tool_id)


def generic_tool_item(project_id: int, generic_tool_item_id: int) -> str:
    """Return the endpoint for one Generic Tool Item."""
    return GENERIC_TOOL_ITEM.format(generic_tool_item_id=generic_tool_item_id)


def meetings(project_id: int) -> str:
    """Return the meetings collection endpoint.

    Args:
        project_id: Procore project ID. Accepted for API consistency; the
            conservative Phase 8C service sends it as a query parameter.
    """
    return MEETINGS


def meeting(project_id: int, meeting_id: int) -> str:
    """Return the endpoint for one meeting."""
    return MEETING.format(meeting_id=meeting_id)


def inspections(project_id: int) -> str:
    """Return the checklist-backed inspections collection endpoint."""
    return CHECKLISTS


def inspection(project_id: int, inspection_id: int) -> str:
    """Return the checklist-backed endpoint for one inspection."""
    return CHECKLIST.format(checklist_id=inspection_id)


def incidents(project_id: int) -> str:
    """Return the incidents collection endpoint."""
    return INCIDENTS


def incident(project_id: int, incident_id: int) -> str:
    """Return the endpoint for one incident."""
    return INCIDENT.format(incident_id=incident_id)


def project_incident_configuration(project_id: int) -> str:
    """Return the project incident configuration endpoint."""
    return PROJECT_INCIDENT_CONFIGURATION.format(project_id=project_id)


def company_users(company_id: int) -> str:
    """Return the company users collection endpoint."""
    return COMPANY_USERS.format(company_id=company_id)


def company_user(company_id: int, user_id: int) -> str:
    """Return the endpoint for one company user."""
    return COMPANY_USER.format(company_id=company_id, user_id=user_id)


def project_users(project_id: int) -> str:
    """Return the project users collection endpoint."""
    return PROJECT_USERS.format(project_id=project_id)


def project_user(project_id: int, user_id: int) -> str:
    """Return the endpoint for one project user."""
    return PROJECT_USER.format(project_id=project_id, user_id=user_id)


def project_tools(project_id: int) -> str:
    """Return the project tools collection endpoint."""
    return PROJECT_TOOLS.format(project_id=project_id)


def project_tool(project_id: int, tool_id: int) -> str:
    """Return the endpoint for one project tool."""
    return PROJECT_TOOL.format(project_id=project_id, tool_id=tool_id)


def vendors(company_id: int) -> str:
    """Return the vendors collection endpoint.

    Args:
        company_id: Procore company ID. Accepted for API consistency; the
            conservative Phase 8D service sends it as a query parameter.
    """
    return VENDORS


def vendor(company_id: int, vendor_id: int) -> str:
    """Return the endpoint for one vendor."""
    return VENDOR.format(vendor_id=vendor_id)


def departments(company_id: int) -> str:
    """Return the company departments collection endpoint."""
    return DEPARTMENTS.format(company_id=company_id)


def department(company_id: int, department_id: int) -> str:
    """Return the endpoint for one department."""
    return DEPARTMENT.format(company_id=company_id, department_id=department_id)


def project_distribution_groups(project_id: int) -> str:
    """Return the project distribution groups collection endpoint."""
    return PROJECT_DISTRIBUTION_GROUPS.format(project_id=project_id)


def project_distribution_group(project_id: int, distribution_group_id: int) -> str:
    """Return the endpoint for one project distribution group."""
    return PROJECT_DISTRIBUTION_GROUP.format(
        project_id=project_id,
        distribution_group_id=distribution_group_id,
    )


def locations(project_id: int) -> str:
    """Return the project locations collection endpoint."""
    return LOCATIONS.format(project_id=project_id)


def location(project_id: int, location_id: int) -> str:
    """Return the endpoint for one project location."""
    return LOCATION.format(project_id=project_id, location_id=location_id)


def change_events(project_id: int) -> str:
    """Return the project change events collection endpoint."""
    return CHANGE_EVENTS.format(project_id=project_id)


def change_event(project_id: int, change_event_id: int) -> str:
    """Return the endpoint for one project change event."""
    return CHANGE_EVENT.format(project_id=project_id, change_event_id=change_event_id)


def change_event_statuses(project_id: int) -> str:
    """Return the project change event statuses collection endpoint."""
    return CHANGE_EVENT_STATUSES.format(project_id=project_id)


def change_event_types(project_id: int) -> str:
    """Return the project change event types collection endpoint."""
    return CHANGE_EVENT_TYPES.format(project_id=project_id)


def change_event_settings(project_id: int) -> str:
    """Return the project change event settings endpoint."""
    return CHANGE_EVENT_SETTINGS.format(project_id=project_id)


def prime_change_orders(project_id: int) -> str:
    """Return the project prime change orders collection endpoint."""
    return PRIME_CHANGE_ORDERS.format(project_id=project_id)


def prime_change_order(project_id: int, prime_change_order_id: int) -> str:
    """Return the endpoint for one prime change order."""
    return PRIME_CHANGE_ORDER.format(
        project_id=project_id,
        prime_change_order_id=prime_change_order_id,
    )


def commitment_change_orders(project_id: int) -> str:
    """Return the project commitment change orders collection endpoint."""
    return COMMITMENT_CHANGE_ORDERS.format(project_id=project_id)


def commitment_change_order(project_id: int, commitment_change_order_id: int) -> str:
    """Return the endpoint for one commitment change order."""
    return COMMITMENT_CHANGE_ORDER.format(
        project_id=project_id,
        commitment_change_order_id=commitment_change_order_id,
    )


def change_order_packages(project_id: int) -> str:
    """Return the project change order packages collection endpoint."""
    return CHANGE_ORDER_PACKAGES.format(project_id=project_id)


def change_order_package(project_id: int, change_order_package_id: int) -> str:
    """Return the endpoint for one change order package."""
    return CHANGE_ORDER_PACKAGE.format(
        project_id=project_id,
        change_order_package_id=change_order_package_id,
    )


def direct_costs(project_id: int) -> str:
    """Return the project direct costs collection endpoint."""
    return DIRECT_COSTS.format(project_id=project_id)


def direct_cost(project_id: int, direct_cost_id: int) -> str:
    """Return the endpoint for one direct cost."""
    return DIRECT_COST.format(project_id=project_id, direct_cost_id=direct_cost_id)


def budget_views(project_id: int) -> str:
    """Return the project budget views collection endpoint."""
    return BUDGET_VIEWS.format(project_id=project_id)


def budget_view(project_id: int, budget_view_id: int) -> str:
    """Return the endpoint for one budget view."""
    return BUDGET_VIEW.format(project_id=project_id, budget_view_id=budget_view_id)


def budget_detail_columns(project_id: int, budget_view_id: int) -> str:
    """Return budget detail columns for one budget view."""
    return BUDGET_DETAIL_COLUMNS.format(
        project_id=project_id,
        budget_view_id=budget_view_id,
    )


def budget_details(project_id: int, budget_view_id: int) -> str:
    """Return budget detail rows for one budget view."""
    return BUDGET_DETAILS.format(project_id=project_id, budget_view_id=budget_view_id)


def budget_view_summary_rows(project_id: int, budget_view_id: int) -> str:
    """Return budget summary rows for one budget view."""
    return BUDGET_VIEW_SUMMARY_ROWS.format(
        project_id=project_id,
        budget_view_id=budget_view_id,
    )


def cost_codes(company_id: int) -> str:
    """Return the company cost codes collection endpoint."""
    return COST_CODES.format(company_id=company_id)


def standard_cost_codes(company_id: int, standard_cost_code_list_id: int) -> str:
    """Return cost codes for one standard cost code list."""
    return STANDARD_COST_CODES.format(
        company_id=company_id,
        standard_cost_code_list_id=standard_cost_code_list_id,
    )


def wbs_codes(project_id: int) -> str:
    """Return the project WBS codes collection endpoint."""
    return WBS_CODES.format(project_id=project_id)


def commitments(project_id: int) -> str:
    """Return the project commitments collection endpoint."""
    return COMMITMENTS.format(project_id=project_id)


def commitment(project_id: int, commitment_id: int) -> str:
    """Return the endpoint for one commitment."""
    return COMMITMENT.format(project_id=project_id, commitment_id=commitment_id)


def prime_contracts(project_id: int) -> str:
    """Return the project prime contracts collection endpoint."""
    return PRIME_CONTRACTS.format(project_id=project_id)


def prime_contract(project_id: int, prime_contract_id: int) -> str:
    """Return the endpoint for one prime contract."""
    return PRIME_CONTRACT.format(project_id=project_id, prime_contract_id=prime_contract_id)


def prime_contract_line_items(project_id: int, prime_contract_id: int) -> str:
    """Return line items for one prime contract."""
    return PRIME_CONTRACT_LINE_ITEMS.format(
        project_id=project_id,
        prime_contract_id=prime_contract_id,
    )


def prime_contract_summary(project_id: int, prime_contract_id: int) -> str:
    """Return read-only summary data for one prime contract."""
    return PRIME_CONTRACT_SUMMARY.format(
        project_id=project_id,
        prime_contract_id=prime_contract_id,
    )


def commitment_contracts(project_id: int) -> str:
    """Return the project commitment contracts collection endpoint."""
    return COMMITMENT_CONTRACTS.format(project_id=project_id)


def commitment_contract(project_id: int, commitment_contract_id: int) -> str:
    """Return the endpoint for one commitment contract."""
    return COMMITMENT_CONTRACT.format(
        project_id=project_id,
        commitment_contract_id=commitment_contract_id,
    )


def purchase_order_contracts(project_id: int) -> str:
    """Return the project purchase order contracts collection endpoint."""
    return PURCHASE_ORDER_CONTRACTS.format(project_id=project_id)


def purchase_order_contract(project_id: int, purchase_order_contract_id: int) -> str:
    """Return the endpoint for one purchase order contract."""
    return PURCHASE_ORDER_CONTRACT.format(
        project_id=project_id,
        purchase_order_contract_id=purchase_order_contract_id,
    )


def work_order_contracts(project_id: int) -> str:
    """Return the project work order contracts collection endpoint."""
    return WORK_ORDER_CONTRACTS.format(project_id=project_id)


def work_order_contract(project_id: int, work_order_contract_id: int) -> str:
    """Return the endpoint for one work order contract."""
    return WORK_ORDER_CONTRACT.format(
        project_id=project_id,
        work_order_contract_id=work_order_contract_id,
    )


def owner_invoices(project_id: int, prime_contract_id: int) -> str:
    """Return owner invoices for one prime contract."""
    return OWNER_INVOICES.format(project_id=project_id, prime_contract_id=prime_contract_id)


def owner_invoice(project_id: int, prime_contract_id: int, owner_invoice_id: int) -> str:
    """Return one owner invoice for one prime contract."""
    return OWNER_INVOICE.format(
        project_id=project_id,
        prime_contract_id=prime_contract_id,
        owner_invoice_id=owner_invoice_id,
    )


def owner_invoice_line_items(
    project_id: int,
    prime_contract_id: int,
    owner_invoice_id: int,
) -> str:
    """Return line items for one owner invoice."""
    return OWNER_INVOICE_LINE_ITEMS.format(
        project_id=project_id,
        prime_contract_id=prime_contract_id,
        owner_invoice_id=owner_invoice_id,
    )


def subcontractor_invoices(project_id: int) -> str:
    """Return project subcontractor invoices/requisitions."""
    return SUBCONTRACTOR_INVOICES.format(project_id=project_id)


def subcontractor_invoice(project_id: int, subcontractor_invoice_id: int) -> str:
    """Return one subcontractor invoice/requisition."""
    return SUBCONTRACTOR_INVOICE.format(
        project_id=project_id,
        requisition_id=subcontractor_invoice_id,
    )


def requisition_contract_items(project_id: int, requisition_id: int) -> str:
    """Return contract items for one requisition."""
    return REQUISITION_CONTRACT_ITEMS.format(
        project_id=project_id,
        requisition_id=requisition_id,
    )


def requisition_contract_detail_items(project_id: int, requisition_id: int) -> str:
    """Return contract detail items for one requisition."""
    return REQUISITION_CONTRACT_DETAIL_ITEMS.format(
        project_id=project_id,
        requisition_id=requisition_id,
    )


def requisition_change_order_items(project_id: int, requisition_id: int) -> str:
    """Return change order items for one requisition."""
    return REQUISITION_CHANGE_ORDER_ITEMS.format(
        project_id=project_id,
        requisition_id=requisition_id,
    )


def contract_payments(project_id: int) -> str:
    """Return the project contract payments collection endpoint."""
    return CONTRACT_PAYMENTS.format(project_id=project_id)


def contract_payment(project_id: int, contract_payment_id: int) -> str:
    """Return the endpoint for one contract payment."""
    return CONTRACT_PAYMENT.format(
        project_id=project_id,
        contract_payment_id=contract_payment_id,
    )


def billing_periods(project_id: int) -> str:
    """Return the project billing periods collection endpoint."""
    return BILLING_PERIODS.format(project_id=project_id)


def billing_period(project_id: int, billing_period_id: int) -> str:
    """Return the endpoint for one billing period."""
    return BILLING_PERIOD.format(project_id=project_id, billing_period_id=billing_period_id)


def cost_types(company_id: int) -> str:
    """Return the company cost types collection endpoint."""
    return COST_TYPES.format(company_id=company_id)


def tax_codes(company_id: int) -> str:
    """Return the company tax codes collection endpoint."""
    return TAX_CODES.format(company_id=company_id)


def project_schedule(project_id: int) -> str:
    """Return the project schedule read endpoint."""
    return PROJECT_SCHEDULE.format(project_id=project_id)


def schedule_settings(project_id: int) -> str:
    """Return the project schedule settings read endpoint."""
    return SCHEDULE_SETTINGS.format(project_id=project_id)


def schedule_type(project_id: int) -> str:
    """Return the project schedule type read endpoint."""
    return SCHEDULE_TYPE.format(project_id=project_id)


def schedule_integration(project_id: int) -> str:
    """Return the project schedule integration read endpoint."""
    return SCHEDULE_INTEGRATION.format(project_id=project_id)


def schedule_import_status(project_id: int) -> str:
    """Return the project schedule import status read endpoint."""
    return SCHEDULE_IMPORT_STATUS.format(project_id=project_id)


def schedule_resource_assignments(project_id: int) -> str:
    """Return project schedule resource assignments."""
    return SCHEDULE_RESOURCE_ASSIGNMENTS.format(project_id=project_id)


def schedule_resource_assignment(
    project_id: int,
    schedule_resource_assignment_id: int,
) -> str:
    """Return one project schedule resource assignment."""
    return SCHEDULE_RESOURCE_ASSIGNMENT.format(
        project_id=project_id,
        schedule_resource_assignment_id=schedule_resource_assignment_id,
    )


def tasks(project_id: int) -> str:
    """Return the project tasks collection endpoint."""
    return TASKS.format(project_id=project_id)


def task(project_id: int, task_id: int) -> str:
    """Return one project task endpoint."""
    return TASK.format(project_id=project_id, task_id=task_id)


def task_requested_changes(project_id: int, task_id: int) -> str:
    """Return requested changes for one task."""
    return TASK_REQUESTED_CHANGES.format(project_id=project_id, task_id=task_id)


def calendar_items(project_id: int) -> str:
    """Return the project calendar items collection endpoint."""
    return CALENDAR_ITEMS.format(project_id=project_id)


def calendar_item(project_id: int, calendar_item_id: int) -> str:
    """Return one project calendar item endpoint."""
    return CALENDAR_ITEM.format(project_id=project_id, calendar_item_id=calendar_item_id)


def coordination_issues(project_id: int) -> str:
    """Return the project coordination issues collection endpoint."""
    return COORDINATION_ISSUES.format(project_id=project_id)


def coordination_issue(project_id: int, coordination_issue_id: int) -> str:
    """Return one project coordination issue endpoint."""
    return COORDINATION_ISSUE.format(
        project_id=project_id,
        coordination_issue_id=coordination_issue_id,
    )


def coordination_issue_change_history(project_id: int, coordination_issue_id: int) -> str:
    """Return change history for one coordination issue."""
    return COORDINATION_ISSUE_CHANGE_HISTORY.format(
        project_id=project_id,
        coordination_issue_id=coordination_issue_id,
    )


def coordination_issue_activity_feed(project_id: int, coordination_issue_id: int) -> str:
    """Return activity feed items for one coordination issue."""
    return COORDINATION_ISSUE_ACTIVITY_FEED.format(
        project_id=project_id,
        coordination_issue_id=coordination_issue_id,
    )


def coordination_issue_filter_options(project_id: int) -> str:
    """Return read-only coordination issue filter options."""
    return COORDINATION_ISSUE_FILTER_OPTIONS.format(project_id=project_id)


def forms(project_id: int) -> str:
    """Return the project forms collection endpoint."""
    return FORMS.format(project_id=project_id)


def form(project_id: int, form_id: int) -> str:
    """Return one project form endpoint."""
    return FORM.format(project_id=project_id, form_id=form_id)


def form_templates(project_id: int) -> str:
    """Return project form templates."""
    return FORM_TEMPLATES.format(project_id=project_id)


def action_plans(project_id: int) -> str:
    """Return the project action plans collection endpoint."""
    return ACTION_PLANS.format(project_id=project_id)


def action_plan(project_id: int, action_plan_id: int) -> str:
    """Return one project action plan endpoint."""
    return ACTION_PLAN.format(project_id=project_id, action_plan_id=action_plan_id)


def action_plan_change_history_events(project_id: int, action_plan_id: int) -> str:
    """Return change history events for one action plan."""
    return ACTION_PLAN_CHANGE_HISTORY_EVENTS.format(
        project_id=project_id,
        action_plan_id=action_plan_id,
    )


class Endpoints:
    """Backward-compatible namespace for endpoint path templates."""

    COMPANIES = COMPANIES
    PROJECTS = PROJECTS
    RFIS = RFIS
    RFI = RFI
    SUBMITTALS = SUBMITTALS
    SUBMITTAL = SUBMITTAL
    DOCUMENT_FOLDERS = DOCUMENT_FOLDERS
    DOCUMENT_FOLDER = DOCUMENT_FOLDER
    DOCUMENTS = DOCUMENTS
    DOCUMENT = DOCUMENT
    DRAWINGS = DRAWINGS
    DRAWING = DRAWING
    DRAWING_AREAS = DRAWING_AREAS
    DRAWING_AREA = DRAWING_AREA
    DRAWING_DISCIPLINES = DRAWING_DISCIPLINES
    DRAWING_REVISIONS = DRAWING_REVISIONS
    IMAGE_CATEGORIES = IMAGE_CATEGORIES
    IMAGE_CATEGORY = IMAGE_CATEGORY
    IMAGES = IMAGES
    IMAGE = IMAGE
    DAILY_LOG_COUNTS = DAILY_LOG_COUNTS
    DAILY_LOG_HEADERS = DAILY_LOG_HEADERS
    DAILY_LOG_TYPES = DAILY_LOG_TYPES
    DELAY_LOG_TYPES = DELAY_LOG_TYPES
    SPECIFICATION_SETS = SPECIFICATION_SETS
    SPECIFICATION_SET_V1 = SPECIFICATION_SET_V1
    SPECIFICATION_SECTIONS = SPECIFICATION_SECTIONS
    SPECIFICATION_SECTION_REVISIONS = SPECIFICATION_SECTION_REVISIONS
    SPECIFICATION_SECTION_REVISION = SPECIFICATION_SECTION_REVISION
    SPECIFICATION_SECTION_REVISION_DOWNLOAD = SPECIFICATION_SECTION_REVISION_DOWNLOAD
    OBSERVATION_ITEMS = OBSERVATION_ITEMS
    OBSERVATION_ITEM = OBSERVATION_ITEM
    PUNCH_ITEMS = PUNCH_ITEMS
    PUNCH_ITEM = PUNCH_ITEM
    GENERIC_TOOLS = GENERIC_TOOLS
    GENERIC_TOOL = GENERIC_TOOL
    GENERIC_TOOL_ITEMS = GENERIC_TOOL_ITEMS
    GENERIC_TOOL_ITEM = GENERIC_TOOL_ITEM
    MEETINGS = MEETINGS
    MEETING = MEETING
    CHECKLISTS = CHECKLISTS
    CHECKLIST = CHECKLIST
    INCIDENTS = INCIDENTS
    INCIDENT = INCIDENT
    PROJECT_INCIDENT_CONFIGURATION = PROJECT_INCIDENT_CONFIGURATION
    COMPANY_USERS = COMPANY_USERS
    COMPANY_USER = COMPANY_USER
    PROJECT_USERS = PROJECT_USERS
    PROJECT_USER = PROJECT_USER
    PROJECT_TOOLS = PROJECT_TOOLS
    PROJECT_TOOL = PROJECT_TOOL
    VENDORS = VENDORS
    VENDOR = VENDOR
    DEPARTMENTS = DEPARTMENTS
    DEPARTMENT = DEPARTMENT
    PROJECT_DISTRIBUTION_GROUPS = PROJECT_DISTRIBUTION_GROUPS
    PROJECT_DISTRIBUTION_GROUP = PROJECT_DISTRIBUTION_GROUP
    LOCATIONS = LOCATIONS
    LOCATION = LOCATION
    CHANGE_EVENTS = CHANGE_EVENTS
    CHANGE_EVENT = CHANGE_EVENT
    CHANGE_EVENT_STATUSES = CHANGE_EVENT_STATUSES
    CHANGE_EVENT_TYPES = CHANGE_EVENT_TYPES
    CHANGE_EVENT_SETTINGS = CHANGE_EVENT_SETTINGS
    PRIME_CHANGE_ORDERS = PRIME_CHANGE_ORDERS
    PRIME_CHANGE_ORDER = PRIME_CHANGE_ORDER
    COMMITMENT_CHANGE_ORDERS = COMMITMENT_CHANGE_ORDERS
    COMMITMENT_CHANGE_ORDER = COMMITMENT_CHANGE_ORDER
    CHANGE_ORDER_PACKAGES = CHANGE_ORDER_PACKAGES
    CHANGE_ORDER_PACKAGE = CHANGE_ORDER_PACKAGE
    DIRECT_COSTS = DIRECT_COSTS
    DIRECT_COST = DIRECT_COST
    BUDGET_VIEWS = BUDGET_VIEWS
    BUDGET_VIEW = BUDGET_VIEW
    BUDGET_DETAIL_COLUMNS = BUDGET_DETAIL_COLUMNS
    BUDGET_DETAILS = BUDGET_DETAILS
    BUDGET_VIEW_SUMMARY_ROWS = BUDGET_VIEW_SUMMARY_ROWS
    COST_CODES = COST_CODES
    STANDARD_COST_CODES = STANDARD_COST_CODES
    WBS_CODES = WBS_CODES
    COMMITMENTS = COMMITMENTS
    COMMITMENT = COMMITMENT
    PRIME_CONTRACTS = PRIME_CONTRACTS
    PRIME_CONTRACT = PRIME_CONTRACT
    PRIME_CONTRACT_LINE_ITEMS = PRIME_CONTRACT_LINE_ITEMS
    PRIME_CONTRACT_SUMMARY = PRIME_CONTRACT_SUMMARY
    COMMITMENT_CONTRACTS = COMMITMENT_CONTRACTS
    COMMITMENT_CONTRACT = COMMITMENT_CONTRACT
    PURCHASE_ORDER_CONTRACTS = PURCHASE_ORDER_CONTRACTS
    PURCHASE_ORDER_CONTRACT = PURCHASE_ORDER_CONTRACT
    WORK_ORDER_CONTRACTS = WORK_ORDER_CONTRACTS
    WORK_ORDER_CONTRACT = WORK_ORDER_CONTRACT
    OWNER_INVOICES = OWNER_INVOICES
    OWNER_INVOICE = OWNER_INVOICE
    OWNER_INVOICE_LINE_ITEMS = OWNER_INVOICE_LINE_ITEMS
    SUBCONTRACTOR_INVOICES = SUBCONTRACTOR_INVOICES
    SUBCONTRACTOR_INVOICE = SUBCONTRACTOR_INVOICE
    REQUISITION_CONTRACT_ITEMS = REQUISITION_CONTRACT_ITEMS
    REQUISITION_CONTRACT_DETAIL_ITEMS = REQUISITION_CONTRACT_DETAIL_ITEMS
    REQUISITION_CHANGE_ORDER_ITEMS = REQUISITION_CHANGE_ORDER_ITEMS
    CONTRACT_PAYMENTS = CONTRACT_PAYMENTS
    CONTRACT_PAYMENT = CONTRACT_PAYMENT
    BILLING_PERIODS = BILLING_PERIODS
    BILLING_PERIOD = BILLING_PERIOD
    COST_TYPES = COST_TYPES
    TAX_CODES = TAX_CODES
    PROJECT_SCHEDULE = PROJECT_SCHEDULE
    SCHEDULE_SETTINGS = SCHEDULE_SETTINGS
    SCHEDULE_TYPE = SCHEDULE_TYPE
    SCHEDULE_INTEGRATION = SCHEDULE_INTEGRATION
    SCHEDULE_IMPORT_STATUS = SCHEDULE_IMPORT_STATUS
    SCHEDULE_RESOURCE_ASSIGNMENTS = SCHEDULE_RESOURCE_ASSIGNMENTS
    SCHEDULE_RESOURCE_ASSIGNMENT = SCHEDULE_RESOURCE_ASSIGNMENT
    TASKS = TASKS
    TASK = TASK
    TASK_REQUESTED_CHANGES = TASK_REQUESTED_CHANGES
    CALENDAR_ITEMS = CALENDAR_ITEMS
    CALENDAR_ITEM = CALENDAR_ITEM
    COORDINATION_ISSUES = COORDINATION_ISSUES
    COORDINATION_ISSUE = COORDINATION_ISSUE
    COORDINATION_ISSUE_CHANGE_HISTORY = COORDINATION_ISSUE_CHANGE_HISTORY
    COORDINATION_ISSUE_ACTIVITY_FEED = COORDINATION_ISSUE_ACTIVITY_FEED
    COORDINATION_ISSUE_FILTER_OPTIONS = COORDINATION_ISSUE_FILTER_OPTIONS
    FORMS = FORMS
    FORM = FORM
    FORM_TEMPLATES = FORM_TEMPLATES
    ACTION_PLANS = ACTION_PLANS
    ACTION_PLAN = ACTION_PLAN
    ACTION_PLAN_CHANGE_HISTORY_EVENTS = ACTION_PLAN_CHANGE_HISTORY_EVENTS
