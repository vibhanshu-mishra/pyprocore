"""Quickstart for the local-only async PyProcore client pattern.

This example uses MockAsyncTransport so it does not call Procore. Replace the
mock transport with the default transport only after configuring OAuth and
installing the optional async extra with `pip install pyprocore[async]`.
"""

from __future__ import annotations

import asyncio

from pyprocore import AsyncProcore, AsyncResponse, MockAsyncTransport


class DemoTokenManager:
    """Tiny token provider for the local mock example."""

    def get_access_token(self, force_refresh: bool = False) -> str:
        """Return a placeholder token."""
        return "PLACEHOLDER_ACCESS_TOKEN"


async def main() -> None:
    """Run the async quickstart against local mock data."""
    transport = MockAsyncTransport(
        [
            AsyncResponse(
                status_code=200,
                url="https://api.example.com/rest/v1.0/companies",
                headers={"Content-Type": "application/json"},
                json_data=[{"id": 123, "name": "Placeholder Company"}],
                content=b"[]",
            )
        ]
    )
    async with AsyncProcore(
        token_manager=DemoTokenManager(),  # type: ignore[arg-type]
        transport=transport,
        retry_sleep_seconds=0,
    ) as client:
        companies = await client.list_companies()

    print("Async client quickstart completed with local mock data.")
    for company in companies:
        print(f"- {company.id}: {company.name}")


if __name__ == "__main__":
    asyncio.run(main())
