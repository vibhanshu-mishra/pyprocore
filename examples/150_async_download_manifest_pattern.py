"""Demonstrate async download manifests with local mock file responses.

This pattern works when Procore resource payloads include direct download URLs.
The example never calls Procore and writes only to a temporary folder.
"""

from __future__ import annotations

import asyncio
import tempfile

from pyprocore import AsyncResponse, MockAsyncTransport, async_download_with_manifest


async def main() -> None:
    """Run the local async download manifest example."""
    transport = MockAsyncTransport(
        [
            AsyncResponse(
                status_code=200,
                url="https://download.example.com/mock-one.pdf",
                content=b"first file",
            ),
            AsyncResponse(
                status_code=200,
                url="https://download.example.com/mock-two.pdf",
                content=b"second file",
            ),
        ]
    )
    records = [
        {"id": 1, "name": "Mock One.pdf", "url": "https://download.example.com/mock-one.pdf"},
        {"id": 2, "name": "Mock Two.pdf", "url": "https://download.example.com/mock-two.pdf"},
    ]
    with tempfile.TemporaryDirectory() as temp_dir:
        manifest = await async_download_with_manifest(
            transport,
            records,
            temp_dir,
            resource_name="documents",
        )

        print("Async download manifest completed with local mock files.")
        print(f"Downloaded: {manifest.success_count}")
        print(f"Skipped: {manifest.skipped_count}")
        print(f"Failed: {manifest.failure_count}")


if __name__ == "__main__":
    asyncio.run(main())
