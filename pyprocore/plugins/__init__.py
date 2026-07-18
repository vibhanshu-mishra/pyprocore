"""Metadata-only plugin architecture foundation for PyProcore.

Phase 11A plugin helpers validate and expose safe plugin manifests. They do not
install plugins, fetch remote registries, import arbitrary plugin modules, or
execute plugin code.
"""

from pyprocore.plugins.discovery import (
    builtin_plugin_manifests,
    discover_builtin_plugins,
    discover_installed_plugin_metadata,
    discover_local_plugin_manifests,
    discover_plugins,
    load_local_plugin_manifest_file,
)
from pyprocore.plugins.models import (
    PLUGIN_SCHEMA_VERSION,
    PluginCapability,
    PluginDiscoveryResult,
    PluginManifest,
    PluginManifestData,
    PluginMetadata,
    PluginRegistration,
    PluginRegistryManifest,
    PluginSafetyLevel,
    PluginValidationResult,
)
from pyprocore.plugins.registry import (
    PluginRegistry,
    export_plugin_registry_manifest,
    find_plugins_by_capability,
    get_plugin,
    list_plugins,
    register_plugin_manifest,
    unregister_plugin,
)
from pyprocore.plugins.validation import (
    load_plugin_manifest_from_dict,
    validate_plugin_manifest,
    validate_plugin_manifest_data,
)

__all__ = [
    "PLUGIN_SCHEMA_VERSION",
    "PluginCapability",
    "PluginDiscoveryResult",
    "PluginManifest",
    "PluginManifestData",
    "PluginMetadata",
    "PluginRegistration",
    "PluginRegistry",
    "PluginRegistryManifest",
    "PluginSafetyLevel",
    "PluginValidationResult",
    "builtin_plugin_manifests",
    "discover_builtin_plugins",
    "discover_installed_plugin_metadata",
    "discover_local_plugin_manifests",
    "discover_plugins",
    "export_plugin_registry_manifest",
    "find_plugins_by_capability",
    "get_plugin",
    "list_plugins",
    "load_local_plugin_manifest_file",
    "load_plugin_manifest_from_dict",
    "register_plugin_manifest",
    "unregister_plugin",
    "validate_plugin_manifest",
    "validate_plugin_manifest_data",
]
