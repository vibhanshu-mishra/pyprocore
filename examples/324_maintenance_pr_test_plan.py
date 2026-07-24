"""Render the safe manual test plan from a local PR draft pack."""

from pathlib import Path

from pyprocore.maintenance import build_pr_draft_pack, pr_test_plan_to_markdown

EXAMPLES_DIR = Path(__file__).resolve().parent
FAKE_CODEBASE = EXAMPLES_DIR / "maintenance" / "customer_codebase"


def main() -> None:
    """Print a test plan that defaults to mocked or fixture data."""
    pack = build_pr_draft_pack(FAKE_CODEBASE)
    print(pr_test_plan_to_markdown(pack).rstrip())


if __name__ == "__main__":
    main()
