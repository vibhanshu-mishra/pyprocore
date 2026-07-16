# Async Client

Phase 10A adds an async client foundation in the current unreleased branch.
The published stable release remains `2.2.0`; this async work remains
branch-only until a future release is cut.

## What this does

`AsyncProcore` is an additive, read-oriented client for scalable workflows such
as multi-project reporting, large-company exports, and concurrent read patterns.
It does not replace the existing sync `Procore` client.

Initial async coverage includes:

- Companies
- Projects
- RFIs
- Submittals
- Documents
- Drawing areas and drawings
- Specification sections

No create, update, delete, approval, status-change, or write helpers are added
in Phase 10A.

## Optional async transport

The base PyProcore install does not require an async HTTP dependency. Local
tests and examples use `MockAsyncTransport`, which never calls Procore.

For real async HTTP calls, install the optional async extra:

```bash
python3 -m pip install "pyprocore[async]"
```

If `httpx` is not installed and a real async HTTP transport is requested,
PyProcore raises a clear configuration error explaining how to install the
optional extra.

## Local mock example

```python
import asyncio

from pyprocore import AsyncProcore, AsyncResponse, MockAsyncTransport


class DemoTokenManager:
    def get_access_token(self, force_refresh: bool = False) -> str:
        return "PLACEHOLDER_ACCESS_TOKEN"


async def main() -> None:
    transport = MockAsyncTransport(
        [
            AsyncResponse(
                status_code=200,
                url="https://api.example.com/rest/v1.0/companies",
                headers={"Content-Type": "application/json"},
                json_data=[{"id": 123, "name": "Placeholder Company"}],
                content=b"[]",
            )
        ]
    )
    async with AsyncProcore(
        token_manager=DemoTokenManager(),
        transport=transport,
        retry_sleep_seconds=0,
    ) as client:
        companies = await client.list_companies()
        print(companies[0].name)


asyncio.run(main())
```

## Real usage shape

After OAuth is configured and the optional async extra is installed, the same
client can use the real async HTTP transport:

```python
import asyncio

from pyprocore import AsyncProcore


async def main() -> None:
    async with AsyncProcore() as client:
        projects = await client.projects.list(company_id=123456)
        for project in projects:
            print(project.id, project.name)


asyncio.run(main())
```

## Safety boundaries

- Existing sync APIs remain backward compatible.
- Tests and examples do not call live Procore APIs.
- No external AI/model APIs are called.
- No required vector DB or AI dependencies are added.
- Agent tool execution remains disabled.
- MCP remains discovery-only.
- Agent evals remain local and deterministic.
