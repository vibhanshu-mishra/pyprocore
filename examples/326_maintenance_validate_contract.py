"""Validate a bundled fake local compatibility contract."""

from pathlib import Path

from pyprocore.maintenance import validate_compatibility_contract_file

EXAMPLES_DIR = Path(__file__).resolve().parent
CONTRACT = EXAMPLES_DIR / "maintenance" / "contracts" / "new_pyprocore_compatibility_contract.json"


def main() -> None:
    """Print local contract validation status without remote access."""
    report = validate_compatibility_contract_file(CONTRACT)
    print(f"Valid: {report.valid}")
    print(f"Findings: {len(report.findings)}")


if __name__ == "__main__":
    main()
