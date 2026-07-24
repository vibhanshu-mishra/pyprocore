"""Build a combined local project health report from fake exported data.

The report combines RFI aging, submittal delay, change exposure, and daily log
completeness. It is heuristic and review-oriented, not a guarantee.
"""

from __future__ import annotations

from pathlib import Path

from pyprocore.analytics import analytics_result_to_markdown, run_project_health_recipe


def main() -> None:
    """Print a Markdown combined project health report."""
    data_dir = Path(__file__).resolve().parent / "analytics"
    result = run_project_health_recipe(
        rfis_path=data_dir / "fake_rfis.json",
        submittals_path=data_dir / "fake_submittals.json",
        changes_path=data_dir / "fake_changes.json",
        daily_logs_path=data_dir / "fake_daily_logs.json",
        start_date="2026-06-01",
        end_date="2026-06-05",
    )
    print(analytics_result_to_markdown(result))


if __name__ == "__main__":
    main()
