"""Safe JSON plugin configuration helpers for PyProcore.

Phase 11C configuration is metadata-only. Loading a config never imports plugin
code, installs packages, registers hook callables, fetches remote resources, or
calls Procore.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic import ValidationError as PydanticValidationError

from pyprocore.core.exceptions import ValidationError
from pyprocore.models.base import ProcoreModel
from pyprocore.plugins.hook_registry import SAFE_HOOK_NAME_PATTERN
from pyprocore.plugins.hooks import PluginHookType, redact_sensitive_text
from pyprocore.plugins.models import PluginCapability, PluginManifest
from pyprocore.plugins.validation import SAFE_PLUGIN_NAME_PATTERN

PLUGIN_CONFIG_SCHEMA_VERSION = "1"
SAFE_CONFIG_POLICIES = {"metadata_only", "local_metadata_only", "read_only_metadata"}
SECRET_KEYWORDS = (
    "access_token",
    "refresh_token",
    "client_secret",
    "authorization",
    "password",
    "secret",
    "token",
)
UNSAFE_COMMAND_FRAGMENTS = (
    " ".join(("pip", "install")),
    "python -m pip",
    "curl ",
    "wget ",
    "npm install",
    "uv pip",
)
UNSAFE_IMPORT_FRAGMENTS = (
    "importlib",
    "__import__",
)
UNSAFE_WRITE_PREFIXES = (
    "create",
    "update",
    "delete",
    "upload",
    "approve",
    "reject",
    "submit",
    "payment",
    "pay",
    "write",
    "mutate",
)


class PluginConfigSource(str, Enum):
    """Trusted local source categories for plugin configuration."""

    DICT = "dict"
    LOCAL_FILE = "local_file"
    TEMPLATE = "template"


class PluginConfigFinding(ProcoreModel):
    """One validation finding for plugin configuration metadata."""

    severity: str
    message: str
    field: str | None = None


class PluginHookPreference(ProcoreModel):
    """Preference for hook metadata, without registering or executing a hook."""

    hook_name: str
    hook_type: PluginHookType
    enabled: bool = True
    priority: int = 100
    options: dict[str, Any] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)


class PluginCapabilityPreference(ProcoreModel):
    """Preference for a plugin capability category."""

    capability: PluginCapability
    enabled: bool = True
    notes: list[str] = Field(default_factory=list)


class PluginConfig(ProcoreModel):
    """JSON-serializable plugin configuration metadata.

    This model stores user preferences only. It cannot reference executable
    Python code, import paths, shell commands, URLs, or credentials.
    """

    config_version: str = PLUGIN_CONFIG_SCHEMA_VERSION
    enabled_plugins: list[str] = Field(default_factory=list)
    disabled_plugins: list[str] = Field(default_factory=list)
    enabled_capabilities: list[PluginCapability] = Field(default_factory=list)
    disabled_capabilities: list[PluginCapability] = Field(default_factory=list)
    hook_preferences: list[PluginHookPreference] = Field(default_factory=list)
    capability_preferences: list[PluginCapabilityPreference] = Field(default_factory=list)
    extension_packs: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    safety_policy: str = "metadata_only"


class PluginConfigValidationResult(ProcoreModel):
    """Result of validating plugin configuration metadata."""

    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    findings: list[PluginConfigFinding] = Field(default_factory=list)
    config: PluginConfig | None = None


class PluginConfigSummary(ProcoreModel):
    """Metadata-only summary of config preferences applied to known manifests."""

    config_version: str
    enabled_plugins: list[str] = Field(default_factory=list)
    disabled_plugins: list[str] = Field(default_factory=list)
    enabled_capabilities: list[str] = Field(default_factory=list)
    disabled_capabilities: list[str] = Field(default_factory=list)
    hook_preferences: list[str] = Field(default_factory=list)
    extension_packs: list[str] = Field(default_factory=list)
    matched_plugins: list[str] = Field(default_factory=list)
    unmatched_plugins: list[str] = Field(default_factory=list)
    mode: str = "metadata_filtering_only"


def load_plugin_config_from_dict(data: Mapping[str, Any]) -> PluginConfig:
    """Load plugin configuration from a local dictionary.

    Args:
        data: JSON-compatible configuration data.

    Returns:
        Parsed plugin configuration model.

    Raises:
        ValidationError: If data cannot be parsed.
    """
    try:
        return PluginConfig.model_validate(dict(data))
    except PydanticValidationError as exc:
        raise ValidationError(redact_sensitive_text(str(exc))) from exc


def load_plugin_config_from_file(path: Path | str) -> PluginConfig:
    """Load plugin configuration from a local JSON file."""
    data = _read_local_json_file(path)
    return load_plugin_config_from_dict(data)


def validate_plugin_config(config: PluginConfig) -> PluginConfigValidationResult:
    """Validate plugin configuration safety rules without executing anything."""
    errors: list[str] = []
    warnings: list[str] = []

    if config.config_version != PLUGIN_CONFIG_SCHEMA_VERSION:
        errors.append(
            "Unsupported plugin config version "
            f"{config.config_version!r}; expected {PLUGIN_CONFIG_SCHEMA_VERSION!r}."
        )
    if config.safety_policy not in SAFE_CONFIG_POLICIES:
        errors.append("Plugin config safety_policy must be metadata-only.")

    _validate_plugin_names(config.enabled_plugins, "enabled_plugins", errors)
    _validate_plugin_names(config.disabled_plugins, "disabled_plugins", errors)
    _validate_plugin_names(config.extension_packs, "extension_packs", errors)

    for preference in config.hook_preferences:
        if not SAFE_HOOK_NAME_PATTERN.fullmatch(preference.hook_name):
            errors.append(f"Hook preference {preference.hook_name!r} has an unsafe hook name.")
        if not preference.enabled:
            warnings.append(f"Hook {preference.hook_name!r} is disabled by configuration.")

    for capability in config.enabled_capabilities + config.disabled_capabilities:
        if capability not in PluginCapability:
            errors.append(f"Unsupported plugin capability: {capability}.")

    _scan_safe_json_value(config.model_dump(mode="json"), "config", errors)
    findings = [PluginConfigFinding(severity="error", message=message) for message in errors] + [
        PluginConfigFinding(severity="warning", message=message) for message in warnings
    ]

    return PluginConfigValidationResult(
        valid=not errors,
        errors=errors,
        warnings=warnings,
        findings=findings,
        config=config if not errors else None,
    )


def validate_plugin_config_data(data: Mapping[str, Any]) -> PluginConfigValidationResult:
    """Validate plugin configuration dictionary data."""
    try:
        config = load_plugin_config_from_dict(data)
    except ValidationError as exc:
        return PluginConfigValidationResult(valid=False, errors=[str(exc)])
    return validate_plugin_config(config)


def export_plugin_config_template() -> PluginConfig:
    """Return a safe starter plugin configuration template."""
    return PluginConfig(
        enabled_plugins=["csv_exporter_plugin", "jsonl_exporter_plugin"],
        enabled_capabilities=[PluginCapability.EXPORTER, PluginCapability.FORMATTER],
        hook_preferences=[
            PluginHookPreference(
                hook_name="validate_required_fields",
                hook_type=PluginHookType.VALIDATOR,
                options={"required_fields": ["id", "name"]},
            )
        ],
        extension_packs=["starter_export_pack"],
        tags=["example", "metadata-only"],
        notes=[
            "This file stores metadata preferences only.",
            "It does not install plugins, import modules, or execute hooks.",
        ],
    )


def merge_plugin_config_with_registry_metadata(
    config: PluginConfig,
    manifests: list[PluginManifest],
) -> PluginConfigSummary:
    """Return metadata filtered by plugin config preferences."""
    by_name = {manifest.name: manifest for manifest in manifests}
    enabled_names = set(config.enabled_plugins)
    disabled_names = set(config.disabled_plugins)
    enabled_capabilities = set(config.enabled_capabilities)
    disabled_capabilities = set(config.disabled_capabilities)
    matched: list[str] = []

    for manifest in manifests:
        capability_match = not enabled_capabilities or any(
            capability in enabled_capabilities for capability in manifest.capabilities
        )
        disabled_capability_match = any(
            capability in disabled_capabilities for capability in manifest.capabilities
        )
        if manifest.name in disabled_names or disabled_capability_match:
            continue
        if manifest.name in enabled_names or capability_match:
            matched.append(manifest.name)

    requested = enabled_names | disabled_names | set(config.extension_packs)
    unmatched = sorted(name for name in requested if name not in by_name)
    return PluginConfigSummary(
        config_version=config.config_version,
        enabled_plugins=sorted(enabled_names),
        disabled_plugins=sorted(disabled_names),
        enabled_capabilities=sorted(capability.value for capability in enabled_capabilities),
        disabled_capabilities=sorted(capability.value for capability in disabled_capabilities),
        hook_preferences=sorted(preference.hook_name for preference in config.hook_preferences),
        extension_packs=list(config.extension_packs),
        matched_plugins=sorted(matched),
        unmatched_plugins=unmatched,
    )


def export_plugin_config_summary(config: PluginConfig) -> str:
    """Return a human-readable plugin configuration summary."""
    lines = [
        "PyProcore plugin configuration summary.",
        f"Config version: {config.config_version}",
        f"Safety policy: {config.safety_policy}",
        f"Enabled plugins: {len(config.enabled_plugins)}",
        f"Disabled plugins: {len(config.disabled_plugins)}",
        (
            "Enabled capabilities: "
            f"{', '.join(item.value for item in config.enabled_capabilities) or 'none'}"
        ),
        f"Hook preferences: {len(config.hook_preferences)}",
        f"Extension packs: {len(config.extension_packs)}",
        "Mode: metadata filtering only; no plugin code is loaded or executed.",
    ]
    return "\n".join(lines)


def _read_local_json_file(path: Path | str) -> dict[str, Any]:
    """Read a local JSON object from disk after rejecting unsafe path forms."""
    target = Path(path)
    path_text = str(path)
    if "://" in path_text:
        raise ValidationError("Remote plugin config URLs are not supported.")
    if any(part == ".." for part in target.parts):
        raise ValidationError("Plugin config paths must not contain path traversal.")
    if target.suffix.casefold() != ".json":
        raise ValidationError("Plugin config files must use JSON with a .json suffix.")
    try:
        parsed = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Plugin config JSON is invalid: {exc.msg}.") from exc
    if not isinstance(parsed, dict):
        raise ValidationError("Plugin config JSON must contain an object at the top level.")
    return parsed


def _validate_plugin_names(names: list[str], field: str, errors: list[str]) -> None:
    """Validate safe plugin and extension-pack names."""
    for name in names:
        if not SAFE_PLUGIN_NAME_PATTERN.fullmatch(name):
            errors.append(f"{field} contains unsafe plugin name {name!r}.")
        if name.casefold().startswith(UNSAFE_WRITE_PREFIXES):
            errors.append(f"{field} must not describe write or mutation actions.")


def _scan_safe_json_value(value: Any, field: str, errors: list[str]) -> None:
    """Reject secret-like, executable, remote, or path-like config values."""
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            key_folded = key_text.casefold()
            child = f"{field}.{key_text}"
            if any(keyword in key_folded for keyword in SECRET_KEYWORDS):
                errors.append(f"{child} must not contain secrets or credentials.")
            _scan_safe_json_value(item, child, errors)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _scan_safe_json_value(item, f"{field}[{index}]", errors)
        return
    if not isinstance(value, str):
        return

    text = value.strip()
    folded = text.casefold()
    redacted = redact_sensitive_text(text)
    if "://" in folded:
        errors.append(f"{field} must not contain remote URLs: {redacted!r}.")
    if ".." in text or "/" in text or "\\" in text:
        errors.append(f"{field} must not contain executable or filesystem paths.")
    if any(fragment in folded for fragment in UNSAFE_COMMAND_FRAGMENTS):
        errors.append(f"{field} must not contain shell or install commands.")
    if folded.startswith(("import ", "from ")) or any(
        fragment in folded for fragment in UNSAFE_IMPORT_FRAGMENTS
    ):
        errors.append(f"{field} must not contain import statements or import paths.")
    if any(keyword in folded for keyword in SECRET_KEYWORDS):
        errors.append(f"{field} must not contain secret-like values: {redacted!r}.")
