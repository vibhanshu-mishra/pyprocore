"""Show how async download concurrency limits work with mock responses."""

from __future__ import annotations

import asyncio
import tempfile
from typing import Any

from pyprocore import AsyncResponse, async_download_with_manifest


class TrackingTransport:
    """Mock transport that records peak concurrent requests."""

    def __init__(self) -> None:
        """Initialize counters."""
        self.active = 0
        self.max_active = 0

    async def request(self, **_: Any) -> AsyncResponse:
        """Return a small file response after a short async pause."""
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        await asyncio.sleep(0.01)
        self.active -= 1
        return AsyncResponse(
            status_code=200, url="https://download.example.com/file", content=b"ok"
        )

    async def close(self) -> None:
        """Close the mock transport."""
        return None


async def main() -> None:
    """Run a local concurrency-limit demonstration."""
    transport = TrackingTransport()
    records = [
        {"id": index, "name": f"file-{index}.txt", "url": f"https://download.example.com/{index}"}
        for index in range(1, 7)
    ]
    with tempfile.TemporaryDirectory() as temp_dir:
        manifest = await async_download_with_manifest(
            transport,
            records,
            temp_dir,
            max_concurrency=2,
        )

        print("Async concurrency demo completed with local mock data.")
        print(f"Files handled: {manifest.file_count}")
        print(f"Peak concurrent requests: {transport.max_active}")


if __name__ == "__main__":
    asyncio.run(main())
