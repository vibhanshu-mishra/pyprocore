"""Build a local submittal delay report from fake exported data.

This example reads examples/analytics/fake_submittals.json only and never
contacts Procore.
"""

from __future__ import annotations

from pathlib import Path

from pyprocore.analytics import analytics_result_to_markdown, run_submittal_delay_recipe


def main() -> None:
    """Print a Markdown submittal delay report."""
    data_path = Path(__file__).resolve().parent / "analytics" / "fake_submittals.json"
    result = run_submittal_delay_recipe(data_path)
    print(analytics_result_to_markdown(result))


if __name__ == "__main__":
    main()
