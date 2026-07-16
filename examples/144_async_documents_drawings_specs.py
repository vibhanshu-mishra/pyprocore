"""Fetch documents, drawings, and specs with AsyncProcore using mock data."""

from __future__ import annotations

import asyncio
import os

from pyprocore import AsyncProcore, AsyncResponse, MockAsyncTransport


class DemoTokenManager:
    """Tiny token provider for the local mock example."""

    def get_access_token(self, force_refresh: bool = False) -> str:
        """Return a placeholder token."""
        return "PLACEHOLDER_ACCESS_TOKEN"


async def main() -> None:
    """Run mocked async document, drawing, and specification calls."""
    company_id = int(os.getenv("PROCORE_COMPANY_ID", "123"))
    project_id = int(os.getenv("PROCORE_PROJECT_ID", "456"))
    transport = MockAsyncTransport(
        [
            AsyncResponse(
                status_code=200,
                url="https://api.example.com/rest/v1.0/folders",
                headers={"Content-Type": "application/json"},
                json_data=[{"files": [{"id": 10, "name": "Placeholder Document"}]}],
                content=b"[]",
            ),
            AsyncResponse(
                status_code=200,
                url="https://api.example.com/rest/v1.0/projects/456/drawing_areas",
                headers={"Content-Type": "application/json"},
                json_data=[{"id": 20, "name": "Current Set"}],
                content=b"[]",
            ),
            AsyncResponse(
                status_code=200,
                url="https://api.example.com/rest/v1.0/drawing_areas/20/drawings",
                headers={"Content-Type": "application/json"},
                json_data=[{"id": 21, "title": "A-100"}],
                content=b"[]",
            ),
            AsyncResponse(
                status_code=200,
                url="https://api.example.com/rest/v2.1/companies/123/projects/456/specification_sections",
                headers={"Content-Type": "application/json"},
                json_data=[{"id": 30, "number": "01 00 00", "description": "General"}],
                content=b"[]",
            ),
        ]
    )
    async with AsyncProcore(
        token_manager=DemoTokenManager(),  # type: ignore[arg-type]
        transport=transport,
        retry_sleep_seconds=0,
    ) as client:
        documents = await client.documents.list(company_id, project_id)
        drawings = await client.drawings.list(company_id, project_id)
        specs = await client.specifications.list_sections(company_id, project_id)

    print("Mocked async project resources:")
    print(f"- Documents: {len(documents)}")
    print(f"- Drawings: {len(drawings)}")
    print(f"- Specification sections: {len(specs)}")


if __name__ == "__main__":
    asyncio.run(main())
