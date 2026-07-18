"""Demonstrate read-only async project-management calls with mock data."""

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
    """List project-management records from mocked responses."""
    transport = MockAsyncTransport(
        [
            AsyncResponse(
                200, "https://api.example.test/schedule", json_data={"id": 1, "name": "Schedule"}
            ),
            AsyncResponse(
                200, "https://api.example.test/tasks", json_data=[{"id": 2, "name": "Task"}]
            ),
            AsyncResponse(
                200, "https://api.example.test/forms", json_data=[{"id": 3, "name": "Form"}]
            ),
        ]
    )
    client = AsyncProcore(
        settings=example_settings(),
        token_manager=ExampleTokenManager(),  # type: ignore[arg-type]
        transport=transport,
    )

    schedule = await client.get_project_schedule(12345, 67890)
    tasks = await client.list_tasks(12345, 67890)
    forms = await client.list_forms(12345, 67890)

    print(f"Schedule: {schedule.name}")
    print(f"Tasks: {len(tasks)}")
    print(f"Forms: {len(forms)}")
    print("No schedule imports, form submissions, or action-plan completions were performed.")


if __name__ == "__main__":
    asyncio.run(main())
