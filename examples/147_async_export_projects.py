"""Export projects asynchronously to JSONL with local mock data.

This example does not call Procore. It demonstrates the async export helper
shape using MockAsyncTransport and a temporary output folder.
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from pyprocore import (
    AsyncProcore,
    AsyncResponse,
    MockAsyncTransport,
    async_export_projects,
)


class DemoTokenManager:
    """Tiny token provider for the local mock example."""

    def get_access_token(self, force_refresh: bool = False) -> str:
        """Return a placeholder token."""
        return "PLACEHOLDER_ACCESS_TOKEN"


async def main() -> None:
    """Run the local async project export example."""
    transport = MockAsyncTransport(
        [
            AsyncResponse(
                status_code=200,
                url="https://api.example.com/rest/v1.0/companies/123/projects",
                headers={"Content-Type": "application/json"},
                json_data=[
                    {"id": 456, "name": "Placeholder Project"},
                    {"id": 789, "name": "Training Project"},
                ],
                content=b"[]",
            )
        ]
    )
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "projects.jsonl"
        async with AsyncProcore(
            token_manager=DemoTokenManager(),  # type: ignore[arg-type]
            transport=transport,
            retry_sleep_seconds=0,
        ) as client:
            result = await async_export_projects(client, 123, output_path)

        print("Async project export completed with local mock data.")
        print(f"Records exported: {result.record_count}")
        print(f"Output file: {result.output_path}")


if __name__ == "__main__":
    asyncio.run(main())
