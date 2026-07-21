"""Typed models for PyProcore plugin manifests.

Phase 11A plugin support is metadata-first. These models describe potential
extensions without importing, installing, or executing plugin code.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import Field, field_validator

from pyprocore.models.base import ProcoreModel
from pyprocore.plugins.hooks import PluginHookMetadata

PLUGIN_SCHEMA_VERSION = "1"


class PluginCapability(str, Enum):
    """Supported metadata-only plugin capability categories."""

    WORKFLOW = "workflow"
    EXPORTER = "exporter"
    VALIDATOR = "validator"
    FORMATTER = "formatter"
    REPORT = "report"
    INTEGRATION_ADAPTER = "integration_adapter"
    AGENT_METADATA = "agent_metadata"
    MCP_METADATA = "mcp_metadata"


class PluginSafetyLevel(str, Enum):
    """Safety classification for plugin manifests."""

    METADATA_ONLY = "metadata_only"
    LOCAL_READ_ONLY = "local_read_only"
    LOCAL_FILE_OUTPUT = "local_file_output"


class PluginMetadata(ProcoreModel):
    """Human-readable plugin identity and ownership metadata."""

    name: str
    version: str
    description: str
    author: str | None = None
    homepage: str | None = None
    tags: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class PluginManifest(ProcoreModel):
    """Serializable manifest describing a safe PyProcore plugin.

    Attributes:
        schema_version: Manifest schema version supported by PyProcore.
        name: Stable plugin identifier.
        version: Plugin version string.
        description: Human-readable plugin purpose.
        author: Optional author or organization name.
        publisher: Optional trusted publisher identifier.
        publisher_url: Optional publisher homepage.
        signature: Optional signature metadata. PyProcore does not verify it.
        checksum_sha256: Optional local checksum metadata. PyProcore does not
            fetch remote plugin artifacts.
        min_pyprocore_version: Optional minimum supported PyProcore version.
        max_pyprocore_version: Optional maximum supported PyProcore version.
        allowed_capability_categories: Optional declared capability boundary.
        safety_boundaries: Optional safety declarations from the publisher.
        homepage: Optional public project page.
        capabilities: Metadata-only capability categories.
        requires_pyprocore: Optional PyProcore version requirement.
        entry_points: Optional descriptive entry-point metadata.
        tags: Searchable labels.
        safety_level: Safety classification.
        enabled_by_default: Whether the manifest is considered active by default.
        supports_sync: Whether future sync hooks may be supported.
        supports_async: Whether future async hooks may be supported.
        supports_agent_metadata: Whether the plugin can describe agent metadata.
        supports_cli: Whether future CLI metadata may be supported.
        hooks: Optional hook metadata. Metadata alone is not executable.
        notes: Additional safety or usage notes.
    """

    schema_version: str = PLUGIN_SCHEMA_VERSION
    name: str
    version: str
    description: str
    author: str | None = None
    publisher: str | None = None
    publisher_url: str | None = None
    signature: str | None = None
    checksum_sha256: str | None = None
    min_pyprocore_version: str | None = None
    max_pyprocore_version: str | None = None
    allowed_capability_categories: list[PluginCapability] = Field(default_factory=list)
    safety_boundaries: list[str] = Field(default_factory=list)
    homepage: str | None = None
    capabilities: list[PluginCapability] = Field(default_factory=list)
    requires_pyprocore: str | None = None
    entry_points: dict[str, str] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    safety_level: PluginSafetyLevel = PluginSafetyLevel.METADATA_ONLY
    enabled_by_default: bool = False
    supports_sync: bool = False
    supports_async: bool = False
    supports_agent_metadata: bool = False
    supports_cli: bool = False
    hooks: list[PluginHookMetadata] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    @field_validator("capabilities", mode="after")
    @classmethod
    def _deduplicate_capabilities(
        cls,
        value: list[PluginCapability],
    ) -> list[PluginCapability]:
        """Return capabilities in declaration order without duplicates."""
        unique: list[PluginCapability] = []
        for item in value:
            if item not in unique:
                unique.append(item)
        return unique


class PluginRegistration(ProcoreModel):
    """Registry entry for one validated plugin manifest."""

    manifest: PluginManifest
    source: str = "local"
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PluginValidationResult(ProcoreModel):
    """Result of validating plugin manifest metadata."""

    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    manifest: PluginManifest | None = None


class PluginRegistryManifest(ProcoreModel):
    """JSON-serializable export of registered plugin metadata."""

    schema_version: str = PLUGIN_SCHEMA_VERSION
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    plugin_count: int
    plugins: list[PluginManifest]
    mode: str = "metadata_only"


class PluginDiscoveryResult(ProcoreModel):
    """Result of local safe plugin discovery."""

    discovered: list[PluginManifest] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    source: str = "built-in"


PluginManifestData = dict[str, Any]
