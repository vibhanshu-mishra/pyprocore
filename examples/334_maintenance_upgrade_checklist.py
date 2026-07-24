"""Render an upgrade checklist from bundled fake compatibility contracts."""

from pathlib import Path

from pyprocore.maintenance import (
    build_migration_guide,
    upgrade_checklist_to_markdown,
)


def main() -> None:
    """Print a human-owned checklist without calling Procore or editing code."""
    root = Path(__file__).parent / "maintenance" / "contracts"
    guide = build_migration_guide(
        root / "old_pyprocore_compatibility_contract.json",
        root / "new_pyprocore_compatibility_contract.json",
    )
    print(upgrade_checklist_to_markdown(guide))


if __name__ == "__main__":
    main()
