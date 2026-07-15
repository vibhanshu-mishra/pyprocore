"""Static agent tool registry for PyProcore.

The registry is metadata only. It does not execute tools, read credentials,
load ``.env`` files, or call the Procore API.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from pyprocore.agent.models import (
    AgentManifest,
    AgentTool,
    AgentToolCategory,
    AgentToolPermission,
    AgentToolRegistry,
    AgentToolSafety,
)

REGISTRY_VERSION = "1"


class AgentToolNotFoundError(LookupError):
    """Raised when an agent tool name is not registered."""


def _object_schema(properties: dict[str, dict[str, Any]], required: list[str]) -> dict[str, Any]:
    """Return a small JSON-schema-like object definition."""
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


def _array_output(item_ref: str) -> dict[str, Any]:
    """Return a simple array output schema."""
    return {"type": "array", "items": {"$ref": item_ref}}


def _model_output(model_name: str) -> dict[str, Any]:
    """Return a simple typed model output schema."""
    return {"type": "object", "model": model_name}


def _resource_tool(
    *,
    name: str,
    title: str,
    description: str,
    input_schema: dict[str, Any],
    output_schema: dict[str, Any],
    service_path: str,
    operation_path: str,
    cli_command: str,
    examples: list[str],
    category: AgentToolCategory = AgentToolCategory.RESOURCE,
) -> AgentTool:
    """Create metadata for a read-only Procore API tool."""
    return AgentTool(
        name=name,
        title=title,
        description=description,
        category=category,
        input_schema=input_schema,
        output_schema=output_schema,
        permissions=[AgentToolPermission.READ_PROCORE],
        requires_auth=True,
        calls_live_api=True,
        produces_files=False,
        side_effects=[],
        safety_level=AgentToolSafety.READ_ONLY,
        service_path=service_path,
        operation_path=operation_path,
        cli_command=cli_command,
        examples=examples,
    )


def _workflow_tool(
    *,
    name: str,
    title: str,
    description: str,
    input_schema: dict[str, Any],
    output_schema: dict[str, Any],
    operation_path: str,
    cli_command: str,
    examples: list[str],
    calls_live_api: bool,
    permissions: list[AgentToolPermission] | None = None,
) -> AgentTool:
    """Create metadata for a local workflow/export tool."""
    return AgentTool(
        name=name,
        title=title,
        description=description,
        category=AgentToolCategory.WORKFLOW if calls_live_api else AgentToolCategory.LOCAL_EXPORT,
        input_schema=input_schema,
        output_schema=output_schema,
        permissions=permissions
        or [AgentToolPermission.READ_PROCORE, AgentToolPermission.WRITE_LOCAL_FILES],
        requires_auth=calls_live_api,
        calls_live_api=calls_live_api,
        produces_files=True,
        side_effects=["Creates local output files only."],
        safety_level=AgentToolSafety.LOCAL_FILE_OUTPUT,
        service_path="pyprocore.workflows",
        operation_path=operation_path,
        cli_command=cli_command,
        examples=examples,
    )


def _project_id_schema() -> dict[str, Any]:
    """Return the common project ID input schema."""
    return _object_schema({"project_id": {"type": "integer"}}, ["project_id"])


def _project_company_schema() -> dict[str, Any]:
    """Return the common project plus optional company input schema."""
    return _object_schema(
        {
            "project_id": {"type": "integer"},
            "company_id": {"type": "integer"},
        },
        ["project_id"],
    )


def _company_schema() -> dict[str, Any]:
    """Return the common optional company input schema."""
    return _object_schema({"company_id": {"type": "integer"}}, [])


def _company_user_search_schema() -> dict[str, Any]:
    """Return common company-user search input schema."""
    return _object_schema(
        {
            "company_id": {"type": "integer"},
            "name": {"type": "string"},
            "email": {"type": "string"},
            "query": {"type": "string"},
        },
        [],
    )


def _project_user_search_schema() -> dict[str, Any]:
    """Return common project-user search input schema."""
    return _object_schema(
        {
            "project_id": {"type": "integer"},
            "company_id": {"type": "integer"},
            "name": {"type": "string"},
            "email": {"type": "string"},
            "query": {"type": "string"},
        },
        ["project_id"],
    )


def _company_name_number_search_schema() -> dict[str, Any]:
    """Return common company/name/number search input schema."""
    return _object_schema(
        {
            "company_id": {"type": "integer"},
            "name": {"type": "string"},
            "number": {"type": "string"},
            "query": {"type": "string"},
        },
        [],
    )


def _company_name_code_search_schema() -> dict[str, Any]:
    """Return common company/name/code search input schema."""
    return _object_schema(
        {
            "company_id": {"type": "integer"},
            "name": {"type": "string"},
            "code": {"type": "string"},
            "query": {"type": "string"},
        },
        [],
    )


def _project_name_search_schema() -> dict[str, Any]:
    """Return common project/company/name search input schema."""
    return _object_schema(
        {
            "project_id": {"type": "integer"},
            "company_id": {"type": "integer"},
            "name": {"type": "string"},
            "query": {"type": "string"},
        },
        ["project_id"],
    )


def _project_name_code_search_schema() -> dict[str, Any]:
    """Return common project/company/name/code search input schema."""
    return _object_schema(
        {
            "project_id": {"type": "integer"},
            "company_id": {"type": "integer"},
            "name": {"type": "string"},
            "code": {"type": "string"},
            "query": {"type": "string"},
        },
        ["project_id"],
    )


def _project_name_number_search_schema() -> dict[str, Any]:
    """Return common project/company/name/number search input schema."""
    return _object_schema(
        {
            "project_id": {"type": "integer"},
            "company_id": {"type": "integer"},
            "name": {"type": "string"},
            "number": {"type": "string"},
        },
        ["project_id"],
    )


def _project_item_schema(item_name: str) -> dict[str, Any]:
    """Return common project/company/item input schema."""
    return _object_schema(
        {
            "project_id": {"type": "integer"},
            "company_id": {"type": "integer"},
            item_name: {"type": "integer"},
        },
        ["project_id", item_name],
    )


def _budget_view_schema() -> dict[str, Any]:
    """Return project/company/budget-view input schema."""
    return _project_item_schema("budget_view_id")


def _project_company_search_schema() -> dict[str, Any]:
    """Return common project/company search input schema."""
    return _object_schema(
        {
            "project_id": {"type": "integer"},
            "company_id": {"type": "integer"},
            "number": {"type": "string"},
            "title": {"type": "string"},
            "query": {"type": "string"},
        },
        ["project_id"],
    )


def _generic_tool_item_schema() -> dict[str, Any]:
    """Return project/company/generic-tool input schema."""
    return _object_schema(
        {
            "project_id": {"type": "integer"},
            "company_id": {"type": "integer"},
            "generic_tool_id": {"type": "integer"},
        },
        ["project_id", "generic_tool_id"],
    )


def _build_tools() -> list[AgentTool]:
    """Build the complete static tool list."""
    tools = [
        _resource_tool(
            name="procore.list_companies",
            title="List Companies",
            description="List Procore companies available to the configured token.",
            input_schema=_object_schema({}, []),
            output_schema=_array_output("Company"),
            service_path="pyprocore.services.companies",
            operation_path="pyprocore.services.companies.list_companies",
            cli_command="procore-sdk companies",
            examples=["companies = list_companies()"],
        ),
        _resource_tool(
            name="procore.find_company",
            title="Find Company",
            description="Find one company by case-insensitive name matching.",
            input_schema=_object_schema({"name": {"type": "string"}}, ["name"]),
            output_schema=_model_output("Company"),
            service_path="pyprocore.services.search",
            operation_path="pyprocore.services.search.find_company",
            cli_command="procore-sdk find-company NAME",
            examples=['company = find_company("Tracker")'],
            category=AgentToolCategory.SEARCH,
        ),
        _resource_tool(
            name="procore.list_projects",
            title="List Projects",
            description="List projects for a company.",
            input_schema=_object_schema({"company_id": {"type": "integer"}}, ["company_id"]),
            output_schema=_array_output("Project"),
            service_path="pyprocore.services.projects",
            operation_path="pyprocore.services.projects.list_projects",
            cli_command="procore-sdk projects --company-id COMPANY_ID",
            examples=["projects = list_projects(company_id)"],
        ),
        _resource_tool(
            name="procore.find_project",
            title="Find Project",
            description="Find one project by name, number, or partial text.",
            input_schema=_object_schema(
                {
                    "name": {"type": "string"},
                    "number": {"type": "string"},
                    "company_id": {"type": "integer"},
                },
                [],
            ),
            output_schema=_model_output("Project"),
            service_path="pyprocore.services.search",
            operation_path="pyprocore.services.search.find_project",
            cli_command="procore-sdk find-project QUERY",
            examples=['project = find_project("Hospital")', 'project = find_project(number="001")'],
            category=AgentToolCategory.SEARCH,
        ),
        _resource_tool(
            name="procore.list_rfis",
            title="List RFIs",
            description="List RFIs for a project.",
            input_schema=_project_id_schema(),
            output_schema=_array_output("RFI"),
            service_path="pyprocore.services.rfis",
            operation_path="pyprocore.services.rfis.list_rfis",
            cli_command="procore-sdk rfis --project PROJECT_ID",
            examples=["rfis = list_rfis(project_id)"],
        ),
        _resource_tool(
            name="procore.get_rfi",
            title="Get RFI",
            description="Get one RFI by project ID and RFI ID.",
            input_schema=_object_schema(
                {"project_id": {"type": "integer"}, "rfi_id": {"type": "integer"}},
                ["project_id", "rfi_id"],
            ),
            output_schema=_model_output("RFI"),
            service_path="pyprocore.services.rfis",
            operation_path="pyprocore.services.rfis.get_rfi",
            cli_command="procore-sdk rfi --project PROJECT_ID --id RFI_ID",
            examples=["rfi = get_rfi(project_id, rfi_id)"],
        ),
        _resource_tool(
            name="procore.find_rfi",
            title="Find RFI",
            description="Find one RFI in a project by RFI number.",
            input_schema=_object_schema(
                {"project_id": {"type": "integer"}, "number": {"type": "string"}},
                ["project_id", "number"],
            ),
            output_schema=_model_output("RFI"),
            service_path="pyprocore.services.search",
            operation_path="pyprocore.services.search.find_rfi",
            cli_command="procore-sdk find-rfi --project PROJECT_ID --number NUMBER",
            examples=['rfi = find_rfi(project_id, number="15")'],
            category=AgentToolCategory.SEARCH,
        ),
        _resource_tool(
            name="procore.list_submittals",
            title="List Submittals",
            description="List submittals for a project.",
            input_schema=_project_id_schema(),
            output_schema=_array_output("Submittal"),
            service_path="pyprocore.services.submittals",
            operation_path="pyprocore.services.submittals.list_submittals",
            cli_command="procore-sdk submittals --project PROJECT_ID",
            examples=["submittals = list_submittals(project_id)"],
        ),
        _resource_tool(
            name="procore.get_submittal",
            title="Get Submittal",
            description="Get one submittal by project ID and submittal ID.",
            input_schema=_object_schema(
                {"project_id": {"type": "integer"}, "submittal_id": {"type": "integer"}},
                ["project_id", "submittal_id"],
            ),
            output_schema=_model_output("Submittal"),
            service_path="pyprocore.services.submittals",
            operation_path="pyprocore.services.submittals.get_submittal",
            cli_command="procore-sdk submittal --project PROJECT_ID --id SUBMITTAL_ID",
            examples=["submittal = get_submittal(project_id, submittal_id)"],
        ),
        _resource_tool(
            name="procore.find_submittal",
            title="Find Submittal",
            description="Find one submittal in a project by submittal number.",
            input_schema=_object_schema(
                {"project_id": {"type": "integer"}, "number": {"type": "string"}},
                ["project_id", "number"],
            ),
            output_schema=_model_output("Submittal"),
            service_path="pyprocore.services.search",
            operation_path="pyprocore.services.search.find_submittal",
            cli_command="procore-sdk find-submittal --project PROJECT_ID --number NUMBER",
            examples=['submittal = find_submittal(project_id, number="27")'],
            category=AgentToolCategory.SEARCH,
        ),
        _resource_tool(
            name="procore.list_observations",
            title="List Observations",
            description="List observation items for a project.",
            input_schema=_project_company_schema(),
            output_schema=_array_output("Observation"),
            service_path="pyprocore.services.observations",
            operation_path="pyprocore.services.observations.list_observations",
            cli_command="procore-sdk observations --project PROJECT_ID --company-id COMPANY_ID",
            examples=["observations = list_observations(company_id, project_id)"],
        ),
        _resource_tool(
            name="procore.get_observation",
            title="Get Observation",
            description="Get one observation item by project ID and observation ID.",
            input_schema=_object_schema(
                {
                    "project_id": {"type": "integer"},
                    "company_id": {"type": "integer"},
                    "observation_id": {"type": "integer"},
                },
                ["project_id", "observation_id"],
            ),
            output_schema=_model_output("Observation"),
            service_path="pyprocore.services.observations",
            operation_path="pyprocore.services.observations.get_observation",
            cli_command="procore-sdk observation --project PROJECT_ID --id OBSERVATION_ID",
            examples=["observation = get_observation(company_id, project_id, observation_id)"],
        ),
        _resource_tool(
            name="procore.find_observation",
            title="Find Observation",
            description="Find one observation by number, title, or text.",
            input_schema=_project_company_search_schema(),
            output_schema=_model_output("Observation"),
            service_path="pyprocore.services.search",
            operation_path="pyprocore.services.search.find_observation",
            cli_command="procore-sdk find-observation --project PROJECT_ID --number NUMBER",
            examples=['observation = find_observation(company_id, project_id, number="15")'],
            category=AgentToolCategory.SEARCH,
        ),
        _resource_tool(
            name="procore.list_punch_items",
            title="List Punch Items",
            description="List punch items for a project.",
            input_schema=_project_company_schema(),
            output_schema=_array_output("PunchItem"),
            service_path="pyprocore.services.punch_items",
            operation_path="pyprocore.services.punch_items.list_punch_items",
            cli_command="procore-sdk punch-items --project PROJECT_ID --company-id COMPANY_ID",
            examples=["punch_items = list_punch_items(company_id, project_id)"],
        ),
        _resource_tool(
            name="procore.get_punch_item",
            title="Get Punch Item",
            description="Get one punch item by project ID and punch item ID.",
            input_schema=_object_schema(
                {
                    "project_id": {"type": "integer"},
                    "company_id": {"type": "integer"},
                    "punch_item_id": {"type": "integer"},
                },
                ["project_id", "punch_item_id"],
            ),
            output_schema=_model_output("PunchItem"),
            service_path="pyprocore.services.punch_items",
            operation_path="pyprocore.services.punch_items.get_punch_item",
            cli_command="procore-sdk punch-item --project PROJECT_ID --id PUNCH_ITEM_ID",
            examples=["punch_item = get_punch_item(company_id, project_id, punch_item_id)"],
        ),
        _resource_tool(
            name="procore.find_punch_item",
            title="Find Punch Item",
            description="Find one punch item by number, title, or text.",
            input_schema=_project_company_search_schema(),
            output_schema=_model_output("PunchItem"),
            service_path="pyprocore.services.search",
            operation_path="pyprocore.services.search.find_punch_item",
            cli_command="procore-sdk find-punch-item --project PROJECT_ID --number NUMBER",
            examples=['punch_item = find_punch_item(company_id, project_id, number="2")'],
            category=AgentToolCategory.SEARCH,
        ),
        _resource_tool(
            name="procore.list_generic_tools",
            title="List Generic Tools",
            description="List Generic Tool metadata for a project.",
            input_schema=_project_company_schema(),
            output_schema=_array_output("GenericTool"),
            service_path="pyprocore.services.correspondence",
            operation_path="pyprocore.services.correspondence.list_generic_tools",
            cli_command="procore-sdk generic-tools --project PROJECT_ID --company-id COMPANY_ID",
            examples=["tools = list_generic_tools(company_id, project_id)"],
        ),
        _resource_tool(
            name="procore.list_correspondences",
            title="List Correspondences",
            description="List correspondence items for a Generic Tool.",
            input_schema=_generic_tool_item_schema(),
            output_schema=_array_output("Correspondence"),
            service_path="pyprocore.services.correspondence",
            operation_path="pyprocore.services.correspondence.list_correspondences",
            cli_command=(
                "procore-sdk correspondences --project PROJECT_ID "
                "--generic-tool-id GENERIC_TOOL_ID"
            ),
            examples=["items = list_correspondences(company_id, project_id, generic_tool_id)"],
        ),
        _resource_tool(
            name="procore.get_correspondence",
            title="Get Correspondence",
            description="Get one Generic Tool correspondence item.",
            input_schema=_object_schema(
                {
                    "project_id": {"type": "integer"},
                    "company_id": {"type": "integer"},
                    "correspondence_id": {"type": "integer"},
                },
                ["project_id", "correspondence_id"],
            ),
            output_schema=_model_output("Correspondence"),
            service_path="pyprocore.services.correspondence",
            operation_path="pyprocore.services.correspondence.get_correspondence",
            cli_command="procore-sdk correspondence --project PROJECT_ID --id CORRESPONDENCE_ID",
            examples=["item = get_correspondence(company_id, project_id, correspondence_id)"],
        ),
        _resource_tool(
            name="procore.find_correspondence",
            title="Find Correspondence",
            description="Find one Generic Tool correspondence item by number, title, or text.",
            input_schema=_object_schema(
                {
                    "project_id": {"type": "integer"},
                    "company_id": {"type": "integer"},
                    "generic_tool_id": {"type": "integer"},
                    "number": {"type": "string"},
                    "title": {"type": "string"},
                    "query": {"type": "string"},
                },
                ["project_id", "generic_tool_id"],
            ),
            output_schema=_model_output("Correspondence"),
            service_path="pyprocore.services.search",
            operation_path="pyprocore.services.search.find_correspondence",
            cli_command=(
                "procore-sdk find-correspondence --project PROJECT_ID "
                "--generic-tool-id GENERIC_TOOL_ID --query TEXT"
            ),
            examples=[
                "item = find_correspondence(company_id, project_id, generic_tool_id, query='RFI')"
            ],
            category=AgentToolCategory.SEARCH,
        ),
        _resource_tool(
            name="procore.list_meetings",
            title="List Meetings",
            description="List meetings for a project.",
            input_schema=_project_company_schema(),
            output_schema=_array_output("Meeting"),
            service_path="pyprocore.services.operations",
            operation_path="pyprocore.services.operations.list_meetings",
            cli_command="procore-sdk meetings --project PROJECT_ID --company-id COMPANY_ID",
            examples=["meetings = list_meetings(company_id, project_id)"],
        ),
        _resource_tool(
            name="procore.get_meeting",
            title="Get Meeting",
            description="Get one meeting by project ID and meeting ID.",
            input_schema=_object_schema(
                {
                    "project_id": {"type": "integer"},
                    "company_id": {"type": "integer"},
                    "meeting_id": {"type": "integer"},
                },
                ["project_id", "meeting_id"],
            ),
            output_schema=_model_output("Meeting"),
            service_path="pyprocore.services.operations",
            operation_path="pyprocore.services.operations.get_meeting",
            cli_command="procore-sdk meeting --project PROJECT_ID --id MEETING_ID",
            examples=["meeting = get_meeting(company_id, project_id, meeting_id)"],
        ),
        _resource_tool(
            name="procore.find_meeting",
            title="Find Meeting",
            description="Find one meeting by number, title, or text.",
            input_schema=_project_company_search_schema(),
            output_schema=_model_output("Meeting"),
            service_path="pyprocore.services.search",
            operation_path="pyprocore.services.search.find_meeting",
            cli_command="procore-sdk find-meeting --project PROJECT_ID --number NUMBER",
            examples=['meeting = find_meeting(company_id, project_id, number="1")'],
            category=AgentToolCategory.SEARCH,
        ),
        _resource_tool(
            name="procore.list_inspections",
            title="List Inspections",
            description="List checklist-backed inspections for a project.",
            input_schema=_project_company_schema(),
            output_schema=_array_output("Inspection"),
            service_path="pyprocore.services.operations",
            operation_path="pyprocore.services.operations.list_inspections",
            cli_command="procore-sdk inspections --project PROJECT_ID --company-id COMPANY_ID",
            examples=["inspections = list_inspections(company_id, project_id)"],
        ),
        _resource_tool(
            name="procore.get_inspection",
            title="Get Inspection",
            description="Get one checklist-backed inspection by project ID and inspection ID.",
            input_schema=_object_schema(
                {
                    "project_id": {"type": "integer"},
                    "company_id": {"type": "integer"},
                    "inspection_id": {"type": "integer"},
                },
                ["project_id", "inspection_id"],
            ),
            output_schema=_model_output("Inspection"),
            service_path="pyprocore.services.operations",
            operation_path="pyprocore.services.operations.get_inspection",
            cli_command="procore-sdk inspection --project PROJECT_ID --id INSPECTION_ID",
            examples=["inspection = get_inspection(company_id, project_id, inspection_id)"],
        ),
        _resource_tool(
            name="procore.find_inspection",
            title="Find Inspection",
            description="Find one checklist-backed inspection by number, title, or text.",
            input_schema=_project_company_search_schema(),
            output_schema=_model_output("Inspection"),
            service_path="pyprocore.services.search",
            operation_path="pyprocore.services.search.find_inspection",
            cli_command="procore-sdk find-inspection --project PROJECT_ID --query TEXT",
            examples=["inspection = find_inspection(company_id, project_id, query='safety')"],
            category=AgentToolCategory.SEARCH,
        ),
        _resource_tool(
            name="procore.list_incidents",
            title="List Incidents",
            description="List incidents for a project.",
            input_schema=_project_company_schema(),
            output_schema=_array_output("Incident"),
            service_path="pyprocore.services.operations",
            operation_path="pyprocore.services.operations.list_incidents",
            cli_command="procore-sdk incidents --project PROJECT_ID --company-id COMPANY_ID",
            examples=["incidents = list_incidents(company_id, project_id)"],
        ),
        _resource_tool(
            name="procore.get_incident",
            title="Get Incident",
            description="Get one incident by project ID and incident ID.",
            input_schema=_object_schema(
                {
                    "project_id": {"type": "integer"},
                    "company_id": {"type": "integer"},
                    "incident_id": {"type": "integer"},
                },
                ["project_id", "incident_id"],
            ),
            output_schema=_model_output("Incident"),
            service_path="pyprocore.services.operations",
            operation_path="pyprocore.services.operations.get_incident",
            cli_command="procore-sdk incident --project PROJECT_ID --id INCIDENT_ID",
            examples=["incident = get_incident(company_id, project_id, incident_id)"],
        ),
        _resource_tool(
            name="procore.get_project_incident_configuration",
            title="Get Project Incident Configuration",
            description="Get project incident configuration metadata.",
            input_schema=_project_company_schema(),
            output_schema=_model_output("IncidentConfiguration"),
            service_path="pyprocore.services.operations",
            operation_path=("pyprocore.services.operations.get_project_incident_configuration"),
            cli_command=(
                "procore-sdk incident-configuration --project PROJECT_ID " "--company-id COMPANY_ID"
            ),
            examples=["configuration = get_project_incident_configuration(company_id, project_id)"],
        ),
        _resource_tool(
            name="procore.find_incident",
            title="Find Incident",
            description="Find one incident by number, title, or text.",
            input_schema=_project_company_search_schema(),
            output_schema=_model_output("Incident"),
            service_path="pyprocore.services.search",
            operation_path="pyprocore.services.search.find_incident",
            cli_command="procore-sdk find-incident --project PROJECT_ID --number NUMBER",
            examples=['incident = find_incident(company_id, project_id, number="1")'],
            category=AgentToolCategory.SEARCH,
        ),
        _resource_tool(
            name="procore.list_company_users",
            title="List Company Users",
            description="List read-only company directory users.",
            input_schema=_company_schema(),
            output_schema=_array_output("CompanyUser"),
            service_path="pyprocore.services.directory",
            operation_path="pyprocore.services.directory.list_company_users",
            cli_command="procore-sdk company-users --company-id COMPANY_ID",
            examples=["users = list_company_users(company_id)"],
        ),
        _resource_tool(
            name="procore.get_company_user",
            title="Get Company User",
            description="Get one read-only company directory user.",
            input_schema=_object_schema(
                {"company_id": {"type": "integer"}, "user_id": {"type": "integer"}},
                ["user_id"],
            ),
            output_schema=_model_output("CompanyUser"),
            service_path="pyprocore.services.directory",
            operation_path="pyprocore.services.directory.get_company_user",
            cli_command="procore-sdk company-user --company-id COMPANY_ID --id USER_ID",
            examples=["user = get_company_user(company_id, user_id)"],
        ),
        _resource_tool(
            name="procore.find_company_user",
            title="Find Company User",
            description="Find one company user by name, email, or text.",
            input_schema=_company_user_search_schema(),
            output_schema=_model_output("CompanyUser"),
            service_path="pyprocore.services.search",
            operation_path="pyprocore.services.search.find_company_user",
            cli_command="procore-sdk find-company-user --company-id COMPANY_ID --email EMAIL",
            examples=["user = find_company_user(company_id, email='person@example.com')"],
            category=AgentToolCategory.SEARCH,
        ),
        _resource_tool(
            name="procore.list_project_users",
            title="List Project Users",
            description="List read-only project directory users.",
            input_schema=_project_company_schema(),
            output_schema=_array_output("ProjectUser"),
            service_path="pyprocore.services.directory",
            operation_path="pyprocore.services.directory.list_project_users",
            cli_command="procore-sdk project-users --project PROJECT_ID --company-id COMPANY_ID",
            examples=["users = list_project_users(company_id, project_id)"],
        ),
        _resource_tool(
            name="procore.get_project_user",
            title="Get Project User",
            description="Get one read-only project directory user.",
            input_schema=_object_schema(
                {
                    "project_id": {"type": "integer"},
                    "company_id": {"type": "integer"},
                    "user_id": {"type": "integer"},
                },
                ["project_id", "user_id"],
            ),
            output_schema=_model_output("ProjectUser"),
            service_path="pyprocore.services.directory",
            operation_path="pyprocore.services.directory.get_project_user",
            cli_command="procore-sdk project-user --project PROJECT_ID --id USER_ID",
            examples=["user = get_project_user(company_id, project_id, user_id)"],
        ),
        _resource_tool(
            name="procore.find_project_user",
            title="Find Project User",
            description="Find one project user by name, email, or text.",
            input_schema=_project_user_search_schema(),
            output_schema=_model_output("ProjectUser"),
            service_path="pyprocore.services.search",
            operation_path="pyprocore.services.search.find_project_user",
            cli_command="procore-sdk find-project-user --project PROJECT_ID --name NAME",
            examples=["user = find_project_user(company_id, project_id, name='Alex')"],
            category=AgentToolCategory.SEARCH,
        ),
        _resource_tool(
            name="procore.list_vendors",
            title="List Vendors",
            description="List read-only company vendors.",
            input_schema=_company_schema(),
            output_schema=_array_output("Vendor"),
            service_path="pyprocore.services.directory",
            operation_path="pyprocore.services.directory.list_vendors",
            cli_command="procore-sdk vendors --company-id COMPANY_ID",
            examples=["vendors = list_vendors(company_id)"],
        ),
        _resource_tool(
            name="procore.get_vendor",
            title="Get Vendor",
            description="Get one read-only vendor.",
            input_schema=_object_schema(
                {"company_id": {"type": "integer"}, "vendor_id": {"type": "integer"}},
                ["vendor_id"],
            ),
            output_schema=_model_output("Vendor"),
            service_path="pyprocore.services.directory",
            operation_path="pyprocore.services.directory.get_vendor",
            cli_command="procore-sdk vendor --company-id COMPANY_ID --id VENDOR_ID",
            examples=["vendor = get_vendor(company_id, vendor_id)"],
        ),
        _resource_tool(
            name="procore.find_vendor",
            title="Find Vendor",
            description="Find one vendor by name, number, or text.",
            input_schema=_company_name_number_search_schema(),
            output_schema=_model_output("Vendor"),
            service_path="pyprocore.services.search",
            operation_path="pyprocore.services.search.find_vendor",
            cli_command="procore-sdk find-vendor --company-id COMPANY_ID --name NAME",
            examples=["vendor = find_vendor(company_id, name='Concrete')"],
            category=AgentToolCategory.SEARCH,
        ),
        _resource_tool(
            name="procore.list_departments",
            title="List Departments",
            description="List read-only company departments.",
            input_schema=_company_schema(),
            output_schema=_array_output("Department"),
            service_path="pyprocore.services.directory",
            operation_path="pyprocore.services.directory.list_departments",
            cli_command="procore-sdk departments --company-id COMPANY_ID",
            examples=["departments = list_departments(company_id)"],
        ),
        _resource_tool(
            name="procore.get_department",
            title="Get Department",
            description="Get one read-only company department.",
            input_schema=_object_schema(
                {"company_id": {"type": "integer"}, "department_id": {"type": "integer"}},
                ["department_id"],
            ),
            output_schema=_model_output("Department"),
            service_path="pyprocore.services.directory",
            operation_path="pyprocore.services.directory.get_department",
            cli_command="procore-sdk department --company-id COMPANY_ID --id DEPARTMENT_ID",
            examples=["department = get_department(company_id, department_id)"],
        ),
        _resource_tool(
            name="procore.find_department",
            title="Find Department",
            description="Find one department by name, code, or text.",
            input_schema=_company_name_code_search_schema(),
            output_schema=_model_output("Department"),
            service_path="pyprocore.services.search",
            operation_path="pyprocore.services.search.find_department",
            cli_command="procore-sdk find-department --company-id COMPANY_ID --name NAME",
            examples=["department = find_department(company_id, name='Operations')"],
            category=AgentToolCategory.SEARCH,
        ),
        _resource_tool(
            name="procore.list_project_distribution_groups",
            title="List Project Distribution Groups",
            description="List read-only project distribution groups.",
            input_schema=_project_company_schema(),
            output_schema=_array_output("DistributionGroup"),
            service_path="pyprocore.services.directory",
            operation_path="pyprocore.services.directory.list_project_distribution_groups",
            cli_command=(
                "procore-sdk distribution-groups --project PROJECT_ID " "--company-id COMPANY_ID"
            ),
            examples=["groups = list_project_distribution_groups(company_id, project_id)"],
        ),
        _resource_tool(
            name="procore.get_project_distribution_group",
            title="Get Project Distribution Group",
            description="Get one read-only project distribution group.",
            input_schema=_object_schema(
                {
                    "project_id": {"type": "integer"},
                    "company_id": {"type": "integer"},
                    "distribution_group_id": {"type": "integer"},
                },
                ["project_id", "distribution_group_id"],
            ),
            output_schema=_model_output("DistributionGroup"),
            service_path="pyprocore.services.directory",
            operation_path="pyprocore.services.directory.get_project_distribution_group",
            cli_command="procore-sdk distribution-group --project PROJECT_ID --id GROUP_ID",
            examples=[
                (
                    "group = get_project_distribution_group("
                    "company_id, project_id, distribution_group_id)"
                )
            ],
        ),
        _resource_tool(
            name="procore.find_project_distribution_group",
            title="Find Project Distribution Group",
            description="Find one project distribution group by name or text.",
            input_schema=_project_name_search_schema(),
            output_schema=_model_output("DistributionGroup"),
            service_path="pyprocore.services.search",
            operation_path="pyprocore.services.search.find_project_distribution_group",
            cli_command="procore-sdk find-distribution-group --project PROJECT_ID --name NAME",
            examples=[
                "group = find_project_distribution_group(company_id, project_id, name='Team')"
            ],
            category=AgentToolCategory.SEARCH,
        ),
        _resource_tool(
            name="procore.list_locations",
            title="List Locations",
            description="List read-only project locations.",
            input_schema=_project_company_schema(),
            output_schema=_array_output("Location"),
            service_path="pyprocore.services.directory",
            operation_path="pyprocore.services.directory.list_locations",
            cli_command="procore-sdk locations --project PROJECT_ID --company-id COMPANY_ID",
            examples=["locations = list_locations(company_id, project_id)"],
        ),
        _resource_tool(
            name="procore.get_location",
            title="Get Location",
            description="Get one read-only project location.",
            input_schema=_object_schema(
                {
                    "project_id": {"type": "integer"},
                    "company_id": {"type": "integer"},
                    "location_id": {"type": "integer"},
                },
                ["project_id", "location_id"],
            ),
            output_schema=_model_output("Location"),
            service_path="pyprocore.services.directory",
            operation_path="pyprocore.services.directory.get_location",
            cli_command="procore-sdk location --project PROJECT_ID --id LOCATION_ID",
            examples=["location = get_location(company_id, project_id, location_id)"],
        ),
        _resource_tool(
            name="procore.find_location",
            title="Find Location",
            description="Find one project location by name, code, or text.",
            input_schema=_project_name_code_search_schema(),
            output_schema=_model_output("Location"),
            service_path="pyprocore.services.search",
            operation_path="pyprocore.services.search.find_location",
            cli_command="procore-sdk find-location --project PROJECT_ID --name NAME",
            examples=["location = find_location(company_id, project_id, name='Level 1')"],
            category=AgentToolCategory.SEARCH,
        ),
        _resource_tool(
            name="procore.list_documents",
            title="List Documents",
            description="List project documents, optionally within a folder.",
            input_schema=_project_company_schema(),
            output_schema=_array_output("Document"),
            service_path="pyprocore.services.documents",
            operation_path="pyprocore.services.documents.list_documents",
            cli_command="procore-sdk documents --project PROJECT_ID",
            examples=["documents = list_documents(project_id)"],
        ),
        _resource_tool(
            name="procore.get_document",
            title="Get Document",
            description="Get one project document by ID.",
            input_schema=_object_schema(
                {"project_id": {"type": "integer"}, "document_id": {"type": "integer"}},
                ["project_id", "document_id"],
            ),
            output_schema=_model_output("Document"),
            service_path="pyprocore.services.documents",
            operation_path="pyprocore.services.documents.get_document",
            cli_command="procore-sdk document --project PROJECT_ID --id DOCUMENT_ID",
            examples=["document = get_document(project_id, document_id)"],
        ),
        _resource_tool(
            name="procore.find_document",
            title="Find Document",
            description="Find one project document by name or filename.",
            input_schema=_object_schema(
                {
                    "project_id": {"type": "integer"},
                    "name": {"type": "string"},
                    "filename": {"type": "string"},
                },
                ["project_id"],
            ),
            output_schema=_model_output("Document"),
            service_path="pyprocore.services.search",
            operation_path="pyprocore.services.search.find_document",
            cli_command="procore-sdk find-document --project PROJECT_ID --name NAME",
            examples=['document = find_document(project_id, name="spec")'],
            category=AgentToolCategory.SEARCH,
        ),
        _resource_tool(
            name="procore.list_drawings",
            title="List Drawings",
            description="List drawings for a project or drawing area.",
            input_schema=_project_company_schema(),
            output_schema=_array_output("Drawing"),
            service_path="pyprocore.services.drawings",
            operation_path="pyprocore.services.drawings.list_drawings",
            cli_command="procore-sdk drawings PROJECT_ID",
            examples=["drawings = list_drawings(project_id)"],
        ),
        _resource_tool(
            name="procore.get_drawing",
            title="Get Drawing",
            description="Get one drawing by project ID and drawing ID.",
            input_schema=_object_schema(
                {
                    "project_id": {"type": "integer"},
                    "drawing_id": {"type": "integer"},
                    "drawing_area_id": {"type": "integer"},
                },
                ["project_id", "drawing_id"],
            ),
            output_schema=_model_output("Drawing"),
            service_path="pyprocore.services.drawings",
            operation_path="pyprocore.services.drawings.get_drawing",
            cli_command="procore-sdk drawing PROJECT_ID DRAWING_ID",
            examples=["drawing = get_drawing(project_id, drawing_id)"],
        ),
        _resource_tool(
            name="procore.find_drawing",
            title="Find Drawing",
            description="Find one drawing by number, title, or text.",
            input_schema=_object_schema(
                {
                    "project_id": {"type": "integer"},
                    "number": {"type": "string"},
                    "title": {"type": "string"},
                },
                ["project_id"],
            ),
            output_schema=_model_output("Drawing"),
            service_path="pyprocore.services.search",
            operation_path="pyprocore.services.search.find_drawing",
            cli_command="procore-sdk find-drawing PROJECT_ID --number NUMBER",
            examples=['drawing = find_drawing(project_id, number="A101")'],
            category=AgentToolCategory.SEARCH,
        ),
        _resource_tool(
            name="procore.list_specification_sections",
            title="List Specification Sections",
            description="List specification sections for a project.",
            input_schema=_project_company_schema(),
            output_schema=_array_output("SpecificationSection"),
            service_path="pyprocore.services.specifications",
            operation_path="pyprocore.services.specifications.list_specification_sections",
            cli_command="procore-sdk specification-sections PROJECT_ID",
            examples=["sections = list_specification_sections(project_id)"],
        ),
        _resource_tool(
            name="procore.find_specification_section",
            title="Find Specification Section",
            description="Find one specification section by number, title, or text.",
            input_schema=_object_schema(
                {
                    "project_id": {"type": "integer"},
                    "number": {"type": "string"},
                    "title": {"type": "string"},
                    "query": {"type": "string"},
                },
                ["project_id"],
            ),
            output_schema=_model_output("SpecificationSection"),
            service_path="pyprocore.services.search",
            operation_path="pyprocore.services.search.find_specification_section",
            cli_command="procore-sdk find-specification-section PROJECT_ID --number NUMBER",
            examples=['section = find_specification_section(project_id, number="033000")'],
            category=AgentToolCategory.SEARCH,
        ),
        _resource_tool(
            name="procore.list_photo_albums",
            title="List Photo Albums",
            description="List photo albums for a project.",
            input_schema=_project_company_schema(),
            output_schema=_array_output("PhotoAlbum"),
            service_path="pyprocore.services.photos",
            operation_path="pyprocore.services.photos.list_photo_albums",
            cli_command="procore-sdk photo-albums PROJECT_ID",
            examples=["albums = list_photo_albums(project_id)"],
        ),
        _resource_tool(
            name="procore.list_photos",
            title="List Photos",
            description="List project photos with optional album and date filters.",
            input_schema=_project_company_schema(),
            output_schema=_array_output("Photo"),
            service_path="pyprocore.services.photos",
            operation_path="pyprocore.services.photos.list_photos",
            cli_command="procore-sdk photos PROJECT_ID",
            examples=["photos = list_photos(project_id)"],
        ),
        _resource_tool(
            name="procore.list_daily_logs",
            title="List Daily Logs",
            description="List one type of Daily Log entries for a project.",
            input_schema=_object_schema(
                {
                    "project_id": {"type": "integer"},
                    "log_type": {"type": "string"},
                    "log_date": {"type": "string"},
                },
                ["project_id", "log_type"],
            ),
            output_schema=_array_output("DailyLog"),
            service_path="pyprocore.services.daily_logs",
            operation_path="pyprocore.services.daily_logs.list_daily_logs",
            cli_command="procore-sdk daily-logs PROJECT_ID LOG_TYPE",
            examples=['logs = list_daily_logs(project_id, "manpower")'],
        ),
        _workflow_tool(
            name="procore.build_project_context_package",
            title="Build Project Context Package",
            description="Build a local project context package for review or automation.",
            input_schema=_object_schema(
                {
                    "project_id": {"type": "integer"},
                    "output_dir": {"type": "string"},
                    "include": {"type": "array", "items": {"type": "string"}},
                },
                ["project_id", "output_dir"],
            ),
            output_schema=_model_output("ProjectContextResult"),
            operation_path="pyprocore.workflows.build_project_context_package",
            cli_command="procore-sdk project-context PROJECT_ID OUTPUT_DIR",
            examples=["result = build_project_context_package(project_id, output_dir=output_dir)"],
            calls_live_api=True,
        ),
        _workflow_tool(
            name="procore.build_enhanced_rfi_package",
            title="Build Enhanced RFI Package",
            description="Build a local AI-ready review package for one RFI.",
            input_schema=_object_schema(
                {
                    "project_id": {"type": "integer"},
                    "rfi_id": {"type": "integer"},
                    "rfi_number": {"type": "string"},
                    "output_dir": {"type": "string"},
                },
                ["project_id", "output_dir"],
            ),
            output_schema=_model_output("EnhancedRFIPackageResult"),
            operation_path="pyprocore.workflows.build_enhanced_rfi_package",
            cli_command="procore-sdk enhanced-rfi-package PROJECT_ID OUTPUT_DIR",
            examples=["result = build_enhanced_rfi_package(project_id, rfi_number='15')"],
            calls_live_api=True,
        ),
        _workflow_tool(
            name="procore.build_enhanced_submittal_package",
            title="Build Enhanced Submittal Package",
            description="Build a local AI-ready review package for one submittal.",
            input_schema=_object_schema(
                {
                    "project_id": {"type": "integer"},
                    "submittal_id": {"type": "integer"},
                    "submittal_number": {"type": "string"},
                    "output_dir": {"type": "string"},
                },
                ["project_id", "output_dir"],
            ),
            output_schema=_model_output("EnhancedSubmittalPackageResult"),
            operation_path="pyprocore.workflows.build_enhanced_submittal_package",
            cli_command="procore-sdk enhanced-submittal-package PROJECT_ID OUTPUT_DIR",
            examples=[
                "result = build_enhanced_submittal_package(project_id, submittal_number='27')"
            ],
            calls_live_api=True,
        ),
        _workflow_tool(
            name="procore.build_ai_review_export",
            title="Build AI Review Export",
            description="Create local AI review files from an existing PyProcore package.",
            input_schema=_object_schema(
                {"package_dir": {"type": "string"}, "output_dir": {"type": "string"}},
                ["package_dir"],
            ),
            output_schema=_model_output("AIExportResult"),
            operation_path="pyprocore.workflows.build_ai_review_export",
            cli_command="procore-sdk ai-review-export PACKAGE_DIR",
            examples=["result = build_ai_review_export(package_dir)"],
            calls_live_api=False,
            permissions=[
                AgentToolPermission.READ_LOCAL_FILES,
                AgentToolPermission.WRITE_LOCAL_FILES,
            ],
        ),
        _workflow_tool(
            name="procore.build_ai_prompt_pack",
            title="Build AI Prompt Pack",
            description="Create local prompt-ready files from an existing PyProcore package.",
            input_schema=_object_schema(
                {
                    "package_dir": {"type": "string"},
                    "output_dir": {"type": "string"},
                    "review_type": {"type": "string"},
                },
                ["package_dir"],
            ),
            output_schema=_model_output("AIExportResult"),
            operation_path="pyprocore.workflows.build_ai_prompt_pack",
            cli_command="procore-sdk ai-prompt-pack PACKAGE_DIR",
            examples=["result = build_ai_prompt_pack(package_dir, review_type='general')"],
            calls_live_api=False,
            permissions=[
                AgentToolPermission.READ_LOCAL_FILES,
                AgentToolPermission.WRITE_LOCAL_FILES,
            ],
        ),
        AgentTool(
            name="procore.validate_workflow_plan",
            title="Validate Workflow Plan",
            description="Validate a local workflow plan file without executing it.",
            category=AgentToolCategory.VALIDATION,
            input_schema=_object_schema({"plan_path": {"type": "string"}}, ["plan_path"]),
            output_schema=_model_output("WorkflowPlan"),
            permissions=[
                AgentToolPermission.READ_LOCAL_FILES,
                AgentToolPermission.VALIDATE_LOCAL_FILES,
            ],
            requires_auth=False,
            calls_live_api=False,
            produces_files=False,
            side_effects=[],
            safety_level=AgentToolSafety.READ_ONLY,
            service_path="pyprocore.workflows",
            operation_path="pyprocore.workflows.validate_workflow_plan",
            cli_command="procore-sdk workflow-plan validate PLAN_PATH",
            examples=["plan = validate_workflow_plan(load_workflow_plan(plan_path))"],
        ),
        _resource_tool(
            name="procore.list_change_events",
            title="List Change Events",
            description="List read-only change events for a Procore project.",
            input_schema=_project_company_schema(),
            output_schema=_array_output("ChangeEvent"),
            service_path="pyprocore.services.financials",
            operation_path="pyprocore.services.financials.list_change_events",
            cli_command="procore-sdk change-events --project PROJECT_ID",
            examples=["events = list_change_events(company_id, project_id)"],
        ),
        _resource_tool(
            name="procore.get_change_event",
            title="Get Change Event",
            description="Get one read-only change event for a Procore project.",
            input_schema=_project_item_schema("change_event_id"),
            output_schema=_model_output("ChangeEvent"),
            service_path="pyprocore.services.financials",
            operation_path="pyprocore.services.financials.get_change_event",
            cli_command="procore-sdk change-event --project PROJECT_ID --id CHANGE_EVENT_ID",
            examples=["event = get_change_event(company_id, project_id, change_event_id)"],
        ),
        _resource_tool(
            name="procore.find_change_event",
            title="Find Change Event",
            description="Find one change event by number, title, or name.",
            input_schema=_project_name_number_search_schema(),
            output_schema=_model_output("ChangeEvent"),
            service_path="pyprocore.services.search",
            operation_path="pyprocore.services.search.find_change_event",
            cli_command="procore-sdk find-change-event --project PROJECT_ID --number NUMBER",
            examples=["event = find_change_event(project_id, company_id=company_id, number='15')"],
        ),
        _resource_tool(
            name="procore.list_change_event_statuses",
            title="List Change Event Statuses",
            description="List read-only change event statuses for a project.",
            input_schema=_project_company_schema(),
            output_schema=_array_output("ChangeEventStatus"),
            service_path="pyprocore.services.financials",
            operation_path="pyprocore.services.financials.list_change_event_statuses",
            cli_command="procore-sdk change-event-statuses --project PROJECT_ID",
            examples=["statuses = list_change_event_statuses(company_id, project_id)"],
        ),
        _resource_tool(
            name="procore.list_change_event_types",
            title="List Change Event Types",
            description="List read-only change event types for a project.",
            input_schema=_project_company_schema(),
            output_schema=_array_output("ChangeEventType"),
            service_path="pyprocore.services.financials",
            operation_path="pyprocore.services.financials.list_change_event_types",
            cli_command="procore-sdk change-event-types --project PROJECT_ID",
            examples=["types = list_change_event_types(company_id, project_id)"],
        ),
        _resource_tool(
            name="procore.get_change_event_settings",
            title="Get Change Event Settings",
            description="Get read-only project change event settings.",
            input_schema=_project_company_schema(),
            output_schema=_model_output("ChangeEventSettings"),
            service_path="pyprocore.services.financials",
            operation_path="pyprocore.services.financials.get_change_event_settings",
            cli_command="procore-sdk change-event-settings --project PROJECT_ID",
            examples=["settings = get_change_event_settings(company_id, project_id)"],
        ),
        _resource_tool(
            name="procore.list_prime_change_orders",
            title="List Prime Change Orders",
            description="List read-only prime change orders for a project.",
            input_schema=_project_company_schema(),
            output_schema=_array_output("PrimeChangeOrder"),
            service_path="pyprocore.services.financials",
            operation_path="pyprocore.services.financials.list_prime_change_orders",
            cli_command="procore-sdk prime-change-orders --project PROJECT_ID",
            examples=["pcos = list_prime_change_orders(company_id, project_id)"],
        ),
        _resource_tool(
            name="procore.get_prime_change_order",
            title="Get Prime Change Order",
            description="Get one read-only prime change order.",
            input_schema=_project_item_schema("prime_change_order_id"),
            output_schema=_model_output("PrimeChangeOrder"),
            service_path="pyprocore.services.financials",
            operation_path="pyprocore.services.financials.get_prime_change_order",
            cli_command="procore-sdk prime-change-order --project PROJECT_ID --id ID",
            examples=["pco = get_prime_change_order(company_id, project_id, pco_id)"],
        ),
        _resource_tool(
            name="procore.find_prime_change_order",
            title="Find Prime Change Order",
            description="Find one prime change order by number, title, or name.",
            input_schema=_project_name_number_search_schema(),
            output_schema=_model_output("PrimeChangeOrder"),
            service_path="pyprocore.services.search",
            operation_path="pyprocore.services.search.find_prime_change_order",
            cli_command="procore-sdk find-prime-change-order --project PROJECT_ID --number NUMBER",
            examples=[
                "pco = find_prime_change_order(project_id, company_id=company_id, number='1')"
            ],
        ),
        _resource_tool(
            name="procore.list_commitment_change_orders",
            title="List Commitment Change Orders",
            description="List read-only commitment change orders for a project.",
            input_schema=_project_company_schema(),
            output_schema=_array_output("CommitmentChangeOrder"),
            service_path="pyprocore.services.financials",
            operation_path="pyprocore.services.financials.list_commitment_change_orders",
            cli_command="procore-sdk commitment-change-orders --project PROJECT_ID",
            examples=["ccos = list_commitment_change_orders(company_id, project_id)"],
        ),
        _resource_tool(
            name="procore.list_change_order_packages",
            title="List Change Order Packages",
            description="List read-only change order packages for a project.",
            input_schema=_project_company_schema(),
            output_schema=_array_output("ChangeOrderPackage"),
            service_path="pyprocore.services.financials",
            operation_path="pyprocore.services.financials.list_change_order_packages",
            cli_command="procore-sdk change-order-packages --project PROJECT_ID",
            examples=["packages = list_change_order_packages(company_id, project_id)"],
        ),
        _resource_tool(
            name="procore.list_direct_costs",
            title="List Direct Costs",
            description="List read-only direct costs for a project.",
            input_schema=_project_company_schema(),
            output_schema=_array_output("DirectCost"),
            service_path="pyprocore.services.financials",
            operation_path="pyprocore.services.financials.list_direct_costs",
            cli_command="procore-sdk direct-costs --project PROJECT_ID",
            examples=["costs = list_direct_costs(company_id, project_id)"],
        ),
        _resource_tool(
            name="procore.get_direct_cost",
            title="Get Direct Cost",
            description="Get one read-only direct cost.",
            input_schema=_project_item_schema("direct_cost_id"),
            output_schema=_model_output("DirectCost"),
            service_path="pyprocore.services.financials",
            operation_path="pyprocore.services.financials.get_direct_cost",
            cli_command="procore-sdk direct-cost --project PROJECT_ID --id DIRECT_COST_ID",
            examples=["cost = get_direct_cost(company_id, project_id, direct_cost_id)"],
        ),
        _resource_tool(
            name="procore.find_direct_cost",
            title="Find Direct Cost",
            description="Find one direct cost by number, title, or name.",
            input_schema=_project_name_number_search_schema(),
            output_schema=_model_output("DirectCost"),
            service_path="pyprocore.services.search",
            operation_path="pyprocore.services.search.find_direct_cost",
            cli_command="procore-sdk find-direct-cost --project PROJECT_ID --number NUMBER",
            examples=["cost = find_direct_cost(project_id, company_id=company_id, number='1')"],
        ),
        _resource_tool(
            name="procore.list_budget_views",
            title="List Budget Views",
            description="List read-only project budget views.",
            input_schema=_project_company_schema(),
            output_schema=_array_output("BudgetView"),
            service_path="pyprocore.services.financials",
            operation_path="pyprocore.services.financials.list_budget_views",
            cli_command="procore-sdk budget-views --project PROJECT_ID",
            examples=["views = list_budget_views(company_id, project_id)"],
        ),
        _resource_tool(
            name="procore.list_budget_detail_columns",
            title="List Budget Detail Columns",
            description="List read-only budget detail columns for a budget view.",
            input_schema=_budget_view_schema(),
            output_schema=_array_output("BudgetDetailColumn"),
            service_path="pyprocore.services.financials",
            operation_path="pyprocore.services.financials.list_budget_detail_columns",
            cli_command="procore-sdk budget-detail-columns --project PROJECT --budget-view VIEW",
            examples=["columns = list_budget_detail_columns(company_id, project_id, view_id)"],
        ),
        _resource_tool(
            name="procore.list_budget_details",
            title="List Budget Details",
            description="List read-only budget detail rows for a budget view.",
            input_schema=_budget_view_schema(),
            output_schema=_array_output("BudgetDetailRow"),
            service_path="pyprocore.services.financials",
            operation_path="pyprocore.services.financials.list_budget_details",
            cli_command="procore-sdk budget-details --project PROJECT_ID --budget-view VIEW_ID",
            examples=["rows = list_budget_details(company_id, project_id, view_id)"],
        ),
        _resource_tool(
            name="procore.list_budget_view_summary_rows",
            title="List Budget Summary Rows",
            description="List read-only budget summary rows for a budget view.",
            input_schema=_budget_view_schema(),
            output_schema=_array_output("BudgetSummaryRow"),
            service_path="pyprocore.services.financials",
            operation_path="pyprocore.services.financials.list_budget_view_summary_rows",
            cli_command="procore-sdk budget-summary-rows --project PROJECT --budget-view VIEW",
            examples=["rows = list_budget_view_summary_rows(company_id, project_id, view_id)"],
        ),
        _resource_tool(
            name="procore.list_cost_codes",
            title="List Cost Codes",
            description="List read-only company cost codes.",
            input_schema=_company_schema(),
            output_schema=_array_output("CostCode"),
            service_path="pyprocore.services.financials",
            operation_path="pyprocore.services.financials.list_cost_codes",
            cli_command="procore-sdk cost-codes",
            examples=["codes = list_cost_codes(company_id)"],
        ),
        _resource_tool(
            name="procore.list_wbs_codes",
            title="List WBS Codes",
            description="List read-only project WBS codes.",
            input_schema=_project_company_schema(),
            output_schema=_array_output("WbsCode"),
            service_path="pyprocore.services.financials",
            operation_path="pyprocore.services.financials.list_wbs_codes",
            cli_command="procore-sdk wbs-codes --project PROJECT_ID",
            examples=["codes = list_wbs_codes(company_id, project_id)"],
        ),
        _resource_tool(
            name="procore.list_commitments",
            title="List Commitments",
            description="List read-only project commitments.",
            input_schema=_project_company_schema(),
            output_schema=_array_output("Commitment"),
            service_path="pyprocore.services.financials",
            operation_path="pyprocore.services.financials.list_commitments",
            cli_command="procore-sdk commitments --project PROJECT_ID",
            examples=["commitments = list_commitments(company_id, project_id)"],
        ),
        _resource_tool(
            name="procore.get_commitment",
            title="Get Commitment",
            description="Get one read-only commitment.",
            input_schema=_project_item_schema("commitment_id"),
            output_schema=_model_output("Commitment"),
            service_path="pyprocore.services.financials",
            operation_path="pyprocore.services.financials.get_commitment",
            cli_command="procore-sdk commitment --project PROJECT_ID --id COMMITMENT_ID",
            examples=["commitment = get_commitment(company_id, project_id, commitment_id)"],
        ),
        _resource_tool(
            name="procore.find_commitment",
            title="Find Commitment",
            description="Find one commitment by number, title, or name.",
            input_schema=_project_name_number_search_schema(),
            output_schema=_model_output("Commitment"),
            service_path="pyprocore.services.search",
            operation_path="pyprocore.services.search.find_commitment",
            cli_command="procore-sdk find-commitment --project PROJECT_ID --number NUMBER",
            examples=[
                "commitment = find_commitment(project_id, company_id=company_id, number='1')"
            ],
        ),
    ]
    tools.extend(
        [
            _resource_tool(
                name="procore.list_prime_contracts",
                title="List Prime Contracts",
                description="List read-only prime contracts for a Procore project.",
                input_schema=_project_company_schema(),
                output_schema=_array_output("PrimeContract"),
                service_path="pyprocore.services.contracts",
                operation_path="pyprocore.services.contracts.list_prime_contracts",
                cli_command="procore-sdk prime-contracts --project PROJECT_ID",
                examples=["contracts = list_prime_contracts(company_id, project_id)"],
            ),
            _resource_tool(
                name="procore.get_prime_contract",
                title="Get Prime Contract",
                description="Get one read-only prime contract.",
                input_schema=_project_item_schema("prime_contract_id"),
                output_schema=_model_output("PrimeContract"),
                service_path="pyprocore.services.contracts",
                operation_path="pyprocore.services.contracts.get_prime_contract",
                cli_command="procore-sdk prime-contract --project PROJECT_ID --id ID",
                examples=["contract = get_prime_contract(company_id, project_id, contract_id)"],
            ),
            _resource_tool(
                name="procore.find_prime_contract",
                title="Find Prime Contract",
                description="Find one prime contract by number, title, or name.",
                input_schema=_project_name_number_search_schema(),
                output_schema=_model_output("PrimeContract"),
                service_path="pyprocore.services.search",
                operation_path="pyprocore.services.search.find_prime_contract",
                cli_command="procore-sdk find-prime-contract --project PROJECT_ID --number NUM",
                examples=["contract = find_prime_contract(project_id, number='1')"],
            ),
            _resource_tool(
                name="procore.list_prime_contract_line_items",
                title="List Prime Contract Line Items",
                description="List read-only line items for one prime contract.",
                input_schema=_project_item_schema("prime_contract_id"),
                output_schema=_array_output("PrimeContractLineItem"),
                service_path="pyprocore.services.contracts",
                operation_path="pyprocore.services.contracts.list_prime_contract_line_items",
                cli_command=(
                    "procore-sdk prime-contract-line-items " "--project PROJECT --prime-contract ID"
                ),
                examples=["items = list_prime_contract_line_items(company_id, project_id, id)"],
            ),
            _resource_tool(
                name="procore.get_prime_contract_summary",
                title="Get Prime Contract Summary",
                description="Get read-only summary data for one prime contract.",
                input_schema=_project_item_schema("prime_contract_id"),
                output_schema=_model_output("PrimeContractSummary"),
                service_path="pyprocore.services.contracts",
                operation_path="pyprocore.services.contracts.get_prime_contract_summary",
                cli_command=(
                    "procore-sdk prime-contract-summary --project PROJECT --prime-contract ID"
                ),
                examples=["summary = get_prime_contract_summary(company_id, project_id, id)"],
            ),
            _resource_tool(
                name="procore.list_commitment_contracts",
                title="List Commitment Contracts",
                description="List read-only commitment contracts for a project.",
                input_schema=_project_company_schema(),
                output_schema=_array_output("CommitmentContract"),
                service_path="pyprocore.services.contracts",
                operation_path="pyprocore.services.contracts.list_commitment_contracts",
                cli_command="procore-sdk commitment-contracts --project PROJECT_ID",
                examples=["contracts = list_commitment_contracts(company_id, project_id)"],
            ),
            _resource_tool(
                name="procore.get_commitment_contract",
                title="Get Commitment Contract",
                description="Get one read-only commitment contract.",
                input_schema=_project_item_schema("commitment_contract_id"),
                output_schema=_model_output("CommitmentContract"),
                service_path="pyprocore.services.contracts",
                operation_path="pyprocore.services.contracts.get_commitment_contract",
                cli_command="procore-sdk commitment-contract --project PROJECT_ID --id ID",
                examples=["contract = get_commitment_contract(company_id, project_id, id)"],
            ),
            _resource_tool(
                name="procore.find_commitment_contract",
                title="Find Commitment Contract",
                description="Find one commitment contract by number, title, or name.",
                input_schema=_project_name_number_search_schema(),
                output_schema=_model_output("CommitmentContract"),
                service_path="pyprocore.services.search",
                operation_path="pyprocore.services.search.find_commitment_contract",
                cli_command="procore-sdk find-commitment-contract --project PROJECT --number NUM",
                examples=["contract = find_commitment_contract(project_id, number='1')"],
            ),
            _resource_tool(
                name="procore.list_purchase_order_contracts",
                title="List Purchase Order Contracts",
                description="List read-only purchase order contracts for a project.",
                input_schema=_project_company_schema(),
                output_schema=_array_output("PurchaseOrderContract"),
                service_path="pyprocore.services.contracts",
                operation_path="pyprocore.services.contracts.list_purchase_order_contracts",
                cli_command="procore-sdk purchase-order-contracts --project PROJECT_ID",
                examples=["contracts = list_purchase_order_contracts(company_id, project_id)"],
            ),
            _resource_tool(
                name="procore.list_work_order_contracts",
                title="List Work Order Contracts",
                description="List read-only work order contracts for a project.",
                input_schema=_project_company_schema(),
                output_schema=_array_output("WorkOrderContract"),
                service_path="pyprocore.services.contracts",
                operation_path="pyprocore.services.contracts.list_work_order_contracts",
                cli_command="procore-sdk work-order-contracts --project PROJECT_ID",
                examples=["contracts = list_work_order_contracts(company_id, project_id)"],
            ),
            _resource_tool(
                name="procore.list_owner_invoices",
                title="List Owner Invoices",
                description="List read-only owner invoices/payment applications.",
                input_schema=_project_item_schema("prime_contract_id"),
                output_schema=_array_output("OwnerInvoice"),
                service_path="pyprocore.services.contracts",
                operation_path="pyprocore.services.contracts.list_owner_invoices",
                cli_command="procore-sdk owner-invoices --project PROJECT --prime-contract ID",
                examples=["invoices = list_owner_invoices(company_id, project_id, contract_id)"],
            ),
            _resource_tool(
                name="procore.list_subcontractor_invoices",
                title="List Subcontractor Invoices",
                description="List read-only subcontractor invoices/requisitions.",
                input_schema=_project_company_schema(),
                output_schema=_array_output("SubcontractorInvoice"),
                service_path="pyprocore.services.contracts",
                operation_path="pyprocore.services.contracts.list_subcontractor_invoices",
                cli_command="procore-sdk subcontractor-invoices --project PROJECT_ID",
                examples=["invoices = list_subcontractor_invoices(company_id, project_id)"],
            ),
            _resource_tool(
                name="procore.list_contract_payments",
                title="List Contract Payments",
                description="List read-only contract payments for a project.",
                input_schema=_project_company_schema(),
                output_schema=_array_output("ContractPayment"),
                service_path="pyprocore.services.contracts",
                operation_path="pyprocore.services.contracts.list_contract_payments",
                cli_command="procore-sdk contract-payments --project PROJECT_ID",
                examples=["payments = list_contract_payments(company_id, project_id)"],
            ),
            _resource_tool(
                name="procore.list_billing_periods",
                title="List Billing Periods",
                description="List read-only billing periods for a project.",
                input_schema=_project_company_schema(),
                output_schema=_array_output("BillingPeriod"),
                service_path="pyprocore.services.contracts",
                operation_path="pyprocore.services.contracts.list_billing_periods",
                cli_command="procore-sdk billing-periods --project PROJECT_ID",
                examples=["periods = list_billing_periods(company_id, project_id)"],
            ),
            _resource_tool(
                name="procore.list_cost_types",
                title="List Cost Types",
                description="List read-only company cost types.",
                input_schema=_company_schema(),
                output_schema=_array_output("CostType"),
                service_path="pyprocore.services.contracts",
                operation_path="pyprocore.services.contracts.list_cost_types",
                cli_command="procore-sdk cost-types",
                examples=["cost_types = list_cost_types(company_id)"],
            ),
            _resource_tool(
                name="procore.list_tax_codes",
                title="List Tax Codes",
                description="List read-only company tax codes.",
                input_schema=_company_schema(),
                output_schema=_array_output("TaxCode"),
                service_path="pyprocore.services.contracts",
                operation_path="pyprocore.services.contracts.list_tax_codes",
                cli_command="procore-sdk tax-codes",
                examples=["tax_codes = list_tax_codes(company_id)"],
            ),
        ]
    )
    return sorted(tools, key=lambda tool: tool.name)


def get_agent_registry() -> AgentToolRegistry:
    """Return the static PyProcore agent tool registry."""
    return AgentToolRegistry(registry_version=REGISTRY_VERSION, tools=_build_tools())


def list_agent_tools() -> list[AgentTool]:
    """Return all registered agent tools sorted by stable name."""
    return get_agent_registry().tools


def get_agent_tool(name: str) -> AgentTool:
    """Return one registered agent tool by name.

    Args:
        name: Stable tool name, such as ``procore.find_rfi``.

    Raises:
        AgentToolNotFoundError: If the requested tool is not registered.
    """
    for tool in list_agent_tools():
        if tool.name == name:
            return tool
    raise AgentToolNotFoundError(f"Agent tool is not registered: {name}")


def build_agent_manifest() -> AgentManifest:
    """Build a JSON-serializable manifest for all registered tools."""
    from pyprocore import __version__

    registry = get_agent_registry()
    return AgentManifest(
        package_name="pyprocore",
        package_version=__version__,
        registry_version=registry.registry_version,
        generated_at=datetime.now(timezone.utc),
        tool_count=registry.tool_count,
        tools=registry.tools,
    )


def export_agent_manifest_json(*, pretty: bool = True) -> str:
    """Return the full agent manifest as a JSON string."""
    indent = 2 if pretty else None
    return build_agent_manifest().model_dump_json(indent=indent)


def export_agent_tools_json(*, pretty: bool = True) -> str:
    """Return registered agent tools as a JSON string."""
    indent = 2 if pretty else None
    data = [tool.model_dump(mode="json") for tool in list_agent_tools()]
    return json.dumps(data, indent=indent)
