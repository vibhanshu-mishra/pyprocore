"""Coverage-gap analysis for local OAS catalogs."""

from __future__ import annotations

from pathlib import Path

from pyprocore.catalog import (
    CatalogEndpointSafety,
    compare_catalog_to_pyprocore_supported_coverage,
    load_oas_catalog,
)
from pyprocore.maintenance.models import (
    ApiCoverageGap,
    ApiCoverageGapReport,
    ApiMaintenanceFinding,
)


def analyze_pyprocore_coverage_gaps(oas_path: str | Path) -> ApiCoverageGapReport:
    """Analyze a local OAS file against PyProcore's supported read areas.

    Args:
        oas_path: Local OAS JSON file path.

    Returns:
        Metadata-only coverage-gap report.
    """
    catalog = load_oas_catalog(oas_path)
    coverage = compare_catalog_to_pyprocore_supported_coverage(catalog)
    supported_areas = set(coverage.already_supported_areas)
    read_only: list[ApiCoverageGap] = []
    risky: list[ApiCoverageGap] = []
    unknown: list[ApiCoverageGap] = []
    for endpoint in catalog.endpoints:
        if endpoint.path_area in supported_areas:
            continue
        gap = ApiCoverageGap(
            resource_family=endpoint.path_area,
            endpoint=endpoint,
            supported=False,
            recommendation=_recommendation(endpoint.safety),
            deferred=endpoint.safety != CatalogEndpointSafety.READ_ONLY,
            notes=list(endpoint.safety_reasons),
        )
        if endpoint.safety == CatalogEndpointSafety.READ_ONLY:
            read_only.append(gap)
        elif endpoint.safety == CatalogEndpointSafety.WRITE_OR_MUTATION:
            risky.append(gap)
        else:
            unknown.append(gap)
    return ApiCoverageGapReport(
        source_path=str(oas_path),
        supported_areas=coverage.already_supported_areas,
        unsupported_read_only=read_only,
        unsupported_risky_write=risky,
        unknown=unknown,
        recommended_next_candidates=read_only,
        deferred_candidates=[*risky, *unknown],
        findings=[
            ApiMaintenanceFinding(
                severity="info",
                code="metadata_only",
                message=(
                    "Coverage gaps are recommendations from local metadata. "
                    "Human endpoint-shape and permission review is required."
                ),
            )
        ],
    )


def _recommendation(safety: CatalogEndpointSafety) -> str:
    """Return a conservative recommendation for one safety classification."""
    if safety == CatalogEndpointSafety.READ_ONLY:
        return "Candidate for human-reviewed read-only SDK coverage."
    if safety == CatalogEndpointSafety.WRITE_OR_MUTATION:
        return "Defer: write or mutation behavior is outside this maintenance assistant."
    return "Review endpoint shape and semantics before considering SDK coverage."
