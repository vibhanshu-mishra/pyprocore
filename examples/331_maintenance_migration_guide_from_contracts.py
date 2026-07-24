"""Compare bundled fake contracts and print local migration-guide changes."""

from pathlib import Path

from pyprocore.maintenance import build_migration_guide


def main() -> None:
    """Build a guide from fake local compatibility contracts."""
    root = Path(__file__).parent / "maintenance" / "contracts"
    guide = build_migration_guide(
        root / "old_pyprocore_compatibility_contract.json",
        root / "new_pyprocore_compatibility_contract.json",
    )
    print(f"From {guide.from_version} to {guide.to_version}")
    print(f"New capabilities: {len(guide.feature_additions)}")
    print(f"Deprecations: {len(guide.deprecations)}")


if __name__ == "__main__":
    main()
