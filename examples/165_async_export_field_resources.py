"""Export field resources asynchronously to local files with mock data."""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from pyprocore import (
    AsyncProcore,
    AsyncResponse,
    MockAsyncTransport,
    async_export_observations,
    async_export_punch_items,
)


class DemoTokenManager:
    """Tiny token provider for local mock examples."""

    def get_access_token(self, force_refresh: bool = False) -> str:
        """Return a placeholder token."""
        return "PLACEHOLDER_ACCESS_TOKEN"


async def main() -> None:
    """Run the async field export example without Procore access."""
    transport = MockAsyncTransport(
        [
            AsyncResponse(
                200,
                "https://api.example.com/observations",
                json_data=[{"id": 1, "number": "OBS-1"}],
            ),
            AsyncResponse(
                200, "https://api.example.com/punch_items", json_data=[{"id": 2, "number": "P-1"}]
            ),
        ]
    )
    async with AsyncProcore(
        token_manager=DemoTokenManager(),  # type: ignore[arg-type]
        transport=transport,
        retry_sleep_seconds=0,
    ) as client:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_root = Path(temp_dir)
            observations = await async_export_observations(
                client,
                12345,
                67890,
                output_root / "observations.jsonl",
            )
            punch_items = await async_export_punch_items(
                client,
                12345,
                67890,
                output_root / "punch_items.jsonl",
            )
            print("Async field export example completed with local mock data.")
            print(f"Observation rows: {observations.record_count}")
            print(f"Punch item rows: {punch_items.record_count}")


if __name__ == "__main__":
    asyncio.run(main())
