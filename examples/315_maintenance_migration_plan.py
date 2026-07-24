"""Build a local migration readiness plan without OAS comparison data."""

from pathlib import Path

from pyprocore.maintenance import build_migration_patch_plan

EXAMPLES_DIR = Path(__file__).resolve().parent
FAKE_CODEBASE = EXAMPLES_DIR / "maintenance" / "customer_codebase"


def main() -> None:
    """Print a general local migration-plan summary."""
    plan = build_migration_patch_plan(FAKE_CODEBASE)
    print(f"OAS comparison provided: {plan.impact_report.oas_comparison_provided}")
    print(f"Suggestions requiring review: {len(plan.suggestions)}")
    print("No customer files were modified and no patches were applied.")


if __name__ == "__main__":
    main()
