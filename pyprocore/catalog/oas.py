"""Local OpenAPI/OAS parsing helpers for safe endpoint coverage reports."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pyprocore.catalog.models import (
    CatalogEndpoint,
    CatalogEndpointSafety,
    CatalogParameter,
    CoverageFinding,
    CoverageReport,
    OASCatalog,
)
from pyprocore.core.exceptions import ValidationError

READ_ONLY_METHODS = {"GET", "HEAD", "OPTIONS"}
WRITE_OR_MUTATION_METHODS = {"POST", "PATCH", "PUT", "DELETE"}
SUPPORTED_OAS_METHODS = READ_ONLY_METHODS | WRITE_OR_MUTATION_METHODS | {"TRACE"}
RISKY_TERMS = {
    "upload",
    "submit",
    "approve",
    "reject",
    "close",
    "reopen",
    "payment",
    "delete",
    "create",
    "update",
    "import",
    "send",
}
CONTEXT_SEGMENTS = {"companies", "company", "projects", "project"}
PYPROCORE_SUPPORTED_AREAS = {
    "action_plans",
    "accident_logs",
    "billing_periods",
    "budget_details",
    "budget_views",
    "calendar_items",
    "call_logs",
    "change_events",
    "change_order_packages",
    "commitment_change_orders",
    "commitment_contracts",
    "commitments",
    "companies",
    "contract_payments",
    "coordination_issues",
    "correspondence",
    "correspondences",
    "cost_codes",
    "cost_types",
    "daily_logs",
    "delay_logs",
    "departments",
    "direct_costs",
    "distribution_groups",
    "document_folders",
    "documents",
    "drawing_areas",
    "drawing_revisions",
    "drawings",
    "equipment_logs",
    "forms",
    "incidents",
    "inspections",
    "locations",
    "meetings",
    "observations",
    "owner_invoices",
    "photos",
    "plan_revision_logs",
    "prime_change_orders",
    "prime_contracts",
    "projects",
    "project_tools",
    "punch_items",
    "purchase_order_contracts",
    "rfis",
    "schedule",
    "specification_revisions",
    "specification_sections",
    "specification_sets",
    "specifications",
    "subcontractor_invoices",
    "submittals",
    "tasks",
    "tax_codes",
    "tools",
    "users",
    "vendors",
    "visitor_logs",
    "waste_logs",
    "weather_logs",
    "work_order_contracts",
}


def load_oas_catalog(path: str | Path) -> OASCatalog:
    """Load a local OpenAPI/OAS JSON file into a safe endpoint catalog.

    Args:
        path: Local path to a JSON OpenAPI/OAS document.

    Returns:
        Parsed OAS catalog metadata.

    Raises:
        ValidationError: If the path is remote, missing, not JSON, or invalid.
    """
    source_path = _validate_local_oas_path(path)
    payload = _load_json_object(source_path)
    paths = payload.get("paths")
    if not isinstance(paths, Mapping):
        raise ValidationError("OAS catalog must contain a top-level object named 'paths'.")

    info = payload.get("info", {})
    title = info.get("title") if isinstance(info, Mapping) else None
    version = info.get("version") if isinstance(info, Mapping) else None
    endpoints: list[CatalogEndpoint] = []
    for endpoint_path, path_item in paths.items():
        if not isinstance(endpoint_path, str) or not isinstance(path_item, Mapping):
            continue
        shared_parameters = _parse_parameters(path_item.get("parameters", []))
        for method, operation in path_item.items():
            method_upper = method.upper()
            if method_upper not in SUPPORTED_OAS_METHODS:
                continue
            if not isinstance(operation, Mapping):
                operation = {}
            parameters = [
                *shared_parameters,
                *_parse_parameters(operation.get("parameters", [])),
            ]
            safety, reasons = classify_endpoint_safety(
                method_upper,
                endpoint_path,
                operation_id=_string_or_none(operation.get("operationId")),
                summary=_string_or_none(operation.get("summary")),
                description=_string_or_none(operation.get("description")),
            )
            endpoints.append(
                CatalogEndpoint(
                    method=method_upper,
                    path=endpoint_path,
                    path_area=_derive_path_area(endpoint_path),
                    operation_id=_string_or_none(operation.get("operationId")),
                    summary=_string_or_none(operation.get("summary")),
                    description=_string_or_none(operation.get("description")),
                    tags=_string_list(operation.get("tags", [])),
                    parameters=parameters,
                    safety=safety,
                    safety_reasons=reasons,
                )
            )
    return OASCatalog(
        source_path=str(source_path),
        title=_string_or_none(title),
        version=_string_or_none(version),
        endpoints=endpoints,
    )


def list_endpoints(
    catalog: OASCatalog,
    method: str | None = None,
) -> list[CatalogEndpoint]:
    """Return catalog endpoints, optionally filtered by HTTP method.

    Args:
        catalog: Parsed local OAS catalog.
        method: Optional HTTP method filter.

    Returns:
        Matching catalog endpoints.
    """
    return catalog.list_endpoints(method=method)


def summarize_by_method(catalog: OASCatalog) -> dict[str, int]:
    """Return endpoint counts grouped by HTTP method."""
    return catalog.summarize_by_method()


def summarize_by_path_area(catalog: OASCatalog) -> dict[str, int]:
    """Return endpoint counts grouped by derived resource area."""
    return catalog.summarize_by_path_area()


def classify_endpoint_safety(
    method: str,
    path: str,
    *,
    operation_id: str | None = None,
    summary: str | None = None,
    description: str | None = None,
) -> tuple[CatalogEndpointSafety, list[str]]:
    """Classify endpoint safety using method and risk-oriented naming.

    Risky path or operation terms override method-based read-only classification.

    Args:
        method: HTTP method.
        path: Endpoint path.
        operation_id: Optional OAS operation identifier.
        summary: Optional OAS summary.
        description: Optional OAS description.

    Returns:
        Tuple of safety classification and explanatory reasons.
    """
    normalized_method = method.upper()
    combined_text = " ".join(
        value.lower()
        for value in [normalized_method, path, operation_id, summary, description]
        if value
    )
    matched_terms = sorted(term for term in RISKY_TERMS if term in combined_text)
    if matched_terms:
        return (
            CatalogEndpointSafety.WRITE_OR_MUTATION,
            [
                "Endpoint name or metadata contains risky write-oriented terms: "
                + ", ".join(matched_terms)
            ],
        )
    if normalized_method in READ_ONLY_METHODS:
        return (
            CatalogEndpointSafety.READ_ONLY,
            [f"{normalized_method} is normally read-only in OpenAPI metadata."],
        )
    if normalized_method in WRITE_OR_MUTATION_METHODS:
        return (
            CatalogEndpointSafety.WRITE_OR_MUTATION,
            [f"{normalized_method} can mutate Procore data and is treated as risky."],
        )
    return (
        CatalogEndpointSafety.UNKNOWN,
        [f"{normalized_method} is not classified as read-only or write/mutation."],
    )


def compare_catalog_to_pyprocore_supported_coverage(
    catalog: OASCatalog,
) -> CoverageReport:
    """Compare a local OAS catalog to known PyProcore read coverage areas.

    Args:
        catalog: Parsed local OAS catalog.

    Returns:
        Coverage and safety report. This report is metadata-only and does not
        generate executable clients, tools, or Procore API requests.
    """
    endpoints_by_area: dict[str, list[CatalogEndpoint]] = {}
    for endpoint in catalog.endpoints:
        endpoints_by_area.setdefault(endpoint.path_area, []).append(endpoint)

    findings: list[CoverageFinding] = []
    for area, endpoints in sorted(endpoints_by_area.items()):
        supported = area in PYPROCORE_SUPPORTED_AREAS
        read_only_count = sum(
            endpoint.safety == CatalogEndpointSafety.READ_ONLY for endpoint in endpoints
        )
        risky_count = sum(
            endpoint.safety == CatalogEndpointSafety.WRITE_OR_MUTATION for endpoint in endpoints
        )
        unknown_count = sum(
            endpoint.safety == CatalogEndpointSafety.UNKNOWN for endpoint in endpoints
        )
        notes = [
            (
                "PyProcore has existing read coverage metadata for this area."
                if supported
                else "Area is not yet represented in PyProcore supported coverage metadata."
            )
        ]
        findings.append(
            CoverageFinding(
                area=area,
                supported=supported,
                endpoint_count=len(endpoints),
                read_only_count=read_only_count,
                risky_count=risky_count,
                unknown_count=unknown_count,
                notes=notes,
            )
        )

    return CoverageReport(
        source_path=catalog.source_path,
        summary=catalog.summary(),
        already_supported_areas=sorted(
            area for area in endpoints_by_area if area in PYPROCORE_SUPPORTED_AREAS
        ),
        unsupported_areas=sorted(
            area for area in endpoints_by_area if area not in PYPROCORE_SUPPORTED_AREAS
        ),
        read_only_candidates=[
            endpoint
            for endpoint in catalog.endpoints
            if endpoint.safety == CatalogEndpointSafety.READ_ONLY
        ],
        risky_write_candidates=[
            endpoint
            for endpoint in catalog.endpoints
            if endpoint.safety == CatalogEndpointSafety.WRITE_OR_MUTATION
        ],
        unknown_candidates=[
            endpoint
            for endpoint in catalog.endpoints
            if endpoint.safety == CatalogEndpointSafety.UNKNOWN
        ],
        findings=findings,
    )


def _validate_local_oas_path(path: str | Path) -> Path:
    """Validate that a catalog path is a local JSON file."""
    raw_path = str(path)
    if "://" in raw_path:
        raise ValidationError("OAS catalog path must be a local JSON file, not a URL.")
    source_path = Path(path).expanduser()
    if source_path.suffix.lower() != ".json":
        raise ValidationError("OAS catalog path must point to a .json file.")
    if not source_path.exists():
        raise ValidationError(f"OAS catalog file does not exist: {source_path}")
    if not source_path.is_file():
        raise ValidationError(f"OAS catalog path is not a file: {source_path}")
    return source_path


def _load_json_object(path: Path) -> dict[str, Any]:
    """Load a JSON object from a local file."""
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"OAS catalog is not valid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise ValidationError("OAS catalog JSON must be an object.")
    return payload


def _parse_parameters(raw_parameters: object) -> list[CatalogParameter]:
    """Parse OAS parameter metadata."""
    if not isinstance(raw_parameters, list):
        return []
    parameters: list[CatalogParameter] = []
    for item in raw_parameters:
        if not isinstance(item, Mapping):
            continue
        schema = item.get("schema", {})
        schema_type = schema.get("type") if isinstance(schema, Mapping) else None
        name = item.get("name")
        if not isinstance(name, str):
            continue
        parameters.append(
            CatalogParameter(
                name=name,
                location=_string_or_none(item.get("in")),
                required=bool(item.get("required", False)),
                schema_type=_string_or_none(schema_type),
                description=_string_or_none(item.get("description")),
            )
        )
    return parameters


def _derive_path_area(path: str) -> str:
    """Derive a stable resource area from a Procore-style API path."""
    segments = [
        segment
        for segment in path.strip("/").split("/")
        if segment and not segment.startswith("{") and not segment.endswith("}")
    ]
    normalized: list[str] = []
    for segment in segments:
        if segment == "rest" or segment.startswith("v"):
            continue
        normalized.append(segment)
    if not normalized:
        return "unknown"
    if len(normalized) == 1:
        return normalized[0]
    for segment in normalized:
        if segment not in CONTEXT_SEGMENTS:
            return segment
    return normalized[-1]


def _string_or_none(value: object) -> str | None:
    """Return a string value or None."""
    return value if isinstance(value, str) else None


def _string_list(value: object) -> list[str]:
    """Return a list containing only string values."""
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]
