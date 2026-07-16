"""Export RFIs asynchronously to CSV with local mock data.

This example is safe for beginners: it uses placeholder IDs, a mock transport,
and a temporary output folder.
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from pyprocore import AsyncProcore, AsyncResponse, MockAsyncTransport, async_export_rfis


class DemoTokenManager:
    """Tiny token provider for the local mock example."""

    def get_access_token(self, force_refresh: bool = False) -> str:
        """Return a placeholder token."""
        return "PLACEHOLDER_ACCESS_TOKEN"


async def main() -> None:
    """Run the local async RFI export example."""
    transport = MockAsyncTransport(
        [
            AsyncResponse(
                status_code=200,
                url="https://api.example.com/rest/v1.1/projects/456/rfis",
                headers={"Content-Type": "application/json"},
                json_data=[
                    {"id": 1, "number": "15", "subject": "Mocked RFI"},
                    {"id": 2, "number": "16", "subject": "Second mocked RFI"},
                ],
                content=b"[]",
            )
        ]
    )
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "rfis.csv"
        async with AsyncProcore(
            token_manager=DemoTokenManager(),  # type: ignore[arg-type]
            transport=transport,
            retry_sleep_seconds=0,
        ) as client:
            result = await async_export_rfis(
                client,
                company_id=123,
                project_id=456,
                output_path=output_path,
                output_format="csv",
            )

        print("Async RFI CSV export completed with local mock data.")
        print(f"Records exported: {result.record_count}")
        print(f"Output file: {result.output_path}")


if __name__ == "__main__":
    asyncio.run(main())
