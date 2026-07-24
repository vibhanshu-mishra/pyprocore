"""Analyze read-only coverage gaps in a fake local OAS file."""

from pathlib import Path

from pyprocore.maintenance import (
    analyze_pyprocore_coverage_gaps,
    coverage_gap_report_to_markdown,
)

OAS_PATH = Path(__file__).resolve().parent / "maintenance" / "new_fake_procore_oas.json"


def main() -> None:
    """Print local coverage recommendations without calling Procore."""
    report = analyze_pyprocore_coverage_gaps(OAS_PATH)
    print(coverage_gap_report_to_markdown(report))


if __name__ == "__main__":
    main()
