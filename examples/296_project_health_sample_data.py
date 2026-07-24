"""Write fake local analytics sample data for project health recipes.

This script does not call Procore and does not require credentials. It writes
small fake JSON files that can be used with the analytics examples.
"""

from __future__ import annotations

from pathlib import Path

from pyprocore.analytics import write_sample_analytics_data


def main() -> None:
    """Write sample analytics data into examples/analytics/generated."""
    output_dir = Path(__file__).resolve().parent / "analytics" / "generated"
    paths = write_sample_analytics_data(output_dir)
    print("Wrote fake local analytics sample data:")
    for path in paths:
        print(f"- {path}")
    print("No Procore API calls were made.")


if __name__ == "__main__":
    main()
