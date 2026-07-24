"""Preview local PR draft artifact paths without writing files."""

import tempfile
from pathlib import Path

from pyprocore.maintenance import build_pr_draft_pack, write_pr_draft_pack

EXAMPLES_DIR = Path(__file__).resolve().parent
FAKE_CODEBASE = EXAMPLES_DIR / "maintenance" / "customer_codebase"


def main() -> None:
    """Dry-run the nine-file PR draft pack in a temporary location."""
    pack = build_pr_draft_pack(FAKE_CODEBASE)
    with tempfile.TemporaryDirectory() as directory:
        output_dir = Path(directory) / "pr-draft"
        report = write_pr_draft_pack(pack, output_dir, dry_run=True)
        print(f"Planned artifacts: {len(report.planned_files)}")
        print(f"Output directory created: {output_dir.exists()}")


if __name__ == "__main__":
    main()
