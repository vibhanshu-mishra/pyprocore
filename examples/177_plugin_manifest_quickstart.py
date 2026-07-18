"""Create and validate a safe metadata-only plugin manifest.

This example does not install plugins, import plugin code, call Procore, or call
external AI services. It only builds local manifest metadata.
"""

from pyprocore.plugins import PluginCapability, PluginManifest, validate_plugin_manifest


def main() -> None:
    """Build one example plugin manifest and print validation results."""
    manifest = PluginManifest(
        name="example_report_plugin",
        version="1.0.0",
        description="Placeholder metadata for a future local report plugin.",
        author="Your Name",
        capabilities=[PluginCapability.REPORT],
        requires_pyprocore=">=2.2.0",
        tags=["example", "report", "metadata-only"],
        notes=["No plugin code is executed in Phase 11A."],
    )
    result = validate_plugin_manifest(manifest)

    print("Plugin manifest quickstart")
    print(f"Plugin: {manifest.name} {manifest.version}")
    print(f"Valid: {result.valid}")
    print("Mode: metadata only; no Procore calls were made.")


if __name__ == "__main__":
    main()
