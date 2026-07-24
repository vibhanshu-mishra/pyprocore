"""Compare two fake local OAS files and print an API drift report."""

from pathlib import Path

from pyprocore.maintenance import compare_oas_catalogs, drift_report_to_markdown

EXAMPLES_DIR = Path(__file__).resolve().parent


def main() -> None:
    """Build a local drift report without credentials or Procore access."""
    report = compare_oas_catalogs(
        EXAMPLES_DIR / "maintenance" / "old_fake_procore_oas.json",
        EXAMPLES_DIR / "maintenance" / "new_fake_procore_oas.json",
    )
    print(drift_report_to_markdown(report))


if __name__ == "__main__":
    main()
