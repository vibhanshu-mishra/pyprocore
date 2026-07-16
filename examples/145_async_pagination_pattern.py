"""Demonstrate async pagination with local mock Procore responses."""

from __future__ import annotations

import asyncio

from pyprocore import AsyncProcore, AsyncResponse, MockAsyncTransport


class DemoTokenManager:
    """Tiny token provider for the local mock example."""

    def get_access_token(self, force_refresh: bool = False) -> str:
        """Return a placeholder token."""
        return "PLACEHOLDER_ACCESS_TOKEN"


async def main() -> None:
    """Run a mocked paginated company list."""
    transport = MockAsyncTransport(
        [
            AsyncResponse(
                status_code=200,
                url="https://api.example.com/rest/v1.0/companies",
                headers={"Content-Type": "application/json", "X-Next-Page": "2"},
                json_data=[{"id": 1, "name": "Page One Company"}],
                content=b"[]",
            ),
            AsyncResponse(
                status_code=200,
                url="https://api.example.com/rest/v1.0/companies?page=2",
                headers={"Content-Type": "application/json"},
                json_data=[{"id": 2, "name": "Page Two Company"}],
                content=b"[]",
            ),
        ]
    )
    async with AsyncProcore(
        token_manager=DemoTokenManager(),  # type: ignore[arg-type]
        transport=transport,
        retry_sleep_seconds=0,
    ) as client:
        companies = await client.list_companies()

    print(f"Collected {len(companies)} companies from mocked paginated responses.")
    print("The SDK requested page 2 automatically.")


if __name__ == "__main__":
    asyncio.run(main())
