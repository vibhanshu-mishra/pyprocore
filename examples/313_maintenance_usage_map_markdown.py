"""Render a Markdown capability map from the fake local codebase."""

from pathlib import Path

from pyprocore.maintenance import (
    codebase_scan_report_to_markdown,
    scan_pyprocore_usage,
)

EXAMPLES_DIR = Path(__file__).resolve().parent
FAKE_CODEBASE = EXAMPLES_DIR / "maintenance" / "customer_codebase"


def main() -> None:
    """Print a Markdown usage map without calling Procore."""
    report = scan_pyprocore_usage(FAKE_CODEBASE)
    print(codebase_scan_report_to_markdown(report))


if __name__ == "__main__":
    main()
