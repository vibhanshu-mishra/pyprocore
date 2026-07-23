"""Local OAS catalog inspection for safe PyProcore coverage intelligence."""

from pyprocore.catalog.models import (
    CATALOG_MODE,
    CATALOG_SCHEMA_VERSION,
    CatalogEndpoint,
    CatalogEndpointSafety,
    CatalogParameter,
    CatalogSummary,
    CoverageFinding,
    CoverageReport,
    OASCatalog,
)
from pyprocore.catalog.oas import (
    PYPROCORE_SUPPORTED_AREAS,
    RISKY_TERMS,
    classify_endpoint_safety,
    compare_catalog_to_pyprocore_supported_coverage,
    list_endpoints,
    load_oas_catalog,
    summarize_by_method,
    summarize_by_path_area,
)
from pyprocore.catalog.reports import (
    catalog_endpoints_to_json,
    catalog_endpoints_to_markdown,
    catalog_summary_to_json,
    catalog_summary_to_markdown,
    coverage_report_to_json,
    coverage_report_to_markdown,
)

__all__ = [
    "CATALOG_MODE",
    "CATALOG_SCHEMA_VERSION",
    "PYPROCORE_SUPPORTED_AREAS",
    "RISKY_TERMS",
    "CatalogEndpoint",
    "CatalogEndpointSafety",
    "CatalogParameter",
    "CatalogSummary",
    "CoverageFinding",
    "CoverageReport",
    "OASCatalog",
    "catalog_endpoints_to_json",
    "catalog_endpoints_to_markdown",
    "catalog_summary_to_json",
    "catalog_summary_to_markdown",
    "classify_endpoint_safety",
    "compare_catalog_to_pyprocore_supported_coverage",
    "coverage_report_to_json",
    "coverage_report_to_markdown",
    "list_endpoints",
    "load_oas_catalog",
    "summarize_by_method",
    "summarize_by_path_area",
]
