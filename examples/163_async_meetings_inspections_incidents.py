"""List meetings, inspections, incidents, and incident configuration asynchronously."""

from __future__ import annotations

import asyncio

from pyprocore import AsyncProcore, AsyncResponse, MockAsyncTransport


class DemoTokenManager:
    """Tiny token provider for local mock examples."""

    def get_access_token(self, force_refresh: bool = False) -> str:
        """Return a placeholder token."""
        return "PLACEHOLDER_ACCESS_TOKEN"


async def main() -> None:
    """Run the operations example without Procore access."""
    transport = MockAsyncTransport(
        [
            AsyncResponse(
                status_code=200,
                url="https://api.example.com/rest/v1.0/meetings",
                headers={"Content-Type": "application/json"},
                json_data=[{"id": 301, "title": "OAC Meeting"}],
                content=b"[]",
            ),
            AsyncResponse(
                status_code=200,
                url="https://api.example.com/rest/v1.0/checklists",
                headers={"Content-Type": "application/json"},
                json_data=[{"id": 401, "title": "Safety Inspection"}],
                content=b"[]",
            ),
            AsyncResponse(
                status_code=200,
                url="https://api.example.com/rest/v1.0/incidents",
                headers={"Content-Type": "application/json"},
                json_data=[{"id": 501, "title": "Near Miss"}],
                content=b"[]",
            ),
            AsyncResponse(
                status_code=200,
                url="https://api.example.com/rest/v1.0/projects/67890/incident_configuration",
                headers={"Content-Type": "application/json"},
                json_data={"project_id": 67890, "enabled": True},
                content=b"{}",
            ),
        ]
    )
    async with AsyncProcore(
        token_manager=DemoTokenManager(),  # type: ignore[arg-type]
        transport=transport,
        retry_sleep_seconds=0,
    ) as client:
        meetings = await client.list_meetings(12345, 67890)
        inspections = await client.list_inspections(12345, 67890)
        incidents = await client.list_incidents(12345, 67890)
        configuration = await client.get_project_incident_configuration(12345, 67890)

    print("Async operations example completed with local mock data.")
    print(f"Meeting: {meetings[0].title}")
    print(f"Inspection: {inspections[0].title}")
    print(f"Incident: {incidents[0].title}")
    print(f"Incident tool enabled: {configuration.enabled}")


if __name__ == "__main__":
    asyncio.run(main())
