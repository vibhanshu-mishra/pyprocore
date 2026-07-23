"""Built-in metadata-only discovery capability registry."""

from __future__ import annotations

from typing import Any

from pyprocore.discovery.models import DiscoveryBundle, DiscoveryCapability, DiscoveryReport

DEFAULT_SAFETY_LABELS = [
    "metadata_only",
    "execution_disabled",
    "read_or_export_or_validation_only",
    "write_disabled",
    "mcp_execution_disabled",
    "external_ai_not_required",
]


def list_discovery_capabilities() -> list[DiscoveryCapability]:
    """Return built-in safe PyProcore capability metadata.

    Returns:
        Metadata-only capability entries. This function does not call Procore,
        load remote registries, or invoke SDK service functions.
    """
    return [_capability(**entry) for entry in _BUILTIN_CAPABILITIES]


def get_discovery_capability(name: str) -> DiscoveryCapability:
    """Return one built-in capability by name.

    Args:
        name: Capability identifier.

    Returns:
        Matching capability metadata.

    Raises:
        KeyError: If the capability is not present.
    """
    normalized = name.strip().lower()
    for capability in list_discovery_capabilities():
        if capability.name.lower() == normalized:
            return capability
    raise KeyError(f"Unknown discovery capability: {name}")


def build_discovery_bundle() -> DiscoveryBundle:
    """Build a metadata-only discovery capability inventory."""
    return DiscoveryBundle(capabilities=list_discovery_capabilities())


def build_discovery_report() -> DiscoveryReport:
    """Build a metadata-only discovery safety and inventory report."""
    capabilities = list_discovery_capabilities()
    return DiscoveryReport(
        capability_count=len(capabilities),
        resource_families=sorted({capability.resource_family for capability in capabilities}),
        capability_names=[capability.name for capability in capabilities],
        safety_boundaries=[
            "Discovery is local metadata only.",
            "Discovery does not call Procore.",
            "Discovery does not execute SDK tools or service functions.",
            "Discovery does not enable MCP execution.",
            "Discovery does not call external AI/model APIs.",
            "Discovery does not enable create, update, delete, upload, approval, "
            "submit, payment, or send actions.",
            "Discovery does not fetch remote OAS files or remote plugin registries.",
        ],
    )


def _capability(
    *,
    name: str,
    title: str,
    description: str,
    resource_family: str,
    operations: list[str],
    keywords: list[str],
    examples: list[str],
    safety_labels: list[str] | None = None,
) -> DiscoveryCapability:
    """Create one built-in capability with standard safety labels."""
    labels = [*DEFAULT_SAFETY_LABELS]
    if safety_labels:
        labels.extend(label for label in safety_labels if label not in labels)
    return DiscoveryCapability(
        name=name,
        title=title,
        description=description,
        resource_family=resource_family,
        operations=operations,
        keywords=keywords,
        examples=examples,
        safety_labels=labels,
    )


