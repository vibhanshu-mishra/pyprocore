"""List directory resources asynchronously with local mock data."""

from __future__ import annotations

import asyncio

from pyprocore import AsyncProcore, AsyncResponse, MockAsyncTransport


class DemoTokenManager:
    """Tiny token provider for local mock examples."""

    def get_access_token(self, force_refresh: bool = False) -> str:
        """Return a placeholder token."""
        return "PLACEHOLDER_ACCESS_TOKEN"


async def main() -> None:
    """Run the directory example without Procore access."""
    transport = MockAsyncTransport(
        [
            AsyncResponse(
                200, "https://api.example.com/users", json_data=[{"id": 1, "name": "Ava"}]
            ),
            AsyncResponse(
                200, "https://api.example.com/project-users", json_data=[{"id": 2, "name": "Sam"}]
            ),
            AsyncResponse(
                200, "https://api.example.com/vendors", json_data=[{"id": 3, "name": "Vendor Co"}]
            ),
            AsyncResponse(
                200, "https://api.example.com/departments", json_data=[{"id": 4, "name": "Field"}]
            ),
            AsyncResponse(
                200, "https://api.example.com/groups", json_data=[{"id": 5, "name": "Distribution"}]
            ),
            AsyncResponse(
                200, "https://api.example.com/locations", json_data=[{"id": 6, "name": "Level 1"}]
            ),
        ]
    )
    async with AsyncProcore(
        token_manager=DemoTokenManager(),  # type: ignore[arg-type]
        transport=transport,
        retry_sleep_seconds=0,
    ) as client:
        company_users = await client.list_company_users(12345)
        project_users = await client.list_project_users(12345, 67890)
        vendors = await client.list_vendors(12345)
        departments = await client.list_departments(12345)
        groups = await client.list_project_distribution_groups(12345, 67890)
        locations = await client.list_locations(12345, 67890)

    print("Async directory example completed with local mock data.")
    print(f"Company user: {company_users[0].name}")
    print(f"Project user: {project_users[0].name}")
    print(f"Vendor: {vendors[0].name}")
    print(f"Department: {departments[0].name}")
    print(f"Distribution group: {groups[0].name}")
    print(f"Location: {locations[0].name}")


if __name__ == "__main__":
    asyncio.run(main())
