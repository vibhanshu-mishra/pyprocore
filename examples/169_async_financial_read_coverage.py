"""Demonstrate read-only async financial resource calls with mock data.

This example does not call Procore. Replace the mock transport with normal
credentials only after confirming project and company access.
"""

from __future__ import annotations

import asyncio

from pyprocore import AsyncProcore, MockAsyncTransport
from pyprocore.core.async_transport import AsyncResponse
from pyprocore.core.config import ProcoreSettings


class ExampleTokenManager:
    """Tiny token manager for local mock examples."""

    def get_access_token(self, force_refresh: bool = False) -> str:
        """Return a placeholder token."""
        return "placeholder-token"


def example_settings() -> ProcoreSettings:
    """Return placeholder SDK settings."""
    return ProcoreSettings(
        client_id="placeholder-client-id",
        client_secret="placeholder-client-secret",
        redirect_uri="http://localhost/callback",
        login_url="https://login.procore.com",
        api_base="https://api.procore.com",
        company_id=12345,
    )


async def main() -> None:
    """List async financial resources from mocked responses."""
    transport = MockAsyncTransport(
        [
            AsyncResponse(
                200,
                "https://api.example.test/change_events",
                json_data=[{"id": 1, "number": "CE-1"}],
            ),
            AsyncResponse(
                200,
                "https://api.example.test/direct_costs",
                json_data=[{"id": 2, "number": "DC-1"}],
            ),
            AsyncResponse(
                200,
                "https://api.example.test/budget_views",
                json_data=[{"id": 3, "name": "Forecast"}],
            ),
        ]
    )
    client = AsyncProcore(
        settings=example_settings(),
        token_manager=ExampleTokenManager(),  # type: ignore[arg-type]
        transport=transport,
    )

    change_events = await client.list_change_events(12345, 67890)
    direct_costs = await client.list_direct_costs(12345, 67890)
    budget_views = await client.list_budget_views(12345, 67890)

    print(f"Change events: {len(change_events)}")
    print(f"Direct costs: {len(direct_costs)}")
    print(f"Budget views: {len(budget_views)}")
    print("Read-only mock example complete. No Procore API calls were made.")


if __name__ == "__main__":
    asyncio.run(main())
