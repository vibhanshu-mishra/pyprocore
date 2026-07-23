"""Typed models for local capability discovery metadata."""

from __future__ import annotations

from pydantic import Field

from pyprocore.models.base import ProcoreModel

DISCOVERY_SCHEMA_VERSION = "1"
DISCOVERY_MODE = "local_discovery_metadata_only"


class DiscoveryCapability(ProcoreModel):
    """Metadata for one safe PyProcore capability.

    Attributes:
        name: Stable capability identifier.
        title: Human-readable capability title.
        description: Short metadata-only description.
        resource_family: Procore resource family or SDK area.
        operations: Public read/helper operations associated with the capability.
        keywords: Search terms used for deterministic local routing.
        examples: Example user intents or CLI snippets.
        safety_labels: Safety and boundary labels for the capability.
        source: Source of the metadata, such as builtin or local_oas.
        metadata_only: Whether the capability entry is metadata-only.
        execution_enabled: Whether this layer can execute the capability.
        procore_api_call_required: Whether discovery itself requires a Procore API call.
        write_enabled: Whether writes are enabled by this capability entry.
        mcp_execution_enabled: Whether MCP execution is enabled by this entry.
        external_ai_required: Whether external AI/model calls are required.
    """

    name: str
    title: str
    description: str
    resource_family: str
    operations: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)
    safety_labels: list[str] = Field(default_factory=list)
    source: str = "builtin"
    metadata_only: bool = True
    execution_enabled: bool = False
    procore_api_call_required: bool = False
    write_enabled: bool = False
    mcp_execution_enabled: bool = False
    external_ai_required: bool = False


class DiscoveryRouteCandidate(ProcoreModel):
    """Ranked route suggestion for a local discovery query.

    Attributes:
        capability: Matched capability metadata.
        score: Deterministic lexical score.
        matched_terms: Query terms matched by the capability metadata.
        reasons: Human-readable scoring reasons.
        metadata_only: Whether the candidate is metadata-only.
        execution_enabled: Whether candidate execution is enabled.
        procore_api_call_required: Whether discovery requires a Procore API call.
        write_enabled: Whether writes are enabled by this candidate.
        mcp_execution_enabled: Whether MCP execution is enabled by this candidate.
        external_ai_required: Whether external AI/model calls are required.
    """

    capability: DiscoveryCapability
    score: float
    matched_terms: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    metadata_only: bool = True
    execution_enabled: bool = False
    procore_api_call_required: bool = False
    write_enabled: bool = False
    mcp_execution_enabled: bool = False
    external_ai_required: bool = False


class DiscoveryQuery(ProcoreModel):
    """Local discovery query metadata.

    Attributes:
        text: User intent or search text.
        limit: Maximum route candidates to return.
        oas_path: Optional local OAS JSON path used for metadata enrichment.
        metadata_only: Whether the query is metadata-only.
        execution_enabled: Whether this query can execute capabilities.
        remote_fetch_enabled: Whether this query can fetch remote catalogs.
    """

    text: str
    limit: int = 10
    oas_path: str | None = None
    metadata_only: bool = True
    execution_enabled: bool = False
    remote_fetch_enabled: bool = False


class DiscoveryRouteResult(ProcoreModel):
    """Ranked local route suggestions for one discovery query."""

    schema_version: str = DISCOVERY_SCHEMA_VERSION
    mode: str = DISCOVERY_MODE
    query: DiscoveryQuery
    candidates: list[DiscoveryRouteCandidate] = Field(default_factory=list)
    metadata_only: bool = True
    execution_enabled: bool = False
    procore_api_call_required: bool = False
    write_enabled: bool = False
    mcp_execution_enabled: bool = False
    external_ai_required: bool = False
    remote_fetch_enabled: bool = False


class DiscoveryBundle(ProcoreModel):
    """Inventory of local discovery capabilities."""

    schema_version: str = DISCOVERY_SCHEMA_VERSION
    mode: str = DISCOVERY_MODE
    capabilities: list[DiscoveryCapability] = Field(default_factory=list)
    metadata_only: bool = True
    execution_enabled: bool = False
    procore_api_call_required: bool = False
    write_enabled: bool = False
    mcp_execution_enabled: bool = False
    external_ai_required: bool = False


class DiscoveryReport(ProcoreModel):
    """Inventory and safety report for discovery metadata."""

    schema_version: str = DISCOVERY_SCHEMA_VERSION
    mode: str = DISCOVERY_MODE
    capability_count: int
    resource_families: list[str] = Field(default_factory=list)
    capability_names: list[str] = Field(default_factory=list)
    safety_boundaries: list[str] = Field(default_factory=list)
    metadata_only: bool = True
    execution_enabled: bool = False
    procore_api_call_required: bool = False
    write_enabled: bool = False
    mcp_execution_enabled: bool = False
    external_ai_required: bool = False
