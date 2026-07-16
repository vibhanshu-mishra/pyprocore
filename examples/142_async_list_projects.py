"""List projects with AsyncProcore using local mock data.

The example reads PROCORE_COMPANY_ID when present, but it does not call Procore.
It demonstrates the shape of code you can use after configuring real OAuth.
"""

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
    """Run a mocked async project list."""
    company_id = int(os.getenv("PROCORE_COMPANY_ID", "123"))
    transport = MockAsyncTransport(
        [
            AsyncResponse(
                status_code=200,
                url=f"https://api.example.com/rest/v1.0/companies/{company_id}/projects",
                headers={"Content-Type": "application/json"},
                json_data=[{"id": 456, "name": "Placeholder Project"}],
                content=b"[]",
            )
        ]
    )
    client = AsyncProcore(
        token_manager=DemoTokenManager(),  # type: ignore[arg-type]
        transport=transport,
        retry_sleep_seconds=0,
    )
    projects = await client.projects.list(company_id)
    await client.close()

    print(f"Projects for placeholder company {company_id}:")
    for project in projects:
        print(f"- {project.id}: {project.name}")


if __name__ == "__main__":
    asyncio.run(main())
