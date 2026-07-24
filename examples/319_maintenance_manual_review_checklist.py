"""Render the migration planner's local manual-review checklist."""

from pathlib import Path

from pyprocore.maintenance import (
    build_migration_patch_plan,
    manual_review_checklist_to_markdown,
)

EXAMPLES_DIR = Path(__file__).resolve().parent
FAKE_CODEBASE = EXAMPLES_DIR / "maintenance" / "customer_codebase"


def main() -> None:
    """Print the checklist without calling Procore or changing customer files."""
    plan = build_migration_patch_plan(FAKE_CODEBASE)
    print(manual_review_checklist_to_markdown(plan))


if __name__ == "__main__":
    main()
