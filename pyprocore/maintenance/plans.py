"""Maintenance-plan generation from local OAS coverage metadata."""

from __future__ import annotations

import re
from pathlib import Path

from pyprocore.catalog import CatalogEndpoint, CatalogEndpointSafety, load_oas_catalog
from pyprocore.maintenance.coverage import analyze_pyprocore_coverage_gaps
from pyprocore.maintenance.models import (
    ApiMaintenanceFinding,
    ApiMaintenancePlan,
    ApiMaintenanceTask,
)


def build_api_maintenance_plan(oas_path: str | Path) -> ApiMaintenancePlan:
    """Build a human-review implementation plan from a local OAS file.

    Args:
        oas_path: Local OAS JSON file path.

    Returns:
        Metadata-only maintenance plan. The plan does not modify the SDK.
    """
    catalog = load_oas_catalog(oas_path)
    gaps = analyze_pyprocore_coverage_gaps(oas_path)
    unsupported_keys = {
        (gap.endpoint.path, gap.endpoint.method)
        for gap in [
            *gaps.unsupported_read_only,
            *gaps.unsupported_risky_write,
            *gaps.unknown,
        ]
    }
    safe: list[ApiMaintenanceTask] = []
    review: list[ApiMaintenanceTask] = []
    risky: list[ApiMaintenanceTask] = []
    docs: list[ApiMaintenanceTask] = []
    tests: list[ApiMaintenanceTask] = []
    for endpoint in catalog.endpoints:
        task = _task_from_endpoint(endpoint)
        if (endpoint.path, endpoint.method) not in unsupported_keys:
            docs.append(task.model_copy(update={"category": "docs_only_update"}))
            continue
        if endpoint.safety == CatalogEndpointSafety.READ_ONLY:
            safe.append(task.model_copy(update={"category": "safe_read_only_candidate"}))
            tests.append(task.model_copy(update={"category": "tests_examples_needed"}))
        elif endpoint.safety == CatalogEndpointSafety.WRITE_OR_MUTATION:
            risky.append(
                task.model_copy(
                    update={
                        "category": "risky_write_deferred",
                        "warning": (
                            "Write/mutation endpoint. Do not implement through this assistant."
                        ),
                    }
                )
            )
        else:
            review.append(task.model_copy(update={"category": "needs_endpoint_shape_review"}))
    return ApiMaintenancePlan(
        source_path=str(oas_path),
        safe_read_only_candidates=safe,
        needs_endpoint_shape_review=review,
        risky_write_deferred=risky,
        docs_only_updates=docs,
        tests_examples_needed=tests,
        findings=[
            ApiMaintenanceFinding(
                severity="info",
                code="human_review_required",
                message=(
                    "This plan is advisory. It does not generate production endpoint code, "
                    "update files, commit changes, open pull requests, or publish packages."
                ),
            )
        ],
    )


def _task_from_endpoint(endpoint: CatalogEndpoint) -> ApiMaintenanceTask:
    """Build one suggested maintenance task from endpoint metadata."""
    module_name = _python_identifier(endpoint.path_area)
    model_name = "".join(part.title() for part in module_name.split("_")) or "Resource"
    cli_name = module_name.replace("_", "-")
    return ApiMaintenanceTask(
        category="unclassified",
        resource_family=endpoint.path_area,
        endpoint_path=endpoint.path,
        method=endpoint.method,
        safety_classification=endpoint.safety,
        suggested_service_module=f"pyprocore/services/{module_name}.py",
        suggested_model_name=model_name,
        suggested_cli_command=f"procore-sdk {cli_name}",
        suggested_tests=[
            f"Mock {endpoint.method} {endpoint.path} success and API errors.",
            "Assert no live Procore access is required.",
        ],
        suggested_examples=[
            f"Add a local/mock {module_name} read example after maintainer review."
        ],
        implementation_notes=[
            "Confirm the official endpoint shape, context IDs, pagination, and permissions.",
            "Use existing typed service and client patterns.",
            "Keep implementation read-only and add docs/API coverage metadata.",
        ],
    )


def _python_identifier(value: str) -> str:
    """Normalize a resource family to a conservative Python identifier."""
    normalized = re.sub(r"[^a-zA-Z0-9_]+", "_", value).strip("_").lower()
    if not normalized or normalized[0].isdigit():
        return f"resource_{normalized}" if normalized else "resource"
    return normalized
