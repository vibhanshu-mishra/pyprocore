"""Run the built-in record summary formatter hook.

This formats local sample data into plain text. No Procore credentials or live
API access are required.
"""

from __future__ import annotations

from pyprocore.plugins import builtin_hook_registry


def main() -> None:
    """Format local sample records."""
    records = [
        {"id": 1, "number": "RFI-001", "title": "Door hardware"},
        {"id": 2, "number": "SUB-002", "title": "Concrete mix"},
    ]
    result = builtin_hook_registry().run_formatter_hook("format_records_as_summary", records)
    print("Formatter output:")
    print(result.output)


if __name__ == "__main__":
    main()
