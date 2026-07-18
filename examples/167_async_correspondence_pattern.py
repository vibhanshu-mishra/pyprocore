"""Show the async Generic Tool correspondence pattern with mock data."""

from __future__ import annotations

import asyncio

from pyprocore import AsyncProcore, AsyncResponse, MockAsyncTransport


class DemoTokenManager:
    """Tiny token provider for local mock examples."""

    def get_access_token(self, force_refresh: bool = False) -> str:
        """Return a placeholder token."""
        return "PLACEHOLDER_ACCESS_TOKEN"


async def main() -> None:
    """Run the async correspondence example without Procore access."""
    transport = MockAsyncTransport(
        [
            AsyncResponse(
                200,
                "https://api.example.com/generic_tools",
                json_data=[{"id": 31, "name": "Notices"}],
            ),
            AsyncResponse(
                200,
                "https://api.example.com/generic_tool_items",
                json_data=[{"id": 32, "number": "N-1"}],
            ),
        ]
    )
    async with AsyncProcore(
        token_manager=DemoTokenManager(),  # type: ignore[arg-type]
        transport=transport,
        retry_sleep_seconds=0,
    ) as client:
        tools = await client.list_generic_tools(12345, 67890)
        correspondences = await client.list_correspondences(12345, 67890, tools[0].id or 31)

    print("Async correspondence example completed with local mock data.")
    print(f"Generic Tool: {tools[0].name}")
    print(f"Correspondence item: {correspondences[0].number}")


if __name__ == "__main__":
    asyncio.run(main())
