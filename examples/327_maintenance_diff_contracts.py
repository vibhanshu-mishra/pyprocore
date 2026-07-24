"""Compare two bundled fake local compatibility contracts."""

from pathlib import Path

from pyprocore.maintenance import diff_compatibility_contracts

EXAMPLES_DIR = Path(__file__).resolve().parent
CONTRACTS = EXAMPLES_DIR / "maintenance" / "contracts"


def main() -> None:
    """Print deterministic local compatibility changes."""
    report = diff_compatibility_contracts(
        CONTRACTS / "old_pyprocore_compatibility_contract.json",
        CONTRACTS / "new_pyprocore_compatibility_contract.json",
    )
    print(f"Added families: {', '.join(report.added_resource_families)}")
    print(f"Added CLI groups: {', '.join(report.added_cli_groups)}")
    print(f"Risk level: {report.risk_level}")


if __name__ == "__main__":
    main()
