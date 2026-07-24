"""Build a conservative local impact report without OAS comparison data."""

from pathlib import Path

from pyprocore.maintenance import analyze_codebase_api_impact

EXAMPLES_DIR = Path(__file__).resolve().parent
FAKE_CODEBASE = EXAMPLES_DIR / "maintenance" / "customer_codebase"


def main() -> None:
    """Show that missing OAS context produces unknown impact, not guesses."""
    report = analyze_codebase_api_impact(FAKE_CODEBASE)
    print(f"OAS comparison provided: {report.oas_comparison_provided}")
    print(f"Possible-impact findings: {len(report.findings)}")
    print("Human review is required; no customer files were changed.")


if __name__ == "__main__":
    main()
