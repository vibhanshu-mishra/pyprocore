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
    ]
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
