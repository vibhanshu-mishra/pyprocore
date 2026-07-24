"""Build a local PR draft using bundled fake old and new OAS files."""

from pathlib import Path

from pyprocore.maintenance import build_pr_draft_pack

EXAMPLES_DIR = Path(__file__).resolve().parent
MAINTENANCE_DIR = EXAMPLES_DIR / "maintenance"


def main() -> None:
    """Print local API drift and PR draft review counts."""
    pack = build_pr_draft_pack(
        MAINTENANCE_DIR / "customer_codebase",
        MAINTENANCE_DIR / "old_fake_procore_oas.json",
        MAINTENANCE_DIR / "new_fake_procore_oas.json",
    )
    print(f"Draft title: {pack.title}")
    print("OAS comparison provided: yes")
    print(f"Migration suggestions: {len(pack.migration_plan.suggestions)}")


if __name__ == "__main__":
    main()
