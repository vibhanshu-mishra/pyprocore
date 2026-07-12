# Agent API

PyProcore includes a local agent tool registry for developers who want to build
AI assistants, workflow planners, or orchestration layers on top of existing
SDK capabilities.

The registry is metadata only. It does not execute tools, read `.env`, load
tokens, or call Procore. It describes the safe operations PyProcore can perform
today so another system can decide how to present or map those operations.

Phase 7B also exposes this metadata through a local HTTP discovery API. The
server binds to `127.0.0.1` by default, requires no credentials, and still does
not execute tools.

## What It Provides

- Stable tool names such as `procore.find_rfi`.
- Beginner-friendly titles and descriptions.
- Input and output schema metadata.
- Safety metadata for read-only and local-file-output operations.
- Service and CLI command references.
- A JSON manifest for future agent integrations.
- A local HTTP discovery API for reading the manifest and tool metadata.

## What It Is Not

- Not an MCP server.
- Not a tool execution runtime.
- Not a hosted agent.
- Not a public hosted API.
- Not a mutation layer for Procore data.

All registered tools are either read-only Procore lookups or local-file-output
workflows. The registry intentionally excludes update, delete, email, and other
destructive actions.

## CLI

```bash
procore-sdk agent manifest
procore-sdk agent manifest --json
procore-sdk agent tools
procore-sdk agent tool procore.find_rfi
procore-sdk agent serve --port 8765
```

These commands inspect or serve local metadata only and do not require Procore
credentials. Use public binding only when you intentionally want to expose the
local discovery API beyond your machine:

```bash
procore-sdk agent serve --host 0.0.0.0 --allow-public-bind
```

## Local HTTP API

Start the local server:

```bash
procore-sdk agent serve
```

Available endpoints:

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/` | Service metadata and links |
| `GET` | `/health` | Health check |
| `GET` | `/agent/manifest` | Full agent manifest |
| `GET` | `/agent/tools` | Registered tools |
| `GET` | `/agent/tools/procore.find_rfi` | One tool by name |
| `POST` | `/agent/tools/procore.find_rfi/call` | Disabled execution placeholder |

Tool execution is not enabled in Phase 7B. Calls to the `/call` endpoint return
structured JSON with `tool_execution_disabled`.

## Python

```python
from pyprocore.agent import build_agent_manifest, get_agent_tool, list_agent_tools

tools = list_agent_tools()
find_rfi = get_agent_tool("procore.find_rfi")
manifest = build_agent_manifest()

print(len(tools))
print(find_rfi.input_schema)
print(manifest.model_dump_json(indent=2))
```

## Manifest

The manifest includes:

- package name
- package version
- registry version
- generated timestamp
- tool count
- sorted tool metadata

The output is JSON serializable and safe to write to a local file:

```python
from pathlib import Path

from pyprocore.agent import export_agent_manifest_json

Path("exports/agent_manifest.json").write_text(
    export_agent_manifest_json(pretty=True),
    encoding="utf-8",
)
```

## Safety Model

Each tool declares whether it:

- requires authentication
- would call the live Procore API if executed by an external runner
- produces local files
- needs read-only Procore access
- needs local file read/write permissions

This makes the registry and local HTTP API useful for model-agnostic planning
while keeping actual execution under the caller's control.

## Future Path

The registry is the first step toward a future open agent API. Later phases may
add execution adapters, MCP-compatible surfaces, or server integrations. Those
are intentionally not included yet.
