"""Build a local migration plan using the bundled fake OAS comparison."""

from pathlib import Path

from pyprocore.maintenance import build_migration_patch_plan

EXAMPLES_DIR = Path(__file__).resolve().parent
MAINTENANCE_DIR = EXAMPLES_DIR / "maintenance"


def main() -> None:
    """Print suggestion categories from fake local inputs."""
    plan = build_migration_patch_plan(
        MAINTENANCE_DIR / "customer_codebase",
        MAINTENANCE_DIR / "old_fake_procore_oas.json",
        MAINTENANCE_DIR / "new_fake_procore_oas.json",
    )
    for category in sorted({suggestion.category for suggestion in plan.suggestions}):
        print(category)
    print("Human review is required.")


if __name__ == "__main__":
    main()
