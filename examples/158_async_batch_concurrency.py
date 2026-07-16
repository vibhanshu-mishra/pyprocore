"""Demonstrate async batch concurrency limits with mock data."""

from __future__ import annotations

import asyncio

from pyprocore import async_collect_multi_project_rfis


class TrackingAsyncClient:
    """Async client double that tracks concurrent calls."""

    def __init__(self) -> None:
        """Initialize counters."""
        self.active = 0
        self.max_active = 0

    async def list_rfis(
        self, company_id: int, project_id: int, **_: object
    ) -> list[dict[str, int]]:
        """Return placeholder RFIs after a tiny async pause."""
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        await asyncio.sleep(0.01)
        self.active -= 1
        return [{"id": project_id, "company_id": company_id}]


async def run() -> None:
    """Run the local concurrency example."""
    client = TrackingAsyncClient()
    await async_collect_multi_project_rfis(
        client,  # type: ignore[arg-type]
        company_id=12345,
        project_ids=[1, 2, 3, 4],
        max_concurrency=2,
    )
    print(f"Maximum concurrent calls: {client.max_active}")


if __name__ == "__main__":
    asyncio.run(run())
