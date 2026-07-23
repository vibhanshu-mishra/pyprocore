"""Typed models for local OpenAPI/OAS endpoint catalog inspection."""

from __future__ import annotations

from enum import Enum

from pydantic import Field

from pyprocore.models.base import ProcoreModel

CATALOG_SCHEMA_VERSION = "1"
CATALOG_MODE = "local_oas_metadata_only"


class CatalogEndpointSafety(str, Enum):
    """Safety classification for one catalog endpoint."""

    READ_ONLY = "read_only"
    WRITE_OR_MUTATION = "write_or_mutation"
    UNKNOWN = "unknown"


class CatalogParameter(ProcoreModel):
    """OpenAPI parameter metadata for one endpoint.

    Attributes:
        name: Parameter name from the OAS document.
        location: Parameter location such as path, query, or header.
        required: Whether the parameter is required by the endpoint.
        schema_type: Simple schema type when declared.
        description: Optional human-readable description.
    """

    name: str
    location: str | None = None
    required: bool = False
    schema_type: str | None = None
    description: str | None = None


class CatalogEndpoint(ProcoreModel):
    """Metadata for one endpoint discovered in a local OAS file.

    Attributes:
        method: Uppercase HTTP method.
        path: Endpoint path from the OAS paths object.
        path_area: Derived resource area used for coverage grouping.
        operation_id: Optional OAS operationId.
        summary: Optional OAS operation summary.
        description: Optional OAS operation description.
        tags: Optional OAS operation tags.
        parameters: Path and operation parameters.
        safety: Metadata-only safety classification.
        safety_reasons: Explanation of the safety classification.
    """

    method: str
    path: str
    path_area: str
    operation_id: str | None = None
    summary: str | None = None
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    parameters: list[CatalogParameter] = Field(default_factory=list)
    safety: CatalogEndpointSafety
    safety_reasons: list[str] = Field(default_factory=list)


class CatalogSummary(ProcoreModel):
    """Summary counts for a local OAS endpoint catalog."""

    schema_version: str = CATALOG_SCHEMA_VERSION
    source_path: str | None = None
    title: str | None = None
    version: str | None = None
    endpoint_count: int
    method_counts: dict[str, int] = Field(default_factory=dict)
    path_area_counts: dict[str, int] = Field(default_factory=dict)
    read_only_count: int
    write_or_mutation_count: int
    unknown_count: int
    mode: str = CATALOG_MODE
    execution_enabled: bool = False
    remote_fetch_enabled: bool = False


class CoverageFinding(ProcoreModel):
    """Coverage summary for one derived endpoint area."""

    area: str
    supported: bool
    endpoint_count: int
    read_only_count: int
    risky_count: int
    unknown_count: int
    notes: list[str] = Field(default_factory=list)


class CoverageReport(ProcoreModel):
    """Coverage and safety report for a local OAS endpoint catalog.

    Attributes:
        summary: High-level catalog summary.
        already_supported_areas: Areas that map to existing PyProcore coverage.
        unsupported_areas: Areas not currently represented in PyProcore coverage.
        read_only_candidates: Endpoints classified as likely read-only.
        risky_write_candidates: Endpoints classified as write or mutation risk.
        unknown_candidates: Endpoints whose safety is unclear.
        findings: Per-area coverage findings.
    """

    schema_version: str = CATALOG_SCHEMA_VERSION
    source_path: str | None = None
    summary: CatalogSummary
    already_supported_areas: list[str] = Field(default_factory=list)
    unsupported_areas: list[str] = Field(default_factory=list)
    read_only_candidates: list[CatalogEndpoint] = Field(default_factory=list)
    risky_write_candidates: list[CatalogEndpoint] = Field(default_factory=list)
    unknown_candidates: list[CatalogEndpoint] = Field(default_factory=list)
    findings: list[CoverageFinding] = Field(default_factory=list)
    mode: str = CATALOG_MODE
    execution_enabled: bool = False
    remote_fetch_enabled: bool = False


class OASCatalog(ProcoreModel):
    """Parsed local OpenAPI/OAS endpoint catalog.

    Attributes:
        source_path: Local JSON file path used to load the catalog.
        title: Optional title from the OAS info object.
        version: Optional version from the OAS info object.
        endpoints: Parsed endpoint metadata.
    """

    schema_version: str = CATALOG_SCHEMA_VERSION
    source_path: str | None = None
    title: str | None = None
    version: str | None = None
    endpoints: list[CatalogEndpoint] = Field(default_factory=list)
    mode: str = CATALOG_MODE
    execution_enabled: bool = False
    remote_fetch_enabled: bool = False

    def list_endpoints(self, method: str | None = None) -> list[CatalogEndpoint]:
        """Return endpoints, optionally filtered by HTTP method.

        Args:
            method: Optional HTTP method filter such as GET or POST.

        Returns:
            Matching catalog endpoints in OAS declaration order.
        """
        if method is None:
            return list(self.endpoints)
        normalized_method = method.upper()
        return [endpoint for endpoint in self.endpoints if endpoint.method == normalized_method]

    def summarize_by_method(self) -> dict[str, int]:
        """Return endpoint counts grouped by HTTP method."""
        counts: dict[str, int] = {}
        for endpoint in self.endpoints:
            counts[endpoint.method] = counts.get(endpoint.method, 0) + 1
        return dict(sorted(counts.items()))

    def summarize_by_path_area(self) -> dict[str, int]:
        """Return endpoint counts grouped by derived resource area."""
        counts: dict[str, int] = {}
        for endpoint in self.endpoints:
            counts[endpoint.path_area] = counts.get(endpoint.path_area, 0) + 1
        return dict(sorted(counts.items()))

    def summary(self) -> CatalogSummary:
        """Build a high-level summary for this catalog."""
        read_only_count = sum(
            endpoint.safety == CatalogEndpointSafety.READ_ONLY for endpoint in self.endpoints
        )
        risky_count = sum(
            endpoint.safety == CatalogEndpointSafety.WRITE_OR_MUTATION
            for endpoint in self.endpoints
        )
        unknown_count = sum(
            endpoint.safety == CatalogEndpointSafety.UNKNOWN for endpoint in self.endpoints
        )
        return CatalogSummary(
            source_path=self.source_path,
            title=self.title,
            version=self.version,
            endpoint_count=len(self.endpoints),
            method_counts=self.summarize_by_method(),
            path_area_counts=self.summarize_by_path_area(),
            read_only_count=read_only_count,
            write_or_mutation_count=risky_count,
            unknown_count=unknown_count,
        )
