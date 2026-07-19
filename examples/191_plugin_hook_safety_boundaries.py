"""Show Phase 11B plugin hook safety boundaries.

Hooks are trusted local callables registered by your application code. Manifest
metadata alone is descriptive and cannot run code.
"""

from __future__ import annotations

from pyprocore.plugins import PluginHookMetadata, PluginHookType, validate_hook_registration


def main() -> None:
    """Print safety guidance for local plugin hooks."""
    metadata = PluginHookMetadata(
        hook_name="local_quality_check",
        plugin_name="local_examples",
        hook_type=PluginHookType.VALIDATOR,
        description="Example safe local validator metadata.",
    )
    validate_hook_registration(metadata, lambda _context, payload: payload)

    print("Phase 11B hook safety:")
    print("- register trusted callables explicitly in application code")
    print("- keep hook contexts free of tokens and client secrets")
    print("- use metadata manifests for discovery and review")
    print("- avoid network access, package installation, and Procore write actions")


if __name__ == "__main__":
    main()
