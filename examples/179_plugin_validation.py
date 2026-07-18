"""Validate local plugin manifest dictionaries.

This example shows both a valid manifest and an unsafe manifest that is rejected.
It never executes plugin code or calls external services.
"""

from pyprocore.plugins import validate_plugin_manifest_data


def main() -> None:
    """Validate safe and unsafe manifest dictionaries."""
    valid_manifest = {
        "name": "example_validator_plugin",
        "version": "1.0.0",
        "description": "Placeholder metadata for a future local validator.",
        "capabilities": ["validator"],
    }
    unsafe_manifest = {
        "name": "../unsafe",
        "version": "1.0.0",
        "description": "This should be rejected.",
        "capabilities": ["validator"],
        "entry_points": {"delete": "unsafe.delete_records"},
    }

    for label, manifest in [("valid", valid_manifest), ("unsafe", unsafe_manifest)]:
        result = validate_plugin_manifest_data(manifest)
        print(f"{label}: valid={result.valid}")
        for error in result.errors:
            print(f"  error: {error}")


if __name__ == "__main__":
    main()
