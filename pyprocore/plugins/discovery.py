"""Safe plugin discovery helpers.

Phase 11A discovery is manifest-first and local-only. It does not import plugin
modules, execute plugin code, install packages, fetch remote manifests, or call
the Procore API.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from pyprocore.plugins.builtin_hooks import builtin_hook_metadata
from pyprocore.plugins.hooks import PluginHookType
from pyprocore.plugins.models import (
    PluginCapability,
    PluginDiscoveryResult,
    PluginManifest,
    PluginSafetyLevel,
)
from pyprocore.plugins.validation import load_plugin_manifest_from_dict, validate_plugin_manifest


def builtin_plugin_manifests() -> list[PluginManifest]:
    """Return built-in metadata-only plugin manifests."""
    hook_metadata = builtin_hook_metadata()
    exporter_hooks = [hook for hook in hook_metadata if hook.hook_type == PluginHookType.EXPORTER]
    formatter_hooks = [hook for hook in hook_metadata if hook.hook_type == PluginHookType.FORMATTER]
    validator_hooks = [hook for hook in hook_metadata if hook.hook_type == PluginHookType.VALIDATOR]
    report_hooks = [hook for hook in hook_metadata if hook.hook_type == PluginHookType.REPORT]
    transformer_hooks = [
        hook for hook in hook_metadata if hook.hook_type == PluginHookType.RECORD_TRANSFORMER
    ]
    return [
        PluginManifest(
            name="csv_exporter_plugin",
            version="1.0.0",
            description="Metadata for future CSV exporter extension hooks.",
            author="PyProcore",
            capabilities=[PluginCapability.EXPORTER, PluginCapability.FORMATTER],
            requires_pyprocore=">=2.2.0",
            entry_points={"exporter": "pyprocore.workflows.exports"},
            tags=["csv", "export", "local"],
            safety_level=PluginSafetyLevel.METADATA_ONLY,
            supports_sync=True,
            supports_cli=True,
            hooks=exporter_hooks + formatter_hooks,
            notes=["Metadata only. Uses existing core SDK exports today."],
        ),
        PluginManifest(
            name="jsonl_exporter_plugin",
            version="1.0.0",
            description="Metadata for future JSONL exporter extension hooks.",
            author="PyProcore",
            capabilities=[PluginCapability.EXPORTER, PluginCapability.FORMATTER],
            requires_pyprocore=">=2.2.0",
            entry_points={"exporter": "pyprocore.workflows.exports"},
            tags=["jsonl", "export", "local"],
            safety_level=PluginSafetyLevel.METADATA_ONLY,
            supports_sync=True,
            supports_async=True,
            supports_cli=True,
            hooks=exporter_hooks + formatter_hooks + transformer_hooks,
            notes=["Metadata only. No plugin code is executed."],
        ),
        PluginManifest(
            name="async_batch_plugin",
            version="1.0.0",
            description="Metadata for future async batch extension hooks.",
            author="PyProcore",
            capabilities=[PluginCapability.WORKFLOW, PluginCapability.REPORT],
            requires_pyprocore=">=2.2.0",
            entry_points={"workflow": "pyprocore.workflows.async_batch"},
            tags=["async", "batch", "workflow"],
            safety_level=PluginSafetyLevel.METADATA_ONLY,
            supports_async=True,
            supports_cli=True,
            hooks=report_hooks,
            notes=["Read-only batch planning metadata for future extension points."],
        ),
        PluginManifest(
            name="ai_workflow_prompt_pack_plugin",
            version="1.0.0",
            description="Metadata for future local AI prompt-pack workflow extensions.",
            author="PyProcore",
            capabilities=[PluginCapability.WORKFLOW, PluginCapability.AGENT_METADATA],
            requires_pyprocore=">=2.2.0",
            entry_points={"workflow": "pyprocore.workflows.ai_exports"},
            tags=["ai", "prompt-pack", "local"],
            safety_level=PluginSafetyLevel.METADATA_ONLY,
            supports_sync=True,
            supports_agent_metadata=True,
            hooks=report_hooks,
            notes=["No model calls are made. Prompt-pack metadata remains local."],
        ),
        PluginManifest(
            name="enterprise_readiness_plugin",
            version="1.0.0",
            description="Metadata for future enterprise readiness validator extensions.",
            author="PyProcore",
            capabilities=[PluginCapability.VALIDATOR, PluginCapability.REPORT],
            requires_pyprocore=">=2.2.0",
            entry_points={"validator": "pyprocore.workflows.deployment"},
            tags=["enterprise", "readiness", "validation"],
            safety_level=PluginSafetyLevel.METADATA_ONLY,
            supports_cli=True,
            hooks=validator_hooks + report_hooks,
            notes=["Local metadata only. Does not inspect secrets or call Procore."],
        ),
    ]


def discover_builtin_plugins() -> PluginDiscoveryResult:
    """Discover built-in metadata-only plugin manifests."""
    discovered: list[PluginManifest] = []
    errors: list[str] = []
    for manifest in builtin_plugin_manifests():
        result = validate_plugin_manifest(manifest)
        if result.valid:
            discovered.append(manifest)
        else:
            errors.extend(result.errors)
    return PluginDiscoveryResult(discovered=discovered, errors=errors, source="built-in")


def discover_local_plugin_manifests(
    manifests: Iterable[Mapping[str, Any]],
) -> PluginDiscoveryResult:
    """Discover plugin manifests from local dictionaries without executing code."""
    discovered: list[PluginManifest] = []
    errors: list[str] = []
    warnings: list[str] = []
    for index, item in enumerate(manifests, start=1):
        try:
            manifest = load_plugin_manifest_from_dict(item)
        except Exception as exc:
            errors.append(f"Local manifest {index} could not be parsed: {exc}")
            continue
        result = validate_plugin_manifest(manifest)
        if result.valid:
            discovered.append(manifest)
            warnings.extend(result.warnings)
        else:
            errors.extend(f"{manifest.name}: {error}" for error in result.errors)
    return PluginDiscoveryResult(
        discovered=discovered,
        errors=errors,
        warnings=warnings,
        source="local-dict",
    )


def load_local_plugin_manifest_file(path: Path) -> PluginManifest:
    """Load one local JSON plugin manifest file without executing plugin code."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Plugin manifest file must contain a JSON object.")
    return load_plugin_manifest_from_dict(data)


def discover_plugins() -> PluginDiscoveryResult:
    """Discover safe built-in plugin manifests.

    Installed-package and remote discovery are intentionally future work because
    Phase 11A does not import plugin code, fetch manifests, or auto-install.
    """
    return discover_builtin_plugins()


def discover_installed_plugin_metadata() -> PluginDiscoveryResult:
    """Return a future-work discovery result without importing installed packages."""
    return PluginDiscoveryResult(
        discovered=[],
        warnings=[
            "Installed package plugin discovery is future work; Phase 11A avoids importing "
            "or executing third-party plugin code."
        ],
        source="installed-metadata",
    )
