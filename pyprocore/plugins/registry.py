"""Safe local plugin registry for metadata-only plugin manifests."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from pyprocore.core.exceptions import DuplicateMatchError, NotFoundError, ValidationError
from pyprocore.plugins.models import (
    PluginCapability,
    PluginManifest,
    PluginRegistration,
    PluginRegistryManifest,
)
from pyprocore.plugins.validation import (
    load_plugin_manifest_from_dict,
    validate_plugin_manifest,
)


class PluginRegistry:
    """In-memory registry for safe, metadata-only PyProcore plugin manifests."""

    def __init__(self, manifests: Iterable[PluginManifest] | None = None) -> None:
        """Initialize a plugin registry.

        Args:
            manifests: Optional manifests to validate and register immediately.
        """
        self._registrations: dict[str, PluginRegistration] = {}
        if manifests is not None:
            for manifest in manifests:
                self.register_plugin_manifest(manifest)

    def register_plugin_manifest(
        self,
        manifest: PluginManifest,
        *,
        source: str = "local",
        replace: bool = False,
    ) -> PluginRegistration:
        """Validate and register a plugin manifest.

        Args:
            manifest: Plugin manifest to register.
            source: Human-readable source label.
            replace: Whether to replace an existing manifest with the same name.

        Returns:
            The stored plugin registration.

        Raises:
            DuplicateMatchError: If the plugin name already exists and replacement is disabled.
            ValidationError: If the manifest fails Phase 11A safety validation.
        """
        result = validate_plugin_manifest(manifest)
        if not result.valid:
            raise ValidationError("; ".join(result.errors))
        if manifest.name in self._registrations and not replace:
            raise DuplicateMatchError(f"Plugin {manifest.name!r} is already registered.")
        registration = PluginRegistration(manifest=manifest, source=source)
        self._registrations[manifest.name] = registration
        return registration

    def register_plugin_manifest_data(
        self,
        data: Mapping[str, Any],
        *,
        source: str = "local",
        replace: bool = False,
    ) -> PluginRegistration:
        """Load, validate, and register plugin manifest dictionary data."""
        manifest = load_plugin_manifest_from_dict(data)
        return self.register_plugin_manifest(manifest, source=source, replace=replace)

    def unregister_plugin(self, name: str) -> PluginManifest:
        """Remove one plugin manifest from the registry.

        Args:
            name: Plugin name to remove.

        Returns:
            The removed plugin manifest.

        Raises:
            NotFoundError: If the plugin is not registered.
        """
        registration = self._registrations.pop(name, None)
        if registration is None:
            raise NotFoundError(f"Plugin {name!r} is not registered.")
        return registration.manifest

    def list_plugins(self) -> list[PluginManifest]:
        """Return registered plugin manifests sorted by name."""
        return [
            registration.manifest
            for _, registration in sorted(self._registrations.items(), key=lambda item: item[0])
        ]

    def get_plugin(self, name: str) -> PluginManifest:
        """Return one registered plugin manifest by name."""
        registration = self._registrations.get(name)
        if registration is None:
            raise NotFoundError(f"Plugin {name!r} is not registered.")
        return registration.manifest

    def find_plugins_by_capability(
        self,
        capability: PluginCapability | str,
    ) -> list[PluginManifest]:
        """Return registered plugin manifests declaring a capability."""
        target = PluginCapability(capability)
        return [manifest for manifest in self.list_plugins() if target in manifest.capabilities]

    def export_plugin_registry_manifest(self) -> PluginRegistryManifest:
        """Return a JSON-serializable registry manifest."""
        plugins = self.list_plugins()
        return PluginRegistryManifest(plugin_count=len(plugins), plugins=plugins)


def register_plugin_manifest(
    registry: PluginRegistry,
    manifest: PluginManifest,
    *,
    source: str = "local",
    replace: bool = False,
) -> PluginRegistration:
    """Register a plugin manifest in a provided registry."""
    return registry.register_plugin_manifest(manifest, source=source, replace=replace)


def unregister_plugin(registry: PluginRegistry, name: str) -> PluginManifest:
    """Remove a plugin manifest from a provided registry."""
    return registry.unregister_plugin(name)


def list_plugins(registry: PluginRegistry) -> list[PluginManifest]:
    """Return plugin manifests registered in a provided registry."""
    return registry.list_plugins()


def get_plugin(registry: PluginRegistry, name: str) -> PluginManifest:
    """Return one plugin manifest from a provided registry."""
    return registry.get_plugin(name)


def find_plugins_by_capability(
    registry: PluginRegistry,
    capability: PluginCapability | str,
) -> list[PluginManifest]:
    """Return plugin manifests with a matching capability from a provided registry."""
    return registry.find_plugins_by_capability(capability)


def export_plugin_registry_manifest(registry: PluginRegistry) -> PluginRegistryManifest:
    """Return a JSON-serializable export for a provided registry."""
    return registry.export_plugin_registry_manifest()
