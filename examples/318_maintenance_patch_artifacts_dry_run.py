"""Preview migration patch artifact paths without writing any files."""

import tempfile
from pathlib import Path

from pyprocore.maintenance import (
    build_migration_patch_plan,
    write_migration_patch_artifacts,
)

EXAMPLES_DIR = Path(__file__).resolve().parent
MAINTENANCE_DIR = EXAMPLES_DIR / "maintenance"


def main() -> None:
    """Dry-run the fixed artifact set in a temporary output location."""
    plan = build_migration_patch_plan(
        MAINTENANCE_DIR / "customer_codebase",
        MAINTENANCE_DIR / "old_fake_procore_oas.json",
        MAINTENANCE_DIR / "new_fake_procore_oas.json",
    )
    with tempfile.TemporaryDirectory() as directory:
        output_dir = Path(directory) / "migration-review"
        report = write_migration_patch_artifacts(plan, output_dir, dry_run=True)
        print(f"Planned artifacts: {len(report.planned_files)}")
        print(f"Output directory created: {output_dir.exists()}")


if __name__ == "__main__":
    main()
