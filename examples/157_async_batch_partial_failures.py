"""Show async batch partial failure capture with a local mock client."""

from __future__ import annotations

import asyncio

from pyprocore import async_collect_multi_project_rfis


class DemoAsyncClient:
    """Async client double with one intentional project failure."""

    async def list_rfis(
        self, company_id: int, project_id: int, **_: object
    ) -> list[dict[str, object]]:
        """Return placeholder RFIs or raise a safe example error."""
        if project_id == 11111:
            raise RuntimeError("Example permission failure for project 11111")
        return [{"id": 1, "project_id": project_id, "company_id": company_id}]


async def run() -> None:
    """Run the local partial-failure example."""
    manifest = await async_collect_multi_project_rfis(
        DemoAsyncClient(),  # type: ignore[arg-type]
        company_id=12345,
        project_ids=[67890, 11111],
        continue_on_error=True,
    )
    print(f"Completed: {manifest.completed_count}")
    print(f"Failed: {manifest.failed_count}")


if __name__ == "__main__":
    asyncio.run(run())
