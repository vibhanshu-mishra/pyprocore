"""Compare a bundled fake codebase with a fake local compatibility contract."""

from pathlib import Path

from pyprocore.maintenance import analyze_codebase_compatibility_with_contract

EXAMPLES_DIR = Path(__file__).resolve().parent
MAINTENANCE = EXAMPLES_DIR / "maintenance"


def main() -> None:
    """Print local usage compatibility counts without executing customer code."""
    report = analyze_codebase_compatibility_with_contract(
        MAINTENANCE / "customer_codebase",
        MAINTENANCE / "contracts" / "new_pyprocore_compatibility_contract.json",
    )
    print(f"Compatible usage: {len(report.compatible)}")
    print(f"Deprecated usage: {len(report.deprecated)}")
    print(f"Manual review: {len(report.unknown_manual_review)}")


if __name__ == "__main__":
    main()
