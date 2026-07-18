"""Summarize Phase 11A plugin architecture foundation.

This example is safe for beginners because it only prints local package
capabilities. It does not require credentials.
"""

from pyprocore.plugins import discover_builtin_plugins


def main() -> None:
    """Print a compact Phase 11A plugin architecture summary."""
    discovery = discover_builtin_plugins()

    print("Phase 11A: Plugin Architecture Foundation")
    print(f"Built-in metadata manifests: {len(discovery.discovered)}")
    print("Capabilities are manifest metadata only.")
    print("Future phases may add controlled extension hooks.")
    print("No plugin code was executed.")


if __name__ == "__main__":
    main()
