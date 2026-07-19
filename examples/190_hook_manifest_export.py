"""Export the built-in hook registry manifest as JSON.

The manifest contains metadata only. It is safe to inspect and serialize because
it does not include callable objects or credentials.
"""

from __future__ import annotations

from pyprocore.plugins import builtin_hook_registry


def main() -> None:
    """Print the built-in hook registry manifest."""
    manifest = builtin_hook_registry().export_hook_registry_manifest()
    print(manifest.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
