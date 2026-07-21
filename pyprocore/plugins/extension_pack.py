"""Safe local extension-pack manifest support for PyProcore plugins."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic import ValidationError as PydanticValidationError

from pyprocore.core.exceptions import ValidationError
from pyprocore.models.base import ProcoreModel
from pyprocore.plugins.config import (
    PLUGIN_CONFIG_SCHEMA_VERSION,
    PluginConfigFinding,
    _scan_safe_json_value,
)
from pyprocore.plugins.hook_registry import SAFE_HOOK_NAME_PATTERN
from pyprocore.plugins.hooks import PluginHookMetadata, PluginHookType, redact_sensitive_text
from pyprocore.plugins.models import PluginCapability, PluginManifest, PluginSafetyLevel
from pyprocore.plugins.validation import SAFE_PLUGIN_NAME_PATTERN, SAFE_VERSION_PATTERN


class PluginExtensionPackItem(ProcoreModel):
    """One plugin manifest reference inside an extension-pack manifest."""

    plugin_name: str
    required: bool = False
    notes: list[str] = Field(default_factory=list)


class PluginExtensionPack(ProcoreModel):
    """Metadata-only extension-pack manifest.

    Extension packs group plugin and hook metadata for user convenience. They do
    not import modules, install packages, register callables, or execute hooks.
    """

    schema_version: str = PLUGIN_CONFIG_SCHEMA_VERSION
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
    included_plugins: list[PluginExtensionPackItem] = Field(default_factory=list)
    included_hooks: list[PluginHookMetadata] = Field(default_factory=list)
    capabilities: list[PluginCapability] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    safety_level: PluginSafetyLevel = PluginSafetyLevel.METADATA_ONLY
    requires_pyprocore: str | None = ">=2.3.0"


class PluginExtensionPackManifest(ProcoreModel):
    """Serializable collection of local extension-pack manifests."""

    schema_version: str = PLUGIN_CONFIG_SCHEMA_VERSION
    extension_pack_count: int
    extension_packs: list[PluginExtensionPack]
    mode: str = "metadata_only"


class PluginExtensionPackValidationResult(ProcoreModel):
    """Result of validating extension-pack metadata."""

    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    findings: list[PluginConfigFinding] = Field(default_factory=list)
    extension_pack: PluginExtensionPack | None = None


def load_extension_pack_manifest_from_dict(data: Mapping[str, Any]) -> PluginExtensionPack:
    """Load a local extension-pack manifest from dictionary data."""
    try:
        return PluginExtensionPack.model_validate(dict(data))
    except PydanticValidationError as exc:
        raise ValidationError(redact_sensitive_text(str(exc))) from exc


def load_extension_pack_manifest_from_file(path: Path | str) -> PluginExtensionPack:
    """Load a local JSON extension-pack manifest file."""
    data = _read_local_json_file(path)
    return load_extension_pack_manifest_from_dict(data)


def validate_extension_pack_manifest(
    extension_pack: PluginExtensionPack,
) -> PluginExtensionPackValidationResult:
    """Validate extension-pack metadata without executing or loading code."""
    errors: list[str] = []
    warnings: list[str] = []

    if extension_pack.schema_version != PLUGIN_CONFIG_SCHEMA_VERSION:
        errors.append(
            "Unsupported extension-pack schema version "
            f"{extension_pack.schema_version!r}; expected {PLUGIN_CONFIG_SCHEMA_VERSION!r}."
        )
    if not SAFE_PLUGIN_NAME_PATTERN.fullmatch(extension_pack.name):
        errors.append("Extension-pack name must be a safe lowercase metadata identifier.")
    if not SAFE_VERSION_PATTERN.fullmatch(extension_pack.version):
        errors.append("Extension-pack version must look like a semantic version.")
    if not extension_pack.description.strip():
        errors.append("Extension-pack description is required.")
    if extension_pack.safety_level != PluginSafetyLevel.METADATA_ONLY:
        errors.append("Extension packs must remain metadata_only in Phase 11C.")
    if not extension_pack.capabilities:
        warnings.append("Extension pack declares no capabilities.")

    for item in extension_pack.included_plugins:
        if not SAFE_PLUGIN_NAME_PATTERN.fullmatch(item.plugin_name):
            errors.append(f"Extension pack includes unsafe plugin {item.plugin_name!r}.")

    for hook in extension_pack.included_hooks:
        if not SAFE_HOOK_NAME_PATTERN.fullmatch(hook.hook_name):
            errors.append(f"Extension pack includes unsafe hook {hook.hook_name!r}.")

    for capability in extension_pack.capabilities:
        if capability not in PluginCapability:
            errors.append(f"Unsupported extension-pack capability: {capability}.")

    _scan_safe_json_value(extension_pack.model_dump(mode="json"), "extension_pack", errors)
    findings = [PluginConfigFinding(severity="error", message=message) for message in errors] + [
        PluginConfigFinding(severity="warning", message=message) for message in warnings
    ]
    return PluginExtensionPackValidationResult(
        valid=not errors,
        errors=errors,
        warnings=warnings,
        findings=findings,
        extension_pack=extension_pack if not errors else None,
    )


def validate_extension_pack_manifest_data(
    data: Mapping[str, Any],
) -> PluginExtensionPackValidationResult:
    """Validate extension-pack dictionary data."""
    try:
        extension_pack = load_extension_pack_manifest_from_dict(data)
    except ValidationError as exc:
        return PluginExtensionPackValidationResult(valid=False, errors=[str(exc)])
    return validate_extension_pack_manifest(extension_pack)


def export_extension_pack_template() -> PluginExtensionPack:
    """Return a safe starter extension-pack manifest."""
    return PluginExtensionPack(
        name="starter_export_pack",
        version="1.0.0",
        description="Metadata-only bundle for local export helpers.",
        author="PyProcore",
        included_plugins=[
            PluginExtensionPackItem(plugin_name="csv_exporter_plugin"),
            PluginExtensionPackItem(plugin_name="jsonl_exporter_plugin"),
        ],
        included_hooks=[
            PluginHookMetadata(
                hook_name="validate_required_fields",
                plugin_name="enterprise_readiness_plugin",
                hook_type=PluginHookType.VALIDATOR,
                description="Validate required fields before exporting records.",
            ),
            PluginHookMetadata(
                hook_name="format_records_as_summary",
                plugin_name="csv_exporter_plugin",
                hook_type=PluginHookType.FORMATTER,
                description="Format records as a compact local summary.",
            ),
        ],
        capabilities=[PluginCapability.EXPORTER, PluginCapability.FORMATTER],
        tags=["example", "metadata-only"],
        notes=[
            "Extension packs are descriptive metadata only.",
            "They do not install, import, or execute plugin code.",
        ],
    )


def summarize_extension_pack_with_registry_metadata(
    extension_pack: PluginExtensionPack,
    manifests: list[PluginManifest],
) -> PluginExtensionPackManifest:
    """Return metadata for one extension pack alongside known plugin manifests."""
    known_names = {manifest.name for manifest in manifests}
    warnings = [
        f"Plugin {item.plugin_name!r} is not currently registered."
        for item in extension_pack.included_plugins
        if item.plugin_name not in known_names
    ]
    if warnings:
        extension_pack.notes = [*extension_pack.notes, *warnings]
    return PluginExtensionPackManifest(
        extension_pack_count=1,
        extension_packs=[extension_pack],
    )


def export_extension_pack_summary(extension_pack: PluginExtensionPack) -> str:
    """Return a human-readable extension-pack summary."""
    lines = [
        "PyProcore extension-pack summary.",
        f"Name: {extension_pack.name}",
        f"Version: {extension_pack.version}",
        f"Safety level: {extension_pack.safety_level.value}",
        f"Included plugins: {len(extension_pack.included_plugins)}",
        f"Included hooks: {len(extension_pack.included_hooks)}",
        f"Capabilities: {', '.join(item.value for item in extension_pack.capabilities) or 'none'}",
        "Mode: metadata only; no plugin code is loaded, registered, or executed.",
    ]
    return "\n".join(lines)


def _read_local_json_file(path: Path | str) -> dict[str, Any]:
    """Read a local JSON object from disk after rejecting unsafe path forms."""
    target = Path(path)
    path_text = str(path)
    if "://" in path_text:
        raise ValidationError("Remote extension-pack URLs are not supported.")
    if any(part == ".." for part in target.parts):
        raise ValidationError("Extension-pack paths must not contain path traversal.")
    if target.suffix.casefold() != ".json":
        raise ValidationError("Extension-pack files must use JSON with a .json suffix.")
    try:
        parsed = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Extension-pack JSON is invalid: {exc.msg}.") from exc
    if not isinstance(parsed, dict):
        raise ValidationError("Extension-pack JSON must contain an object at the top level.")
    return parsed
