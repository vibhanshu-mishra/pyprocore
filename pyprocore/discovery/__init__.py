"""Local metadata-only discovery router for PyProcore capabilities."""

from pyprocore.discovery.models import (
    DISCOVERY_MODE,
    DISCOVERY_SCHEMA_VERSION,
    DiscoveryBundle,
    DiscoveryCapability,
    DiscoveryQuery,
    DiscoveryReport,
    DiscoveryRouteCandidate,
    DiscoveryRouteResult,
)
from pyprocore.discovery.registry import (
    build_discovery_bundle,
    build_discovery_report,
    get_discovery_capability,
    list_discovery_capabilities,
)
from pyprocore.discovery.reports import (
    discovery_bundle_to_json,
    discovery_bundle_to_markdown,
    discovery_capability_to_json,
    discovery_capability_to_markdown,
    discovery_report_to_json,
    discovery_report_to_markdown,
    discovery_route_result_to_json,
    discovery_route_result_to_markdown,
)
from pyprocore.discovery.router import (
    route_discovery_query,
    search_discovery_capabilities,
    search_oas_catalog_capabilities,
)

__all__ = [
    "DISCOVERY_MODE",
    "DISCOVERY_SCHEMA_VERSION",
    "DiscoveryBundle",
    "DiscoveryCapability",
    "DiscoveryQuery",
    "DiscoveryReport",
    "DiscoveryRouteCandidate",
    "DiscoveryRouteResult",
    "build_discovery_bundle",
    "build_discovery_report",
    "discovery_bundle_to_json",
    "discovery_bundle_to_markdown",
    "discovery_capability_to_json",
    "discovery_capability_to_markdown",
    "discovery_report_to_json",
    "discovery_report_to_markdown",
    "discovery_route_result_to_json",
    "discovery_route_result_to_markdown",
    "get_discovery_capability",
    "list_discovery_capabilities",
    "route_discovery_query",
    "search_discovery_capabilities",
    "search_oas_catalog_capabilities",
]
