"""Check local token-store safety without printing token values."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from pyprocore.auth.token_store import inspect_token_store


def build_parser() -> argparse.ArgumentParser:
    """Build the command parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, help="Optional token-store path")
    return parser


def main() -> int:
    """Run local token-store safety checks."""
    args = build_parser().parse_args()
    result = inspect_token_store(args.path)
    print("PyProcore token-store safety check")
    if result.errors:
        for error in result.errors:
            print(f"FAIL: {error}")
    if result.warnings:
        for warning in result.warnings:
            print(f"WARN: {warning}")
    if not result.errors and not result.warnings:
        print("PASS: No token-store safety issues detected.")
    return 1 if result.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