_BUILTIN_CAPABILITIES: list[dict[str, Any]] = [
    {
        "name": "companies",
        "title": "Companies",
        "description": "Discover company listing helpers and company lookup metadata.",
        "resource_family": "companies",
        "operations": ["list_companies", "find_company"],
        "keywords": ["company", "companies", "tenant", "account", "organization"],
        "examples": ["find company by name", "list companies available to a token"],
    },
    {
        "name": "projects",
        "title": "Projects",
        "description": "Discover project list, get, and human-friendly resolver helpers.",
        "resource_family": "projects",
        "operations": ["list_projects", "get_project", "find_project", "find_project_contains"],
        "keywords": ["project", "projects", "job", "jobsite", "number", "sandbox"],
        "examples": ["find project by name", "list projects for a company"],
    },
    {
        "name": "rfis",
        "title": "RFIs",
        "description": "Discover RFI read helpers, attachment downloads, exports, and packages.",
        "resource_family": "rfis",
        "operations": ["list_rfis", "get_rfi", "find_rfi", "download_rfi_attachments"],
        "keywords": ["rfi", "rfis", "question", "overdue", "ball in court", "attachment"],
        "examples": ["overdue rfis", "download rfi attachments", "build rfi package"],
    },
    {
        "name": "submittals",
        "title": "Submittals",
        "description": (
            "Discover submittal read helpers, attachment downloads, exports, " "and packages."
        ),
        "resource_family": "submittals",
        "operations": [
            "list_submittals",
            "get_submittal",
            "find_submittal",
            "download_submittal_attachments",
        ],
        "keywords": ["submittal", "submittals", "package", "approval", "attachment"],
        "examples": ["submittal package", "download submittal attachments"],
    },
    {
        "name": "documents",
        "title": "Documents",
        "description": "Discover document folder, document metadata, and safe download helpers.",
        "resource_family": "documents",
        "operations": [
            "list_document_folders",
            "list_documents",
            "get_document",
            "download_document",
        ],
        "keywords": ["document", "documents", "folder", "file", "download"],
        "examples": ["list documents", "download document metadata attachment"],
    },
    {
        "name": "drawings",
        "title": "Drawings",
        "description": (
            "Discover drawing areas, drawing lists, drawing lookup, and safe drawing " "downloads."
        ),
        "resource_family": "drawings",
        "operations": [
            "list_drawing_areas",
            "list_drawings",
            "get_drawing",
            "download_drawing",
        ],
        "keywords": ["drawing", "drawings", "drawing area", "revision", "sheet", "download"],
        "examples": ["download drawings", "list drawing areas"],
    },
    {
        "name": "specifications",
        "title": "Specifications",
        "description": "Discover specification set, section, revision, and safe download helpers.",
        "resource_family": "specifications",
        "operations": [
            "list_specification_sets",
            "list_specification_sections",
            "list_specification_revisions",
            "download_specification_section_revision",
        ],
        "keywords": ["specification", "specifications", "spec", "section", "revision"],
        "examples": ["download specification revision", "find specification section"],
    },
    {
        "name": "photos",
        "title": "Photos",
        "description": "Discover photo albums, photos, and safe photo download helpers.",
        "resource_family": "photos",
        "operations": ["list_photo_albums", "list_photos", "get_photo", "download_photo"],
        "keywords": ["photo", "photos", "album", "image", "download"],
        "examples": ["list photo albums", "download photo album"],
    },
    {
        "name": "daily_logs",
        "title": "Daily Logs",
        "description": "Discover daily log headers, counts, and read-only daily log type helpers.",
        "resource_family": "daily_logs",
        "operations": [
            "list_daily_log_headers",
            "list_daily_logs",
            "list_call_logs",
            "list_visitor_logs",
            "list_delay_logs",
            "list_weather_logs",
        ],
        "keywords": ["daily log", "daily logs", "call log", "visitor log", "delay log", "weather"],
        "examples": ["export daily logs", "list weather logs"],
    },
    {
        "name": "observations",
        "title": "Observations",
        "description": "Discover observation list, get, find, and export metadata.",
        "resource_family": "observations",
        "operations": ["list_observations", "get_observation", "find_observation"],
        "keywords": ["observation", "observations", "safety", "quality", "issue"],
        "examples": ["find observation", "export observations"],
    },
    {
        "name": "punch_items",
        "title": "Punch Items",
        "description": "Discover punch item list, get, find, and export metadata.",
        "resource_family": "punch_items",
        "operations": ["list_punch_items", "get_punch_item", "find_punch_item"],
        "keywords": ["punch", "punch item", "punch list", "deficiency"],
        "examples": ["export punch items", "find punch item"],
    },
    {
        "name": "correspondence",
        "title": "Correspondence And Generic Tools",
        "description": "Discover correspondence and generic tool read metadata.",
        "resource_family": "correspondence",
        "operations": ["list_correspondences", "get_correspondence", "list_generic_tools"],
        "keywords": ["correspondence", "generic tool", "custom tool", "records"],
        "examples": ["list correspondence", "find generic tool record"],
    },
    {
        "name": "meetings",
        "title": "Meetings",
        "description": "Discover meeting list, get, find, and export metadata.",
        "resource_family": "meetings",
        "operations": ["list_meetings", "get_meeting", "find_meeting"],
        "keywords": ["meeting", "meetings", "minutes", "agenda"],
        "examples": ["export meetings", "find meeting"],
    },
    {
        "name": "inspections",
        "title": "Inspections",
        "description": "Discover inspection list, get, find, and export metadata.",
        "resource_family": "inspections",
        "operations": ["list_inspections", "get_inspection", "find_inspection"],
        "keywords": ["inspection", "inspections", "checklist", "quality"],
        "examples": ["export inspections", "find inspection"],
    },
    {
        "name": "incidents",
        "title": "Incidents",
        "description": "Discover incident list, get, configuration, find, and export metadata.",
        "resource_family": "incidents",
        "operations": ["list_incidents", "get_incident", "get_incident_configuration"],
        "keywords": ["incident", "incidents", "safety", "accident"],
        "examples": ["export incidents", "incident configuration"],
    },
    {
        "name": "directory",
        "title": "Directory",
        "description": (
            "Discover users, vendors, departments, distribution groups, and locations " "metadata."
        ),
        "resource_family": "directory",
        "operations": [
            "list_company_users",
            "list_project_users",
            "list_vendors",
            "list_departments",
            "list_distribution_groups",
            "list_locations",
        ],
        "keywords": [
            "directory",
            "user",
            "users",
            "vendor",
            "vendors",
            "department",
            "distribution group",
            "location",
        ],
        "examples": ["list project users", "export vendors"],
    },
    {
        "name": "financial_read_helpers",
        "title": "Financial Read Helpers",
        "description": "Discover read-only budget, change event, cost, and invoice metadata.",
        "resource_family": "financials",
        "operations": [
            "list_change_events",
            "list_direct_costs",
            "list_budget_views",
            "list_owner_invoices",
        ],
        "keywords": ["financial", "budget", "cost", "change event", "invoice", "payment"],
        "examples": ["list change events", "export budget details"],
    },
    {
        "name": "contract_read_helpers",
        "title": "Contract Read Helpers",
        "description": (
            "Discover read-only commitment, prime contract, and purchase order " "metadata."
        ),
        "resource_family": "contracts",
        "operations": [
            "list_commitments",
            "list_prime_contracts",
            "list_commitment_contracts",
            "list_purchase_order_contracts",
        ],
        "keywords": ["contract", "contracts", "commitment", "prime contract", "purchase order"],
        "examples": ["list commitments", "find prime contract"],
    },
    {
        "name": "project_management_read_helpers",
        "title": "Project Management Read Helpers",
        "description": "Discover schedule, tasks, calendar items, forms, and action plan metadata.",
        "resource_family": "project_management",
        "operations": [
            "list_tasks",
            "list_calendar_items",
            "list_forms",
            "list_action_plans",
            "get_project_schedule",
        ],
        "keywords": ["task", "schedule", "calendar", "form", "action plan", "coordination issue"],
        "examples": ["list tasks", "export calendar items"],
    },
    {
        "name": "project_tools",
        "title": "Project Tools",
        "description": "Discover Phase 16A read-only project tool metadata.",
        "resource_family": "project_tools",
        "operations": ["list_project_tools", "get_project_tool", "list_generic_tools"],
        "keywords": [
            "project tool",
            "project tools",
            "tools",
            "active tools",
            "configurable tools",
        ],
        "examples": ["list project tools", "show project tool metadata"],
    },
    {
        "name": "async_read_helpers",
        "title": "Async Read Helpers",
        "description": "Discover async client groups for read and export workflows.",
        "resource_family": "async",
        "operations": ["AsyncProcore", "async batch read helpers", "async export helpers"],
        "keywords": ["async", "batch", "concurrent", "export", "read"],
        "examples": ["async read batch", "async export project data"],
    },
    {
        "name": "scheduled_export_dry_runs",
        "title": "Scheduled Export Dry-runs",
        "description": (
            "Discover local scheduled export examples and dry-run workflow plan " "metadata."
        ),
        "resource_family": "automation",
        "operations": [
            "workflow-plan validate",
            "workflow-plan run --dry-run",
            "scheduled-export",
        ],
        "keywords": ["scheduled", "automation", "cron", "workflow plan", "dry run", "export"],
        "examples": ["scheduled export dry run", "validate workflow plan"],
    },
    {
        "name": "ai_workflow_packages",
        "title": "AI Workflow Packages",
        "description": (
            "Discover local AI-ready package builders that create files for review " "workflows."
        ),
        "resource_family": "workflows",
        "operations": [
            "project_context",
            "enhanced_rfi_package",
            "enhanced_submittal_package",
            "ai_review_export",
            "ai_prompt_pack",
        ],
        "keywords": ["ai", "review", "package", "project context", "prompt", "export"],
        "examples": ["build project context package", "ai review export"],
        "safety_labels": ["local_file_output", "external_ai_not_called"],
    },
    {
        "name": "plugin_metadata_trust",
        "title": "Plugin Metadata And Trust Validation",
        "description": "Discover local plugin metadata, scaffolding, and trust validation helpers.",
        "resource_family": "plugins",
        "operations": ["plugins list", "plugins trust validate-manifest", "plugins trust report"],
        "keywords": ["plugin", "plugins", "trust", "manifest", "policy", "metadata"],
        "examples": ["validate plugin trust manifest", "plugin trust report"],
        "safety_labels": ["plugin_execution_disabled", "remote_install_disabled"],
    },
    {
        "name": "golden_evals",
        "title": "Golden Evals",
        "description": "Discover local evaluation datasets, baselines, and report helpers.",
        "resource_family": "evals",
        "operations": ["evals run", "evals baseline", "agent evals run"],
        "keywords": ["eval", "evals", "golden", "baseline", "regression", "score"],
        "examples": ["run golden evals", "compare eval baseline"],
    },
    {
        "name": "mcp_discovery_metadata",
        "title": "MCP Discovery Metadata",
        "description": (
            "Discover MCP resource, prompt, capability, and safety metadata with "
            "execution disabled."
        ),
        "resource_family": "mcp",
        "operations": ["mcp manifest", "mcp resources", "mcp safety", "mcp compatibility"],
        "keywords": ["mcp", "discovery", "resource", "prompt", "capability", "metadata"],
        "examples": ["mcp discovery metadata", "mcp safety report"],
        "safety_labels": ["mcp_discovery_only", "mcp_execution_disabled"],
    },
    {
        "name": "oas_catalog_reports",
        "title": "OAS Catalog Reports",
        "description": (
            "Discover Phase 17A local OAS catalog summaries, endpoint lists, and " "safety reports."
        ),
        "resource_family": "catalog",
        "operations": [
            "catalog summarize",
            "catalog endpoints",
            "catalog coverage-report",
            "catalog safety-report",
        ],
        "keywords": ["oas", "openapi", "catalog", "endpoint", "coverage", "safety", "read only"],
        "examples": ["catalog safety report", "catalog coverage report"],
        "safety_labels": ["local_oas_only", "remote_oas_fetch_disabled"],
    },
]
