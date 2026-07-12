# Agent API

PyProcore includes a local agent tool registry for developers who want to build
AI assistants, workflow planners, or orchestration layers on top of existing
SDK capabilities.

The registry is metadata only. It does not execute tools, start a server, expose
an MCP endpoint, read `.env`, load tokens, or call Procore. It describes the
safe operations PyProcore can perform today so another system can decide how to
present or map those operations.

## What It Provides

- Stable tool names such as `procore.find_rfi`.
- Beginner-friendly titles and descriptions.
- Input and output schema metadata.
- Safety metadata for read-only and local-file-output operations.
- Service and CLI command references.
- A JSON manifest for future agent integrations.

## What It Is Not

- Not an HTTP API.
- Not an MCP server.
- Not a tool execution runtime.
- Not a hosted agent.
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
```

These commands inspect local metadata only and do not require Procore
credentials.

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

This makes the registry useful for model-agnostic planning while keeping actual
execution under the caller's control.

## Future Path

The registry is the first step toward a future open agent API. Later phases may
add execution adapters, MCP-compatible surfaces, or server integrations. Those
are intentionally not included yet.
