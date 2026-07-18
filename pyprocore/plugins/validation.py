"""Validation helpers for metadata-only plugin manifests."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from pyprocore.plugins.models import (
    PLUGIN_SCHEMA_VERSION,
    PluginCapability,
    PluginManifest,
    PluginValidationResult,
)

SAFE_PLUGIN_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*(?:-[a-z0-9_]+)*$")
SAFE_VERSION_PATTERN = re.compile(r"^[0-9]+(?:\.[0-9]+){1,2}(?:[-+][A-Za-z0-9_.-]+)?$")
UNSAFE_ENTRY_POINT_PREFIXES = (
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
UNSAFE_ENTRY_POINT_WORDS = ("client_secret", "access_token", "refresh_token", "password")


def load_plugin_manifest_from_dict(data: Mapping[str, Any]) -> PluginManifest:
    """Load a plugin manifest from a local dictionary.

    Args:
        data: Local manifest data, usually parsed from JSON.

    Returns:
        A typed plugin manifest.

    Raises:
        pydantic.ValidationError: If the structure cannot be parsed.
    """
    return PluginManifest.model_validate(dict(data))


def validate_plugin_manifest_data(data: Mapping[str, Any]) -> PluginValidationResult:
    """Validate local dictionary data as a plugin manifest."""
    try:
        manifest = load_plugin_manifest_from_dict(data)
    except PydanticValidationError as exc:
        return PluginValidationResult(
            valid=False,
            errors=[f"Manifest structure is invalid: {exc}"],
        )
    return validate_plugin_manifest(manifest)


def validate_plugin_manifest(manifest: PluginManifest) -> PluginValidationResult:
    """Validate a typed plugin manifest for Phase 11A safety rules."""
    errors: list[str] = []
    warnings: list[str] = []

    if manifest.schema_version != PLUGIN_SCHEMA_VERSION:
        errors.append(
            "Unsupported plugin schema version "
            f"{manifest.schema_version!r}; expected {PLUGIN_SCHEMA_VERSION!r}."
        )
    if not SAFE_PLUGIN_NAME_PATTERN.fullmatch(manifest.name):
        errors.append(
            "Plugin name must be lowercase letters, numbers, underscores, or hyphens, "
            "start with a letter, and must not contain path characters."
        )
    if not SAFE_VERSION_PATTERN.fullmatch(manifest.version):
        errors.append("Plugin version must look like a semantic version, such as 1.0.0.")
    if not manifest.description.strip():
        errors.append("Plugin description is required.")
    if not manifest.capabilities:
        errors.append("At least one plugin capability is required.")

    for capability in manifest.capabilities:
        if capability not in PluginCapability:
            errors.append(f"Unsupported plugin capability: {capability}.")

    _validate_entry_points(manifest.entry_points, errors)

    if manifest.enabled_by_default:
        warnings.append(
            "Plugin is enabled_by_default, but Phase 11A still treats it as metadata only."
        )
    if (
        manifest.supports_agent_metadata
        and PluginCapability.AGENT_METADATA not in manifest.capabilities
    ):
        warnings.append("supports_agent_metadata is set without the agent_metadata capability.")

    return PluginValidationResult(
        valid=not errors,
        errors=errors,
        warnings=warnings,
        manifest=manifest if not errors else None,
    )


def _validate_entry_points(entry_points: Mapping[str, str], errors: list[str]) -> None:
    """Validate manifest entry-point labels without importing code."""
    for key, value in entry_points.items():
        key_text = key.casefold()
        value_text = value.casefold()
        if (
            "/" in key
            or "\\" in key
            or ".." in key
            or "/" in value
            or "\\" in value
            or ".." in value
        ):
            errors.append("Plugin entry points must not contain filesystem path characters.")
        if key_text.startswith(UNSAFE_ENTRY_POINT_PREFIXES) or value_text.startswith(
            UNSAFE_ENTRY_POINT_PREFIXES
        ):
            errors.append(
                "Plugin entry points must not describe create/update/delete/upload/approve/"
                "reject/submit/payment/write actions in Phase 11A."
            )
        if any(word in key_text or word in value_text for word in UNSAFE_ENTRY_POINT_WORDS):
            errors.append("Plugin entry points must not include secret-like field names.")
