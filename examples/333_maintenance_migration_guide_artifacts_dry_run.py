"""Dry-run the fixed migration-guide artifact set without writing files."""

from pathlib import Path

from pyprocore.maintenance import (
    build_migration_guide,
    write_migration_guide_artifacts,
)


def main() -> None:
    """List planned artifact names using bundled fake contracts."""
    root = Path(__file__).parent / "maintenance" / "contracts"
    guide = build_migration_guide(
        root / "old_pyprocore_compatibility_contract.json",
        root / "new_pyprocore_compatibility_contract.json",
    )
    report = write_migration_guide_artifacts(
        guide,
        Path("exports") / "migration-guide",
        dry_run=True,
    )
    print("Dry-run only; no files were written:")
    for path in report.planned_files:
        print(f"- {path}")


if __name__ == "__main__":
    main()
