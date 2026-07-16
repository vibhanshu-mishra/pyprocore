"""Preview an async batch plan locally without credentials."""

from __future__ import annotations

from pathlib import Path

from pyprocore import explain_async_batch_plan


def main() -> None:
    """Print a local dry-run explanation for the sample config."""
    root = Path(__file__).resolve().parents[1]
    plan_path = root / "examples" / "configs" / "async_batch_dry_run.json"
    print(explain_async_batch_plan(plan_path))


if __name__ == "__main__":
    main()
