"""Print a local PyProcore production runbook summary."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from pyprocore.workflows.deployment import build_production_runbook_summary


def build_parser() -> argparse.ArgumentParser:
    """Build the command parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--auth-mode", default="client_credentials")
    return parser


def main() -> int:
    """Print the local runbook summary."""
    args = build_parser().parse_args()
    print("PyProcore production runbook summary")
    for item in build_production_runbook_summary(args.auth_mode):
        print(f"- {item}")
    print("No Procore API calls were made.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
