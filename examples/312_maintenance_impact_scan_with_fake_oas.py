"""Compare fake local OAS files with a fake local customer codebase."""

from pathlib import Path

from pyprocore.maintenance import analyze_codebase_api_impact

EXAMPLES_DIR = Path(__file__).resolve().parent
MAINTENANCE_DIR = EXAMPLES_DIR / "maintenance"


def main() -> None:
    """Print conservative capability impact classifications."""
    report = analyze_codebase_api_impact(
        MAINTENANCE_DIR / "customer_codebase",
        MAINTENANCE_DIR / "old_fake_procore_oas.json",
        MAINTENANCE_DIR / "new_fake_procore_oas.json",
    )
    for finding in report.findings:
        print(f"{finding.capability_family}: {finding.classification}")
    print("This local report does not certify compatibility.")


if __name__ == "__main__":
    main()
