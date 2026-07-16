"""Fetch RFIs and submittals with AsyncProcore using local mock data."""

from __future__ import annotations

import asyncio
import os

from pyprocore import AsyncProcore, AsyncResponse, MockAsyncTransport


class DemoTokenManager:
    """Tiny token provider for the local mock example."""

    def get_access_token(self, force_refresh: bool = False) -> str:
        """Return a placeholder token."""
        return "PLACEHOLDER_ACCESS_TOKEN"


async def main() -> None:
    """Run mocked async RFI and submittal calls."""
    company_id = int(os.getenv("PROCORE_COMPANY_ID", "123"))
    project_id = int(os.getenv("PROCORE_PROJECT_ID", "456"))
    transport = MockAsyncTransport(
        [
            AsyncResponse(
                status_code=200,
                url="https://api.example.com/rest/v1.1/projects/456/rfis",
                headers={"Content-Type": "application/json"},
                json_data=[{"id": 1001, "subject": "Placeholder RFI"}],
                content=b"[]",
            ),
            AsyncResponse(
                status_code=200,
                url="https://api.example.com/rest/v1.1/projects/456/submittals",
                headers={"Content-Type": "application/json"},
                json_data=[{"id": 2001, "title": "Placeholder Submittal"}],
                content=b"[]",
            ),
        ]
    )
    async with AsyncProcore(
        token_manager=DemoTokenManager(),  # type: ignore[arg-type]
        transport=transport,
        retry_sleep_seconds=0,
    ) as client:
        rfis = await client.rfis.list(company_id, project_id)
        submittals = await client.submittals.list(company_id, project_id)

    print(f"Mocked project {project_id} async summary:")
    print(f"- RFIs: {len(rfis)}")
    print(f"- Submittals: {len(submittals)}")


if __name__ == "__main__":
    asyncio.run(main())
