"""Suggest local metadata route candidates for a project question.

This example does not execute SDK service functions. It only asks the local
discovery router which PyProcore capability metadata best matches a question.
"""

from __future__ import annotations

from pyprocore.discovery import discovery_route_result_to_markdown, route_discovery_query


def main() -> None:
    """Run a local route suggestion example."""
    question = "download drawings for a project"
    print(f"Routing local metadata for: {question!r}")
    result = route_discovery_query(question, limit=3)
    print(discovery_route_result_to_markdown(result).rstrip())


if __name__ == "__main__":
    main()
