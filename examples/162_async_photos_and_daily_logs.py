"""List photos and Daily Log entries with local async mock data."""

from __future__ import annotations

import asyncio

from pyprocore import AsyncProcore, AsyncResponse, MockAsyncTransport


class DemoTokenManager:
    """Tiny token provider for local mock examples."""

    def get_access_token(self, force_refresh: bool = False) -> str:
        """Return a placeholder token."""
        return "PLACEHOLDER_ACCESS_TOKEN"


async def main() -> None:
    """Run the photos and Daily Logs example without Procore access."""
    transport = MockAsyncTransport(
        [
            AsyncResponse(
                status_code=200,
                url="https://api.example.com/rest/v1.0/image_categories",
                headers={"Content-Type": "application/json"},
                json_data=[{"id": 11, "name": "Progress Photos"}],
                content=b"[]",
            ),
            AsyncResponse(
                status_code=200,
                url="https://api.example.com/rest/v1.0/images",
                headers={"Content-Type": "application/json"},
                json_data=[{"id": 12, "filename": "level-1.jpg"}],
                content=b"[]",
            ),
            AsyncResponse(
                status_code=200,
                url="https://api.example.com/rest/v1.0/projects/67890/manpower_logs",
                headers={"Content-Type": "application/json"},
                json_data=[{"id": 13, "comments": "Crew on site"}],
                content=b"[]",
            ),
        ]
    )
    async with AsyncProcore(
        token_manager=DemoTokenManager(),  # type: ignore[arg-type]
        transport=transport,
        retry_sleep_seconds=0,
    ) as client:
        albums = await client.list_photo_albums(12345, 67890)
        photos = await client.list_photos(12345, 67890)
        logs = await client.list_daily_logs(12345, 67890, "manpower")

    print("Async photos and Daily Logs example completed with local mock data.")
    print(f"Album: {albums[0].name}")
    print(f"Photo: {photos[0].filename}")
    print(f"Daily Log: {logs[0].comments}")


if __name__ == "__main__":
    asyncio.run(main())
