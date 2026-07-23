"""Search PyProcore capability metadata without calling Procore.

This example is safe to run without credentials. It searches the local
metadata-only discovery registry for a beginner-friendly intent.
"""

from __future__ import annotations

from pyprocore.discovery import (
    discovery_route_result_to_markdown,
    search_discovery_capabilities,
)


def main() -> None:
    """Run a local discovery search."""
    query = "overdue rfis"
    print(f"Searching local PyProcore capability metadata for: {query!r}")
    result = search_discovery_capabilities(query, limit=5)
    print(discovery_route_result_to_markdown(result).rstrip())


if __name__ == "__main__":
    main()
