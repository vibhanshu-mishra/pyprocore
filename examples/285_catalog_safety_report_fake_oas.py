"""Build a safety report from a tiny local fake Procore OAS catalog.

This example is metadata-only. It does not call Procore, fetch an OAS file,
generate executable tools, or enable write actions.
"""

from __future__ import annotations

from pathlib import Path

from pyprocore.catalog import (
    compare_catalog_to_pyprocore_supported_coverage,
    coverage_report_to_markdown,
    load_oas_catalog,
)
from pyprocore.core.exceptions import ProcoreError


def main() -> None:
    """Run the local OAS catalog safety report example."""
    fixture_path = Path(__file__).parent / "catalog" / "fake_procore_oas.json"
    print("Building a local-only safety report from the fake OAS fixture.")
    try:
        catalog = load_oas_catalog(fixture_path)
        report = compare_catalog_to_pyprocore_supported_coverage(catalog)
    except ProcoreError as exc:
        print(f"Could not build the local OAS safety report: {exc}")
        return
    print(coverage_report_to_markdown(report).rstrip())


if __name__ == "__main__":
    main()
