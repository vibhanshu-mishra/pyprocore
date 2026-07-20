"""List Project Tools with local mock data.

This example demonstrates the Phase 16A Project Tools service without making
live Procore API calls. Replace the fake client with the normal SDK client in a
real integration after configuring OAuth and project access.
"""

from __future__ import annotations

from pyprocore.services.project_tools import ProjectToolsService


class FakeClient:
    """Tiny fake client for a local-only Project Tools example."""

    def get_all(
        self, path: str, *, params: dict | None = None, headers: dict | None = None
    ) -> list:
        """Return local Project Tool metadata."""
        print(f"Mock GET {path}")
        print(f"Mock params: {params}")
        print("Mock headers include Procore-Company-Id, but no token is printed.")
        return [
            {"id": 1, "name": "RFIs", "slug": "rfis", "active": True},
            {"id": 2, "name": "Drawings", "slug": "drawings", "active": True},
        ]


def main() -> None:
    """Run the local Project Tools example."""
    service = ProjectToolsService(client=FakeClient())  # type: ignore[arg-type]
    tools = service.list_project_tools(12345, company_id=67890, active=True)

    print("Project Tools example completed with local mock data.")
    for tool in tools:
        print(f"- {tool.id}: {tool.name} ({tool.slug})")


if __name__ == "__main__":
    main()
