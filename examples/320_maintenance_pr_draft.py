"""Build a local PR draft from the bundled fake customer codebase."""

from pathlib import Path

from pyprocore.maintenance import build_pr_draft_pack

EXAMPLES_DIR = Path(__file__).resolve().parent
FAKE_CODEBASE = EXAMPLES_DIR / "maintenance" / "customer_codebase"


def main() -> None:
    """Print a conservative local PR draft summary without OAS comparison."""
    pack = build_pr_draft_pack(FAKE_CODEBASE)
    print(f"Draft title: {pack.title}")
    print(f"Detected files for review: {len(pack.impacted_files)}")
    print("No PR was opened and no customer files were modified.")


if __name__ == "__main__":
    main()
