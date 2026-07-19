"""Static plugin developer templates for safe local scaffolding.

Phase 11D templates are plain text only. Rendering a template never imports,
loads, installs, fetches, or executes plugin code.
"""

from __future__ import annotations

import json
from enum import Enum

from pyprocore.plugins.config import export_plugin_config_template
from pyprocore.plugins.extension_pack import export_extension_pack_template
from pyprocore.plugins.hooks import PluginHookMetadata, PluginHookType
from pyprocore.plugins.models import PluginCapability, PluginManifest, PluginSafetyLevel


class PluginTemplateKind(str, Enum):
    """Supported safe plugin scaffold template categories."""

    PLUGIN_MANIFEST = "plugin_manifest"
    PLUGIN_CONFIG = "plugin_config"
    EXTENSION_PACK = "extension_pack"
    HOOK_MANIFEST = "hook_manifest"
    README = "readme"
    CHANGELOG = "changelog"
    TESTS = "tests"
    DOCS = "docs"
    EXAMPLE = "example"
    FULL_PACK = "full_pack"


def render_plugin_template(name: str, *, description: str | None = None) -> str:
    """Render a safe placeholder plugin manifest JSON template.

    Args:
        name: Safe plugin metadata name.
        description: Optional human-readable description.

    Returns:
        Pretty JSON text for a metadata-only plugin manifest.
    """
    manifest = PluginManifest(
        name=name,
        version="0.1.0",
        description=description or "Metadata-only local PyProcore plugin template.",
        author="Your Name",
        capabilities=[PluginCapability.EXPORTER, PluginCapability.FORMATTER],
        requires_pyprocore=">=2.2.0",
        tags=["template", "metadata-only"],
        safety_level=PluginSafetyLevel.METADATA_ONLY,
        enabled_by_default=False,
        supports_sync=True,
        supports_async=False,
        supports_agent_metadata=False,
        supports_cli=False,
        notes=[
            "Template only. PyProcore does not load, install, import, or execute this file.",
            "Add trusted local code separately and register hooks explicitly in your application.",
        ],
    )
    return _json_text(manifest.model_dump(mode="json"))


def render_plugin_config_template(name: str) -> str:
    """Render a safe placeholder plugin config JSON template."""
    config = export_plugin_config_template()
    config.enabled_plugins = [name]
    config.disabled_plugins = []
    config.extension_packs = [f"{name}_pack"]
    config.notes = [
        "Template only. This config stores preferences and never executes hooks.",
        "Do not place credentials, tokens, import paths, or executable paths in this file.",
    ]
    return _json_text(config.model_dump(mode="json"))


def render_extension_pack_template(name: str, *, description: str | None = None) -> str:
    """Render a safe placeholder extension-pack JSON template."""
    extension_pack = export_extension_pack_template()
    extension_pack.name = f"{name}_pack"
    extension_pack.description = description or "Metadata-only local extension pack template."
    for item in extension_pack.included_plugins:
        item.plugin_name = name
    for hook in extension_pack.included_hooks:
        hook.plugin_name = name
    extension_pack.notes = [
        "Template only. Extension packs group metadata and do not execute code.",
        "No remote fetching, package installation, dynamic loading, or Procore calls occur.",
    ]
    return _json_text(extension_pack.model_dump(mode="json"))


def render_hook_manifest_template(name: str, *, description: str | None = None) -> str:
    """Render a safe placeholder hook manifest JSON template."""
    hooks = [
        PluginHookMetadata(
            hook_name=f"{name}_validate_records",
            plugin_name=name,
            hook_type=PluginHookType.VALIDATOR,
            description=description or "Template metadata for validating local records.",
            notes=[
                "Metadata only. This does not register or execute a callable.",
                "Trusted application code must register hooks explicitly in-process.",
            ],
        ),
        PluginHookMetadata(
            hook_name=f"{name}_format_summary",
            plugin_name=name,
            hook_type=PluginHookType.FORMATTER,
            description="Template metadata for formatting local summaries.",
        ),
    ]
    return _json_text(
        {
            "schema_version": "1",
            "plugin_name": name,
            "mode": "metadata_only",
            "hooks": [hook.model_dump(mode="json") for hook in hooks],
            "notes": [
                "Hook metadata is descriptive only.",
                "Generated files are not loaded or executed by PyProcore.",
            ],
        }
    )


