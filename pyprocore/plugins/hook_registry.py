"""Explicit local registry for safe PyProcore plugin hooks."""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

from pyprocore.core.exceptions import DuplicateMatchError, NotFoundError, ValidationError
from pyprocore.plugins.hooks import (
    PluginHookCallable,
    PluginHookContext,
    PluginHookMetadata,
    PluginHookRegistration,
    PluginHookRegistryManifest,
    PluginHookResult,
    PluginHookType,
    redact_sensitive_text,
    sanitize_hook_value,
)

SAFE_HOOK_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*(?:-[a-z0-9_]+)*$")
UNSAFE_HOOK_NAME_PREFIXES = (
    "approve",
    "create",
    "delete",
    "mutate",
    "pay",
    "payment",
    "reject",
    "submit",
    "update",
    "upload",
    "write",
)


class PluginHookRegistry:
    """In-memory registry for trusted explicitly registered local hook callables."""

    def __init__(
        self,
        registrations: Iterable[PluginHookRegistration] | None = None,
    ) -> None:
        """Initialize an empty hook registry.

        Args:
            registrations: Optional existing registrations to validate and add.
        """
        self._registrations: dict[str, PluginHookRegistration] = {}
        if registrations is not None:
            for registration in registrations:
                self.register_hook(
                    registration.metadata,
                    registration.hook,
                    source=registration.source,
                )

    def register_hook(
        self,
        metadata: PluginHookMetadata,
        hook: PluginHookCallable,
        *,
        source: str = "local",
        replace: bool = False,
    ) -> PluginHookRegistration:
        """Register a trusted local hook callable explicitly.

        Args:
            metadata: JSON-serializable hook metadata.
            hook: Trusted in-process callable.
            source: Human-readable registration source.
            replace: Whether to replace an existing hook with the same name.

        Returns:
            Stored hook registration.

        Raises:
            DuplicateMatchError: If hook already exists and replacement is disabled.
            ValidationError: If metadata or callable is unsafe.
        """
        validate_hook_registration(metadata, hook)
        if metadata.hook_name in self._registrations and not replace:
            raise DuplicateMatchError(f"Hook {metadata.hook_name!r} is already registered.")
        registration = PluginHookRegistration(metadata=metadata, hook=hook, source=source)
        self._registrations[metadata.hook_name] = registration
        return registration

    def unregister_hook(self, hook_name: str) -> PluginHookMetadata:
        """Remove a hook registration and return its metadata."""
        registration = self._registrations.pop(hook_name, None)
        if registration is None:
            raise NotFoundError(f"Hook {hook_name!r} is not registered.")
        return registration.metadata

    def list_hooks(self) -> list[PluginHookMetadata]:
        """Return registered hook metadata sorted by hook name."""
        return [
            registration.metadata
            for _, registration in sorted(self._registrations.items(), key=lambda item: item[0])
        ]

    def get_hook(self, hook_name: str) -> PluginHookMetadata:
        """Return one hook's metadata."""
        return self._get_registration(hook_name).metadata

    def find_hooks_by_type(self, hook_type: PluginHookType | str) -> list[PluginHookMetadata]:
        """Return hook metadata matching one hook type."""
        target = PluginHookType(hook_type)
        return [metadata for metadata in self.list_hooks() if metadata.hook_type == target]

    def export_hook_registry_manifest(self) -> PluginHookRegistryManifest:
        """Return a JSON-serializable hook registry manifest."""
        hooks = self.list_hooks()
        return PluginHookRegistryManifest(hook_count=len(hooks), hooks=hooks)

    def run_hook(
        self,
        hook_name: str,
        payload: Any,
        *,
        context: PluginHookContext | None = None,
        options: dict[str, Any] | None = None,
    ) -> PluginHookResult:
        """Run one explicitly registered local hook and capture a safe result."""
        registration = self._get_registration(hook_name)
        hook_context = context or PluginHookContext(
            plugin_name=registration.metadata.plugin_name,
            hook_name=registration.metadata.hook_name,
            hook_type=registration.metadata.hook_type,
            options=options or {},
        )
        try:
            output = registration.hook(hook_context, sanitize_hook_value(payload))
        except Exception as exc:
            return PluginHookResult(
                hook_name=registration.metadata.hook_name,
                plugin_name=registration.metadata.plugin_name,
                hook_type=registration.metadata.hook_type,
                success=False,
                errors=[redact_sensitive_text(f"{type(exc).__name__}: {exc}")],
            )
        return PluginHookResult(
            hook_name=registration.metadata.hook_name,
            plugin_name=registration.metadata.plugin_name,
            hook_type=registration.metadata.hook_type,
            success=True,
            output=sanitize_hook_value(output),
        )

    def run_validator_hook(
        self,
        hook_name: str,
        payload: Any,
        *,
        options: dict[str, Any] | None = None,
    ) -> PluginHookResult:
        """Run a registered validator hook."""
        return self._run_typed_hook(hook_name, PluginHookType.VALIDATOR, payload, options=options)

    def run_formatter_hook(
        self,
        hook_name: str,
        payload: Any,
        *,
        options: dict[str, Any] | None = None,
    ) -> PluginHookResult:
        """Run a registered formatter hook."""
        return self._run_typed_hook(hook_name, PluginHookType.FORMATTER, payload, options=options)

    def run_record_transformer_hook(
        self,
        hook_name: str,
        payload: Any,
        *,
        options: dict[str, Any] | None = None,
    ) -> PluginHookResult:
        """Run a registered record-transformer hook."""
        return self._run_typed_hook(
            hook_name,
            PluginHookType.RECORD_TRANSFORMER,
            payload,
            options=options,
        )

    def run_exporter_hook(
        self,
        hook_name: str,
        payload: Any,
        *,
        options: dict[str, Any] | None = None,
    ) -> PluginHookResult:
        """Run a registered exporter hook."""
        return self._run_typed_hook(hook_name, PluginHookType.EXPORTER, payload, options=options)

    def _run_typed_hook(
        self,
        hook_name: str,
        expected_type: PluginHookType,
        payload: Any,
        *,
        options: dict[str, Any] | None = None,
    ) -> PluginHookResult:
        """Run a hook only if its registered type matches the expected type."""
        metadata = self.get_hook(hook_name)
        if metadata.hook_type != expected_type:
            raise ValidationError(
                f"Hook {hook_name!r} is {metadata.hook_type.value}, not {expected_type.value}."
            )
        return self.run_hook(hook_name, payload, options=options)

    def _get_registration(self, hook_name: str) -> PluginHookRegistration:
        """Return one stored hook registration."""
        registration = self._registrations.get(hook_name)
        if registration is None:
            raise NotFoundError(f"Hook {hook_name!r} is not registered.")
        return registration


