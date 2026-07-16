#!/usr/bin/env python3
"""Create a safe placeholder scheduled export plan JSON file."""

from __future__ import annotations

import argparse
from pathlib import Path

from pyprocore.workflows import sample_scheduled_export_plan_json


def main() -> int:
    """Write a sample scheduled export plan without requiring credentials."""
    parser = argparse.ArgumentParser(description="Create a scheduled export sample config.")
    parser.add_argument(
        "--auth-mode",
        choices=["authorization_code", "client_credentials"],
        default="client_credentials",
        help="Auth mode to include in the sample.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("examples/configs/scheduled_export_client_credentials.json"),
        help="Local JSON path to write.",
    )
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        sample_scheduled_export_plan_json(auth_mode=args.auth_mode),
        encoding="utf-8",
    )
    print(f"Sample scheduled export plan written to: {args.output}")
    print("Review and replace placeholder IDs before using it with real exports.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
