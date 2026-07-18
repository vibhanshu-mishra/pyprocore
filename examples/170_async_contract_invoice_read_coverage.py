"""Demonstrate read-only async contract and invoice calls with mock data."""

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
    """List contract and invoice records from mocked responses."""
    transport = MockAsyncTransport(
        [
            AsyncResponse(
                200, "https://api.example.test/contracts", json_data=[{"id": 1, "number": "PC-1"}]
            ),
            AsyncResponse(
                200,
                "https://api.example.test/requisitions",
                json_data=[{"id": 2, "number": "REQ-1"}],
            ),
            AsyncResponse(
                200,
                "https://api.example.test/billing_periods",
                json_data=[{"id": 3, "name": "July"}],
            ),
        ]
    )
    client = AsyncProcore(
        settings=example_settings(),
        token_manager=ExampleTokenManager(),  # type: ignore[arg-type]
        transport=transport,
    )

    contracts = await client.list_contracts(12345, 67890)
    subcontractor_invoices = await client.list_subcontractor_invoices(12345, 67890)
    billing_periods = await client.list_billing_periods(12345, 67890)

    print(f"Prime contracts: {len(contracts)}")
    print(f"Subcontractor invoices: {len(subcontractor_invoices)}")
    print(f"Billing periods: {len(billing_periods)}")
    print("No approval, submission, payment, or mutation actions were performed.")


if __name__ == "__main__":
    asyncio.run(main())
