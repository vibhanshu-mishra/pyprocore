"""Search local PyProcore metadata plus a tiny fake OAS fixture.

This example uses examples/catalog/fake_procore_oas.json. It never fetches a
remote OAS file and never calls Procore.
"""

from __future__ import annotations

from pathlib import Path

from pyprocore.core.exceptions import ProcoreError
from pyprocore.discovery import (
    discovery_route_result_to_markdown,
    search_oas_catalog_capabilities,
)


def main() -> None:
    """Run a local OAS-backed discovery search."""
    fixture_path = Path(__file__).parent / "catalog" / "fake_procore_oas.json"
    query = "change orders"
    print(f"Searching local discovery metadata and fake OAS fixture for: {query!r}")
    try:
        result = search_oas_catalog_capabilities(fixture_path, query, limit=5)
    except ProcoreError as exc:
        print(f"Could not load the local OAS fixture: {exc}")
        return
    print(discovery_route_result_to_markdown(result).rstrip())


if __name__ == "__main__":
    main()
