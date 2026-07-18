"""Export mock async financial records to a temporary local JSONL file."""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from pyprocore import AsyncProcore, MockAsyncTransport
from pyprocore.core.async_transport import AsyncResponse
from pyprocore.core.config import ProcoreSettings
from pyprocore.workflows import async_export_change_events


class ExampleTokenManager:
    """Tiny token manager for local mock examples."""

    def get_access_token(self, force_refresh: bool = False) -> str:
        """Return a placeholder token."""
        return "placeholder-token"


async def main() -> None:
    """Write a local JSONL export from mocked change events."""
    settings = ProcoreSettings(
        client_id="placeholder-client-id",
        client_secret="placeholder-client-secret",
        redirect_uri="http://localhost/callback",
        login_url="https://login.procore.com",
        api_base="https://api.procore.com",
        company_id=12345,
    )
    transport = MockAsyncTransport(
        [
            AsyncResponse(
                200,
                "https://api.example.test/change_events",
                json_data=[{"id": 1, "number": "CE-1"}],
            )
        ]
    )
    client = AsyncProcore(settings=settings, token_manager=ExampleTokenManager(), transport=transport)  # type: ignore[arg-type]

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "change_events.jsonl"
        result = await async_export_change_events(client, 12345, 67890, output_path)
        print(f"Wrote {result.record_count} mock records to {result.output_path}")


if __name__ == "__main__":
    asyncio.run(main())
