"""List and find observations and punch items with local async mock data."""

from __future__ import annotations

import asyncio

from pyprocore import AsyncProcore, AsyncResponse, MockAsyncTransport


class DemoTokenManager:
    """Tiny token provider for local mock examples."""

    def get_access_token(self, force_refresh: bool = False) -> str:
        """Return a placeholder token."""
        return "PLACEHOLDER_ACCESS_TOKEN"


async def main() -> None:
    """Run the observations and punch items example without Procore access."""
    transport = MockAsyncTransport(
        [
            AsyncResponse(
                status_code=200,
                url="https://api.example.com/rest/v1.0/observations/items",
                headers={"Content-Type": "application/json"},
                json_data=[{"id": 101, "number": "OBS-1", "title": "Door frame"}],
                content=b"[]",
            ),
            AsyncResponse(
                status_code=200,
                url="https://api.example.com/rest/v1.0/punch_items",
                headers={"Content-Type": "application/json"},
                json_data=[{"id": 201, "number": "P-1", "title": "Paint touch-up"}],
                content=b"[]",
            ),
        ]
    )
    async with AsyncProcore(
        token_manager=DemoTokenManager(),  # type: ignore[arg-type]
        transport=transport,
        retry_sleep_seconds=0,
    ) as client:
        observations = await client.list_observations(12345, 67890)
        punch_items = await client.list_punch_items(12345, 67890)

    print("Async field issue example completed with local mock data.")
    print(f"Observation: {observations[0].number} - {observations[0].title}")
    print(f"Punch item: {punch_items[0].number} - {punch_items[0].title}")


if __name__ == "__main__":
    asyncio.run(main())
