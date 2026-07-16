"""Print local-only PyProcore credential rotation guidance."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from pyprocore.auth.permissions import (
    build_credential_rotation_checklist,
    explain_credential_rotation,
    explain_sandbox_production_separation,
    explain_token_clearance,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the command parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--auth-mode",
        choices=["authorization_code", "client_credentials"],
        default="authorization_code",
    )
    return parser


def main() -> int:
    """Run the checklist script."""
    args = build_parser().parse_args()
    print("PyProcore credential rotation checklist")
    print(f"Auth mode: {args.auth_mode}")
    print()
    print(explain_credential_rotation(args.auth_mode))
    print()
    for item in build_credential_rotation_checklist(args.auth_mode):
        print(f"- {item}")
    print()
    print(explain_token_clearance(args.auth_mode))
    print(explain_sandbox_production_separation())
    print("No Procore API calls were made.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
