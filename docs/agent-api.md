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

Phase 7C adds OpenAPI and JSON Schema exports for agent frameworks, gateways,
workflow engines, documentation tools, and future MCP/Open Agent API adapters.
These exports are specification-only and do not require Procore credentials.

Phase 7D adds opt-in local run logs and replay. Run logs record sanitized
summaries of local discovery activity only. Replay verifies what happened; it
does not execute tools or call Procore.

## What It Provides

- Stable tool names such as `procore.find_rfi`.
- Beginner-friendly titles and descriptions.
- Input and output schema metadata.
- Safety metadata for read-only and local-file-output operations.
- Service and CLI command references.
- A JSON manifest for future agent integrations.
- A local HTTP discovery API for reading the manifest and tool metadata.
- OpenAPI 3.1 JSON/YAML export for the local Agent API.
- JSON Schema export for agent models and registered tool inputs/outputs.
- Opt-in local run logs for discovery requests.
- Replay checks for local audit and future eval workflows.

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
procore-sdk agent openapi --pretty
procore-sdk agent schemas --pretty
procore-sdk agent openapi --output agent-openapi.json
procore-sdk agent serve --port 8765
procore-sdk agent serve --run-log-dir agent-runs
procore-sdk agent runs list --run-log-dir agent-runs
procore-sdk agent runs replay RUN_ID --run-log-dir agent-runs
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
| `GET` | `/agent/openapi.json` | OpenAPI document for the local Agent API |
| `GET` | `/agent/schemas` | JSON schemas for agent models and registered tools |
| `POST` | `/agent/tools/procore.find_rfi/call` | Disabled execution placeholder |

Tool execution is not enabled in Phase 7B/7C. Calls to the `/call` endpoint return
structured JSON with `tool_execution_disabled`.

## OpenAPI And JSON Schema Export

Export the OpenAPI document:

```bash
procore-sdk agent openapi --pretty --output agent-openapi.json
```

Export JSON schemas:

```bash
procore-sdk agent schemas --pretty --output agent-schemas.json
```

YAML output is available without adding a YAML dependency:

```bash
procore-sdk agent openapi --yaml --output agent-openapi.yaml
```

The schema export includes:

- Pydantic JSON Schema for `AgentManifest`, `AgentTool`, and
  `AgentToolRegistry`.
- A tool-list schema.
- Each registered tool's `input_schema` and `output_schema`.
- Safety metadata such as `requires_auth`, `calls_live_api`, and
  `produces_files`.

The helper script writes both JSON files:

```bash
python3 scripts/export_agent_openapi.py --output-dir agent-spec-output --pretty
```

## Run Logs And Replay

Run logging is local-only and opt-in:

```bash
procore-sdk agent serve --run-log-dir agent-runs
```

The server writes:

```text
agent-runs/
  RUN_ID/
    run.json
    events.jsonl
```

Inspect and replay runs:

```bash
procore-sdk agent runs list --run-log-dir agent-runs
procore-sdk agent runs show RUN_ID --run-log-dir agent-runs
procore-sdk agent runs replay RUN_ID --run-log-dir agent-runs
procore-sdk agent runs export RUN_ID --run-log-dir agent-runs --output-dir agent-run-bundles
```

Run logs do not include raw request headers, authorization values, token store
contents, `.env` values, or full signed URL query values. Replay validates route
shape, registered tool names, and disabled tool-call events without executing
anything.

## Python

```python
from pyprocore.agent import (
    build_agent_manifest,
    export_agent_openapi_json,
    export_agent_tool_schemas_json,
    get_agent_tool,
    list_agent_tools,
)

tools = list_agent_tools()
find_rfi = get_agent_tool("procore.find_rfi")
manifest = build_agent_manifest()

print(len(tools))
print(find_rfi.input_schema)
print(manifest.model_dump_json(indent=2))
print(export_agent_openapi_json(pretty=True))
print(export_agent_tool_schemas_json(pretty=True))
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

## Specification Safety

OpenAPI and schema exports are local metadata. They do not:

- load `.env`
- read token stores
- call the Procore API
- execute registered tools
- include access tokens, refresh tokens, client secrets, or authorization headers

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
add approval-gated execution, MCP-compatible adapters, replay/eval tooling, or
server integrations. Those are intentionally not included yet.
