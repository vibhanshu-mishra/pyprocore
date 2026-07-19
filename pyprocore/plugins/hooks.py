"""Typed models for safe local plugin extension hooks.

Phase 11B hooks are explicit in-process callables. Metadata can be serialized
and shared freely, but callable registration is local and opt-in.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import Field, field_validator

from pyprocore.models.base import ProcoreModel

PluginHookCallable = Callable[["PluginHookContext", Any], Any]
"""Callable signature for explicitly registered local plugin hooks."""

SENSITIVE_KEYWORDS = (
    "access_token",
    "authorization",
    "bearer",
    "client_secret",
    "password",
    "refresh_token",
    "secret",
    "token",
)
SECRET_VALUE_PATTERN = re.compile(
    r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+|"
    r"(access_token|refresh_token|client_secret|authorization|password|secret)"
    r"([\"'\s:=]+)[^\"'\s,;}]+"
)


class PluginHookType(str, Enum):
    """Supported local read-only plugin hook categories."""

    VALIDATOR = "validator"
    EXPORTER = "exporter"
    FORMATTER = "formatter"
    REPORT = "report"
    WORKFLOW_HELPER = "workflow_helper"
    RECORD_TRANSFORMER = "record_transformer"


class PluginHookMetadata(ProcoreModel):
    """JSON-serializable metadata for a safe local plugin hook."""

    hook_name: str
    plugin_name: str
    hook_type: PluginHookType
    description: str
    input_kind: str = "records"
    output_kind: str = "json"
    supports_sync: bool = True
    supports_async: bool = False
    safe_by_default: bool = True
    read_only: bool = True
    notes: list[str] = Field(default_factory=list)


class PluginHookContext(ProcoreModel):
    """Sanitized context passed to explicitly registered local hooks.

    The context intentionally excludes Procore clients, tokens, client secrets,
    authorization headers, and refresh credentials.
    """

    plugin_name: str
    hook_name: str
    hook_type: PluginHookType
    run_id: str | None = None
    options: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("options", "metadata", mode="before")
    @classmethod
    def _sanitize_mapping(cls, value: Any) -> dict[str, Any]:
        """Return mapping values with sensitive entries redacted."""
        if value is None:
            return {}
        if not isinstance(value, Mapping):
            raise ValueError("Hook context options and metadata must be dictionaries.")
        sanitized = sanitize_hook_value(dict(value))
        if isinstance(sanitized, dict):
            return sanitized
        return {}


class PluginHookRegistration(ProcoreModel):
    """Registration for one trusted in-process plugin hook callable."""

    metadata: PluginHookMetadata
    hook: PluginHookCallable = Field(exclude=True)
    source: str = "local"
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PluginHookResult(ProcoreModel):
    """JSON-safe result returned by a plugin hook run."""

    hook_name: str
    plugin_name: str
    hook_type: PluginHookType
    success: bool
    output: Any = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PluginHookRegistryManifest(ProcoreModel):
    """JSON-serializable export of registered hook metadata."""

    schema_version: str = "1"
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    hook_count: int
    hooks: list[PluginHookMetadata]
    mode: str = "explicit_local_hooks"
    notes: list[str] = Field(
        default_factory=lambda: [
            "Hook metadata is descriptive.",
            "Hook callables run only after explicit in-process registration.",
            "No remote plugin loading, installation, or imports are performed.",
        ]
    )


def sanitize_hook_value(value: Any) -> Any:
    """Return a JSON-safe value with sensitive keys and text redacted."""
    if isinstance(value, Mapping):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            if _is_sensitive_key(key_text):
                sanitized[key_text] = "[REDACTED]"
            else:
                sanitized[key_text] = sanitize_hook_value(item)
        return sanitized
    if isinstance(value, list):
        return [sanitize_hook_value(item) for item in value]
    if isinstance(value, tuple):
        return [sanitize_hook_value(item) for item in value]
    if isinstance(value, set):
        return [sanitize_hook_value(item) for item in sorted(value, key=str)]
    if isinstance(value, str):
        return redact_sensitive_text(value)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    try:
        json.dumps(value, default=str)
    except TypeError:
        return redact_sensitive_text(repr(value))
    return value


def redact_sensitive_text(text: str) -> str:
    """Redact common secret patterns from hook outputs and errors."""

    def replacement(match: re.Match[str]) -> str:
        if match.group(1):
            return f"{match.group(1)}[REDACTED]"
        return f"{match.group(2)}{match.group(3)}[REDACTED]"

    return SECRET_VALUE_PATTERN.sub(replacement, text)


def _is_sensitive_key(key: str) -> bool:
    """Return whether a key name appears to contain secret material."""
    lowered = key.casefold()
    return any(keyword in lowered for keyword in SENSITIVE_KEYWORDS)
