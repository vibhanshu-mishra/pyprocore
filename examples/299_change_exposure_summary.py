"""Build a local change exposure summary from fake exported data.

This example uses deterministic local scoring and does not make live Procore
or external AI/model calls.
"""

from __future__ import annotations

from pathlib import Path

from pyprocore.analytics import analytics_result_to_markdown, run_change_exposure_recipe


def main() -> None:
    """Print a Markdown change exposure report."""
    data_path = Path(__file__).resolve().parent / "analytics" / "fake_changes.json"
    result = run_change_exposure_recipe(data_path)
    print(analytics_result_to_markdown(result))


if __name__ == "__main__":
    main()
