"""Review a bundled fake codebase against fake local compatibility contracts."""

from pathlib import Path

from pyprocore.maintenance import build_migration_guide


def main() -> None:
    """Print codebase-specific review counts without changing fixture files."""
    root = Path(__file__).parent / "maintenance"
    guide = build_migration_guide(
        root / "contracts" / "old_pyprocore_compatibility_contract.json",
        root / "contracts" / "new_pyprocore_compatibility_contract.json",
        root / "customer_codebase",
    )
    impact = guide.codebase_impact
    print(f"Manual-review findings: {len(impact.unknown_manual_review) if impact else 0}")
    print("The fake codebase was scanned locally and was not modified.")


if __name__ == "__main__":
    main()
