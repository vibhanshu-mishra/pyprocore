"""Build a coverage report from a tiny local fake Procore OAS catalog.

Use this example to see how PyProcore compares local OAS metadata against
known read-oriented SDK coverage areas without calling Procore.
"""

from __future__ import annotations

from pathlib import Path

from pyprocore.catalog import (
    compare_catalog_to_pyprocore_supported_coverage,
    coverage_report_to_json,
    load_oas_catalog,
)
from pyprocore.core.exceptions import ProcoreError


def main() -> None:
    """Run the local OAS catalog coverage report example."""
    fixture_path = Path(__file__).parent / "catalog" / "fake_procore_oas.json"
    print("Building a local-only coverage report from the fake OAS fixture.")
    try:
        catalog = load_oas_catalog(fixture_path)
        report = compare_catalog_to_pyprocore_supported_coverage(catalog)
    except ProcoreError as exc:
        print(f"Could not build the local OAS coverage report: {exc}")
        return
    print(coverage_report_to_json(report, pretty=True))


if __name__ == "__main__":
    main()
