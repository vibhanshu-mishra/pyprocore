"""Summarize a tiny local fake Procore OpenAPI/OAS catalog.

This example does not require Procore credentials. It only reads the local
examples/catalog/fake_procore_oas.json fixture and prints metadata counts.
"""

from __future__ import annotations

from pathlib import Path

from pyprocore.catalog import catalog_summary_to_markdown, load_oas_catalog
from pyprocore.core.exceptions import ProcoreError


def main() -> None:
    """Run the local OAS catalog summary example."""
    fixture_path = Path(__file__).parent / "catalog" / "fake_procore_oas.json"
    print(f"Reading local OAS fixture: {fixture_path}")
    try:
        catalog = load_oas_catalog(fixture_path)
    except ProcoreError as exc:
        print(f"Could not load the local OAS fixture: {exc}")
        return
    print(catalog_summary_to_markdown(catalog.summary()).rstrip())


if __name__ == "__main__":
    main()
