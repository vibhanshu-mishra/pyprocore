"""Export document metadata asynchronously with local mock data.

The mock response includes document file metadata only. No live Procore calls or
downloads are made by this example.
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from pyprocore import (
    AsyncProcore,
    AsyncResponse,
    MockAsyncTransport,
    async_export_documents,
)


class DemoTokenManager:
    """Tiny token provider for the local mock example."""

    def get_access_token(self, force_refresh: bool = False) -> str:
        """Return a placeholder token."""
        return "PLACEHOLDER_ACCESS_TOKEN"


async def main() -> None:
    """Run the local async document export example."""
    transport = MockAsyncTransport(
        [
            AsyncResponse(
                status_code=200,
                url="https://api.example.com/rest/v1.0/projects/456/documents",
                headers={"Content-Type": "application/json"},
                json_data=[
                    {
                        "files": [
                            {"id": 10, "name": "Mock Drawing.pdf"},
                            {"id": 11, "name": "Mock Specification.pdf"},
                        ]
                    }
                ],
                content=b"[]",
            )
        ]
    )
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "documents.jsonl"
        async with AsyncProcore(
            token_manager=DemoTokenManager(),  # type: ignore[arg-type]
            transport=transport,
            retry_sleep_seconds=0,
        ) as client:
            result = await async_export_documents(client, 123, 456, output_path)

        print("Async document metadata export completed with local mock data.")
        print(f"Records exported: {result.record_count}")
        print(f"Output file: {result.output_path}")


if __name__ == "__main__":
    asyncio.run(main())
