"""Render a Markdown migration patch plan from fake local fixtures."""

from pathlib import Path

from pyprocore.maintenance import (
    build_migration_patch_plan,
    migration_patch_plan_to_markdown,
)

EXAMPLES_DIR = Path(__file__).resolve().parent
MAINTENANCE_DIR = EXAMPLES_DIR / "maintenance"


def main() -> None:
    """Print suggested review actions and non-applied safe documentation diffs."""
    plan = build_migration_patch_plan(
        MAINTENANCE_DIR / "customer_codebase",
        MAINTENANCE_DIR / "old_fake_procore_oas.json",
        MAINTENANCE_DIR / "new_fake_procore_oas.json",
    )
    print(migration_patch_plan_to_markdown(plan))


if __name__ == "__main__":
    main()