def render_plugin_readme_template(name: str, *, description: str | None = None) -> str:
    """Render a beginner-friendly README template for a local plugin pack."""
    title = name.replace("_", " ").replace("-", " ").title()
    return "\n".join(
        [
            f"# {title}",
            "",
            description or "A local metadata-only PyProcore plugin template.",
            "",
            "## What This Is",
            "",
            "This folder contains local template files for plugin metadata, hook metadata, "
            "configuration preferences, and extension-pack metadata.",
            "",
            "## Safety Boundaries",
            "",
            "- Generated files are templates only.",
            "- PyProcore does not install this pack.",
            "- PyProcore does not fetch remote resources for this pack.",
            "- PyProcore does not auto-load modules from this pack.",
            "- PyProcore does not execute hooks from configuration files.",
            "- PyProcore does not call Procore or external model APIs while scaffolding.",
            "- Keep credentials, tokens, and Authorization headers out of these files.",
            "",
            "## Suggested Next Steps",
            "",
            "1. Edit the JSON metadata files with safe placeholder values.",
            "2. Validate them with the PyProcore plugin CLI.",
            "3. Register trusted local hooks explicitly in your own application code when needed.",
            "",
        ]
    )


def render_plugin_changelog_template() -> str:
    """Render a minimal changelog template for a local plugin pack."""
    return "\n".join(
        [
            "# Changelog",
            "",
            "## Unreleased",
            "",
            "- Initial local metadata template.",
            "",
        ]
    )


def render_plugin_test_template(name: str) -> str:
    """Render a static Python test template that performs metadata checks only."""
    return "\n".join(
        [
            '"""Metadata-only tests for the local plugin template."""',
            "",
            "from pathlib import Path",
            "import json",
            "",
            "",
            "def test_plugin_manifest_is_metadata_only() -> None:",
            '    """Check the generated manifest without executing plugin code."""',
            '    manifest_path = Path(__file__).parents[1] / "plugin_manifest.json"',
            '    data = json.loads(manifest_path.read_text(encoding="utf-8"))',
            f'    assert data["name"] == "{name}"',
            '    assert data["safety_level"] == "metadata_only"',
            '    assert data["enabled_by_default"] is False',
            "",
        ]
    )


def render_plugin_docs_template(name: str, *, description: str | None = None) -> str:
    """Render a docs page template for a local plugin pack."""
    title = name.replace("_", " ").replace("-", " ").title()
    return "\n".join(
        [
            f"# {title} Plugin Pack",
            "",
            "## Purpose",
            "",
            description or "Describe the local metadata-only plugin pack here.",
            "",
            "## Files",
            "",
            "- `plugin_manifest.json`: plugin metadata",
            "- `plugin_config.json`: local preference metadata",
            "- `extension_pack_manifest.json`: grouped extension metadata",
            "- `hook_manifest.json`: descriptive hook metadata",
            "",
            "## Safety Notes",
            "",
            "These files are not installed, fetched, imported, or executed by PyProcore.",
            "",
        ]
    )


def render_plugin_example_template(name: str) -> str:
    """Render a static Python usage example for explicit trusted registration."""
    return "\n".join(
        [
            '"""Local plugin metadata usage example.',
            "",
            "This example is intentionally not auto-loaded by PyProcore. Use it as a",
            "starting point for trusted in-process application code only.",
            '"""',
            "",
            "",
            "def describe_plugin_metadata() -> dict[str, str]:",
            '    """Return static metadata for documentation or tests."""',
            "    return {",
            f'        "plugin_name": "{name}",',
            '        "mode": "metadata_only",',
            '        "execution": "disabled_by_template",',
            "    }",
            "",
            "",
            'if __name__ == "__main__":',
            "    metadata = describe_plugin_metadata()",
            "    print(f\"Plugin template: {metadata['plugin_name']}\")",
            '    print("No plugin code was loaded or executed by PyProcore.")',
            "",
        ]
    )


def render_template(
    kind: PluginTemplateKind | str,
    name: str,
    *,
    description: str | None = None,
) -> str:
    """Render one safe scaffold template by kind."""
    template_kind = PluginTemplateKind(kind)
    if template_kind == PluginTemplateKind.PLUGIN_MANIFEST:
        return render_plugin_template(name, description=description)
    if template_kind == PluginTemplateKind.PLUGIN_CONFIG:
        return render_plugin_config_template(name)
    if template_kind == PluginTemplateKind.EXTENSION_PACK:
        return render_extension_pack_template(name, description=description)
    if template_kind == PluginTemplateKind.HOOK_MANIFEST:
        return render_hook_manifest_template(name, description=description)
    if template_kind == PluginTemplateKind.README:
        return render_plugin_readme_template(name, description=description)
    if template_kind == PluginTemplateKind.CHANGELOG:
        return render_plugin_changelog_template()
    if template_kind == PluginTemplateKind.TESTS:
        return render_plugin_test_template(name)
    if template_kind == PluginTemplateKind.DOCS:
        return render_plugin_docs_template(name, description=description)
    if template_kind == PluginTemplateKind.EXAMPLE:
        return render_plugin_example_template(name)
    raise ValueError(f"Unsupported scaffold template kind: {template_kind.value}")


def _json_text(data: object) -> str:
    """Return deterministic pretty JSON text."""
    return json.dumps(data, indent=2, sort_keys=True) + "\n"
