"""Build a non-executing intake plan from a local fake configuration."""

from pathlib import Path

from pyprocore.intake import (
    build_intake_sync_plan,
    load_intake_sync_config,
    summarize_intake_sync_plan,
)

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    """Print a local plan without credentials, writes, or Procore calls."""
    config = load_intake_sync_config(ROOT / "examples/intake/intake_config.json")
    print(summarize_intake_sync_plan(build_intake_sync_plan(config)))


if __name__ == "__main__":
    main()
