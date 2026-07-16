"""Inspect a PyProcore token store without printing token values."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from pyprocore.auth.token_store import inspect_token_store


def build_parser() -> argparse.ArgumentParser:
    """Build the command parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, help="Optional token-store path")
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    return parser


def main() -> int:
    """Run the token-store inspection script."""
    args = build_parser().parse_args()
    result = inspect_token_store(args.path)
    if args.json:
        print(json.dumps(result.model_dump(mode="json"), indent=2))
    else:
        print("PyProcore token-store inspection")
        print(f"Backend: {result.backend_type}")
        print(f"Path: {result.path or 'not applicable'}")
        print(f"Exists: {result.exists}")
        print(f"Readable: {result.readable}")
        print(f"Contains token: {result.contains_token}")
        print(f"Auth mode: {result.auth_mode or 'unknown'}")
        print(f"Token status: {result.token_status}")
        for warning in result.warnings:
            print(f"WARN: {warning}")
        for error in result.errors:
            print(f"FAIL: {error}")
    return 0 if not result.errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
