"""Local OpenAPI/OAS drift detection helpers."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from pyprocore.catalog import CatalogEndpoint, CatalogEndpointSafety, load_oas_catalog
from pyprocore.maintenance.models import (
    ApiDriftReport,
    ApiEndpointChange,
    ApiMaintenanceFinding,
)


def compare_oas_catalogs(old_oas_path: str | Path, new_oas_path: str | Path) -> ApiDriftReport:
    """Compare two local OAS JSON files without network or Procore access.

    Args:
        old_oas_path: Local path to the earlier OAS JSON file.
        new_oas_path: Local path to the newer OAS JSON file.

    Returns:
        A metadata-only drift report requiring human review.
    """
    old_catalog = load_oas_catalog(old_oas_path)
    new_catalog = load_oas_catalog(new_oas_path)
    added = detect_added_endpoints(old_catalog.endpoints, new_catalog.endpoints)
    removed = detect_removed_endpoints(old_catalog.endpoints, new_catalog.endpoints)
    methods = detect_changed_methods(old_catalog.endpoints, new_catalog.endpoints)
    parameters = detect_changed_parameters(old_catalog.endpoints, new_catalog.endpoints)
    operation_ids = detect_changed_operation_ids(old_catalog.endpoints, new_catalog.endpoints)
    risky = detect_risky_changes([*added, *removed, *methods, *parameters, *operation_ids])
    return ApiDriftReport(
        old_source_path=str(old_oas_path),
        new_source_path=str(new_oas_path),
        added_endpoints=added,
        removed_endpoints=removed,
        changed_methods=methods,
        changed_parameters=parameters,
        changed_operation_ids=operation_ids,
        risky_changes=risky,
        findings=[
            ApiMaintenanceFinding(
                severity="info",
                code="human_review_required",
                message=(
                    "This local drift report does not update the SDK, fetch remote specs, "
                    "call Procore, generate executable tools, commit changes, or open pull "
                    "requests."
                ),
            )
        ],
    )


def detect_added_endpoints(
    old_endpoints: list[CatalogEndpoint],
    new_endpoints: list[CatalogEndpoint],
) -> list[ApiEndpointChange]:
    """Return endpoint operations present only in the newer catalog."""
    old_keys = {_endpoint_key(endpoint) for endpoint in old_endpoints}
    return [
        _endpoint_change("added_endpoint", endpoint)
        for endpoint in new_endpoints
        if _endpoint_key(endpoint) not in old_keys
    ]


def detect_removed_endpoints(
    old_endpoints: list[CatalogEndpoint],
    new_endpoints: list[CatalogEndpoint],
) -> list[ApiEndpointChange]:
    """Return endpoint operations present only in the older catalog."""
    new_keys = {_endpoint_key(endpoint) for endpoint in new_endpoints}
    return [
        _endpoint_change("removed_endpoint", endpoint)
        for endpoint in old_endpoints
        if _endpoint_key(endpoint) not in new_keys
    ]


def detect_changed_methods(
    old_endpoints: list[CatalogEndpoint],
    new_endpoints: list[CatalogEndpoint],
) -> list[ApiEndpointChange]:
    """Detect paths whose declared HTTP method set changed."""
    old_by_path = _methods_by_path(old_endpoints)
    new_by_path = _methods_by_path(new_endpoints)
    changes: list[ApiEndpointChange] = []
    for path in sorted(old_by_path.keys() & new_by_path.keys()):
        old_methods = old_by_path[path]
        new_methods = new_by_path[path]
        if old_methods == new_methods:
            continue
        safety = (
            CatalogEndpointSafety.WRITE_OR_MUTATION
            if any(method not in {"GET", "HEAD", "OPTIONS"} for method in new_methods)
            else CatalogEndpointSafety.READ_ONLY
        )
        changes.append(
            ApiEndpointChange(
                change_type="changed_methods",
                path=path,
                safety=safety,
                risky=safety == CatalogEndpointSafety.WRITE_OR_MUTATION,
                details=[
                    f"Methods before: {', '.join(sorted(old_methods)) or 'none'}",
                    f"Methods after: {', '.join(sorted(new_methods)) or 'none'}",
                ],
            )
        )
    return changes


def detect_changed_parameters(
    old_endpoints: list[CatalogEndpoint],
    new_endpoints: list[CatalogEndpoint],
) -> list[ApiEndpointChange]:
    """Detect parameter metadata changes for matching path-method operations."""
    old_map = {_endpoint_key(endpoint): endpoint for endpoint in old_endpoints}
    new_map = {_endpoint_key(endpoint): endpoint for endpoint in new_endpoints}
    changes: list[ApiEndpointChange] = []
    for key in sorted(old_map.keys() & new_map.keys()):
        old_endpoint = old_map[key]
        new_endpoint = new_map[key]
        if _parameter_signature(old_endpoint) == _parameter_signature(new_endpoint):
            continue
        changes.append(
            ApiEndpointChange(
                change_type="changed_parameters",
                path=new_endpoint.path,
                method=new_endpoint.method,
                parameters_before=old_endpoint.parameters,
                parameters_after=new_endpoint.parameters,
                safety=new_endpoint.safety,
                risky=new_endpoint.safety == CatalogEndpointSafety.WRITE_OR_MUTATION,
                details=["Parameter names, locations, requirements, or schema types changed."],
            )
        )
    return changes


def detect_changed_operation_ids(
    old_endpoints: list[CatalogEndpoint],
    new_endpoints: list[CatalogEndpoint],
) -> list[ApiEndpointChange]:
    """Detect operationId changes for matching path-method operations."""
    old_map = {_endpoint_key(endpoint): endpoint for endpoint in old_endpoints}
    new_map = {_endpoint_key(endpoint): endpoint for endpoint in new_endpoints}
    changes: list[ApiEndpointChange] = []
    for key in sorted(old_map.keys() & new_map.keys()):
        old_endpoint = old_map[key]
        new_endpoint = new_map[key]
        if old_endpoint.operation_id == new_endpoint.operation_id:
            continue
        changes.append(
            ApiEndpointChange(
                change_type="changed_operation_id",
                path=new_endpoint.path,
                method=new_endpoint.method,
                operation_id_before=old_endpoint.operation_id,
                operation_id_after=new_endpoint.operation_id,
                safety=new_endpoint.safety,
                risky=new_endpoint.safety == CatalogEndpointSafety.WRITE_OR_MUTATION,
                details=["The OAS operationId changed; review generated names and documentation."],
            )
        )
    return changes


def detect_risky_changes(changes: list[ApiEndpointChange]) -> list[ApiEndpointChange]:
    """Return changes classified as write/mutation risk."""
    return [
        change
        for change in changes
        if change.risky or change.safety == CatalogEndpointSafety.WRITE_OR_MUTATION
    ]


def _endpoint_key(endpoint: CatalogEndpoint) -> tuple[str, str]:
    """Return a stable endpoint operation key."""
    return endpoint.path, endpoint.method


def _endpoint_change(change_type: str, endpoint: CatalogEndpoint) -> ApiEndpointChange:
    """Build a change row from endpoint metadata."""
    risky = endpoint.safety == CatalogEndpointSafety.WRITE_OR_MUTATION
    return ApiEndpointChange(
        change_type=change_type,
        path=endpoint.path,
        method=endpoint.method,
        operation_id_after=endpoint.operation_id if change_type == "added_endpoint" else None,
        operation_id_before=endpoint.operation_id if change_type == "removed_endpoint" else None,
        parameters_after=endpoint.parameters if change_type == "added_endpoint" else [],
        parameters_before=endpoint.parameters if change_type == "removed_endpoint" else [],
        safety=endpoint.safety,
        risky=risky,
        details=list(endpoint.safety_reasons),
    )


def _methods_by_path(endpoints: list[CatalogEndpoint]) -> dict[str, set[str]]:
    """Group HTTP methods by endpoint path."""
    grouped: dict[str, set[str]] = defaultdict(set)
    for endpoint in endpoints:
        grouped[endpoint.path].add(endpoint.method)
    return dict(grouped)


def _parameter_signature(endpoint: CatalogEndpoint) -> tuple[tuple[object, ...], ...]:
    """Return a stable signature for endpoint parameter metadata."""
    return tuple(
        sorted(
            (
                (
                    parameter.name,
                    parameter.location,
                    parameter.required,
                    parameter.schema_type,
                )
                for parameter in endpoint.parameters
            ),
            key=lambda item: tuple("" if value is None else str(value) for value in item),
        )
    )
