"""Print or create a safe private PyProcore deployment folder layout."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from pyprocore.workflows.deployment import sample_private_folder_layout


def build_parser() -> argparse.ArgumentParser:
    """Build the command parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("./pyprocore-private-runtime"))
    parser.add_argument("--create", action="store_true", help="Actually create folders")
    return parser


def main() -> int:
    """Print or create a local folder layout."""
    args = build_parser().parse_args()
    print(sample_private_folder_layout(args.root))
    if not args.create:
        print("Dry run only. Re-run with --create to create these folders.")
        return 0

    for relative in (
        "config",
        "token-stores/sandbox",
        "token-stores/production",
        "plans",
        "exports/sandbox",
        "exports/production",
        "logs/sandbox",
        "logs/production",
    ):
        (args.root / relative).mkdir(parents=True, exist_ok=True)
    print(f"Created private deployment folders under: {args.root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
