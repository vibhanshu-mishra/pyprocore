"""Run the built-in select-fields record transformer hook.

Use this pattern when you want to trim local SDK results before exporting or
reviewing them. This example uses placeholder records only.
"""

from __future__ import annotations

from pyprocore.plugins import builtin_hook_registry


def main() -> None:
    """Transform local sample records."""
    records = [
        {"id": 1, "number": "15", "title": "Door hardware", "internal": "ignore"},
        {"id": 2, "number": "27", "title": "Concrete mix", "internal": "ignore"},
    ]
    result = builtin_hook_registry().run_record_transformer_hook(
        "transform_records_select_fields",
        records,
        options={"fields": ["id", "number", "title"]},
    )
    print("Transformed records:")
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
