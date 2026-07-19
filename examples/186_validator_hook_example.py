"""Run the built-in required-fields validator hook.

The built-in hook validates local sample dictionaries only. It does not connect
to Procore or read your `.env` file.
"""

from __future__ import annotations

from pyprocore.plugins import builtin_hook_registry


def main() -> None:
    """Validate local sample records."""
    records = [
        {"id": 1, "name": "Sample RFI"},
        {"id": 2, "name": ""},
    ]
    result = builtin_hook_registry().run_validator_hook(
        "validate_required_fields",
        records,
        options={"required_fields": ["id", "name"]},
    )
    print("Validation complete.")
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
