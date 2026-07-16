"""Export multi-project RFI data asynchronously with a local mock client."""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from pyprocore import async_export_multi_project_rfis


class DemoAsyncClient:
    """Tiny async client double that never calls Procore."""

    async def list_rfis(
        self, company_id: int, project_id: int, **_: object
    ) -> list[dict[str, object]]:
        """Return placeholder RFIs."""
        return [{"id": project_id * 10, "number": f"RFI-{project_id}", "company_id": company_id}]


async def run() -> None:
    """Run the local mock export."""
    with tempfile.TemporaryDirectory() as temp_dir:
        manifest = await async_export_multi_project_rfis(
            DemoAsyncClient(),  # type: ignore[arg-type]
            company_id=12345,
            project_ids=[67890, 11111],
            output_dir=Path(temp_dir),
            output_format="jsonl",
        )
        print(f"Completed exports: {manifest.completed_count}")
        print(f"Output folder: {manifest.output_dir}")


if __name__ == "__main__":
    asyncio.run(run())
