"""Render the human-review checklist from a local PR draft pack."""

from pathlib import Path

from pyprocore.maintenance import (
    build_pr_draft_pack,
    pr_review_checklist_to_markdown,
)

EXAMPLES_DIR = Path(__file__).resolve().parent
FAKE_CODEBASE = EXAMPLES_DIR / "maintenance" / "customer_codebase"


def main() -> None:
    """Print the local PR draft review checklist."""
    pack = build_pr_draft_pack(FAKE_CODEBASE)
    print(pr_review_checklist_to_markdown(pack).rstrip())


if __name__ == "__main__":
    main()