def validate_hook_registration(
    metadata: PluginHookMetadata,
    hook: Any,
) -> None:
    """Validate hook metadata and callable safety boundaries."""
    errors: list[str] = []
    if not SAFE_HOOK_NAME_PATTERN.fullmatch(metadata.hook_name):
        errors.append(
            "Hook name must be lowercase letters, numbers, underscores, or hyphens "
            "and must not contain path characters."
        )
    if metadata.hook_name.casefold().startswith(UNSAFE_HOOK_NAME_PREFIXES):
        errors.append("Hook names must not describe write, upload, approval, or payment actions.")
    if not metadata.description.strip():
        errors.append("Hook description is required.")
    if not metadata.read_only:
        errors.append("Plugin hooks must be read-only in Phase 11B.")
    if not metadata.safe_by_default:
        errors.append("Plugin hooks must be safe_by_default in Phase 11B.")
    if not callable(hook):
        errors.append("Plugin hook must be a callable registered explicitly in-process.")
    if errors:
        raise ValidationError("; ".join(errors))


def register_hook(
    registry: PluginHookRegistry,
    metadata: PluginHookMetadata,
    hook: PluginHookCallable,
    *,
    source: str = "local",
    replace: bool = False,
) -> PluginHookRegistration:
    """Register a hook in a provided registry."""
    return registry.register_hook(metadata, hook, source=source, replace=replace)


def unregister_hook(registry: PluginHookRegistry, hook_name: str) -> PluginHookMetadata:
    """Unregister a hook from a provided registry."""
    return registry.unregister_hook(hook_name)


def list_hooks(registry: PluginHookRegistry) -> list[PluginHookMetadata]:
    """Return hooks registered in a provided registry."""
    return registry.list_hooks()


def get_hook(registry: PluginHookRegistry, hook_name: str) -> PluginHookMetadata:
    """Return one hook from a provided registry."""
    return registry.get_hook(hook_name)


def find_hooks_by_type(
    registry: PluginHookRegistry,
    hook_type: PluginHookType | str,
) -> list[PluginHookMetadata]:
    """Return hooks matching one type from a provided registry."""
    return registry.find_hooks_by_type(hook_type)


def export_hook_registry_manifest(
    registry: PluginHookRegistry,
) -> PluginHookRegistryManifest:
    """Return a JSON-serializable hook registry manifest."""
    return registry.export_hook_registry_manifest()


def run_validator_hook(
    registry: PluginHookRegistry,
    hook_name: str,
    payload: Any,
    *,
    options: dict[str, Any] | None = None,
) -> PluginHookResult:
    """Run a registered validator hook."""
    return registry.run_validator_hook(hook_name, payload, options=options)


def run_formatter_hook(
    registry: PluginHookRegistry,
    hook_name: str,
    payload: Any,
    *,
    options: dict[str, Any] | None = None,
) -> PluginHookResult:
    """Run a registered formatter hook."""
    return registry.run_formatter_hook(hook_name, payload, options=options)


def run_record_transformer_hook(
    registry: PluginHookRegistry,
    hook_name: str,
    payload: Any,
    *,
    options: dict[str, Any] | None = None,
) -> PluginHookResult:
    """Run a registered record-transformer hook."""
    return registry.run_record_transformer_hook(hook_name, payload, options=options)


def run_exporter_hook(
    registry: PluginHookRegistry,
    hook_name: str,
    payload: Any,
    *,
    options: dict[str, Any] | None = None,
) -> PluginHookResult:
    """Run a registered exporter hook."""
    return registry.run_exporter_hook(hook_name, payload, options=options)
