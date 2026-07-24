"""Build a local RFI aging risk report from fake exported data.

This example reads examples/analytics/fake_rfis.json only. It does not call
Procore, does not require OAuth, and does not perform write actions.
"""

from __future__ import annotations

from pathlib import Path

from pyprocore.analytics import analytics_result_to_markdown, run_rfi_aging_recipe


def main() -> None:
    """Print a Markdown RFI aging report."""
    data_path = Path(__file__).resolve().parent / "analytics" / "fake_rfis.json"
    result = run_rfi_aging_recipe(data_path)
    print(analytics_result_to_markdown(result))


if __name__ == "__main__":
    main()
