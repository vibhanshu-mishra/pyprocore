# Agent API

PyProcore includes a local agent tool registry for developers who want to build
AI assistants, workflow planners, or orchestration layers on top of existing
SDK capabilities.

The agent layer is included in the current stable `2.2.0` release.

The registry is metadata only. It does not execute tools, read `.env`, load
tokens, or call Procore. It describes the safe operations PyProcore can perform
today so another system can decide how to present or map those operations.

Phase 7B exposes this metadata through a local HTTP discovery API. The
server binds to `127.0.0.1` by default, requires no credentials, and still does
not execute tools.

Phase 7C adds OpenAPI and JSON Schema exports for agent frameworks, gateways,
workflow engines, documentation tools, and future MCP/Open Agent API adapters.
These exports are specification-only and do not require Procore credentials.

Phase 7D adds opt-in local run logs and replay. Run logs record sanitized
summaries of local discovery activity only. Replay verifies what happened; it
does not execute tools or call Procore.

Phase 7E adds a discovery-only MCP adapter. It maps the same local agent
registry into MCP-style tool, resource, prompt, and manifest documents. Tool
execution remains disabled, and no Procore credentials are required.

Phase 15A, Phase 15B, and Phase 15C expand MCP discovery with richer local
resources, prompt templates, kind filters, capability summaries,
stdio-friendly discovery payloads, explicit safety boundaries, contract
validation, local snapshots, compatibility reports, and static fixtures. See
[MCP Discovery](mcp.md). This remains metadata-only and does not execute tools,
plugins, Procore calls, or model calls.

Phase 7F adds a local deterministic agent eval harness. The evals check
registry safety, schema quality, OpenAPI completeness, MCP discovery, run-log
replay, redaction, and disabled-execution guarantees without calling Procore or
any AI/model APIs.

The current unreleased branch adds Phase 8A, Phase 8C, Phase 8D, Phase 8E,
Phase 8F, and Phase 8G registry metadata for
read-only Observations, Punch Items, Generic Tools, correspondence items,
Meetings, checklist-backed Inspections, Incidents, Directory users, Vendors,
Departments, Distribution Groups, Locations, financial/change-management
resources, contracts, invoices, payments, billing resources, schedules, tasks,
calendar items, coordination issues, forms, and action plans. This expands
discovery metadata only; tool execution remains disabled.

Phase 12 AI workflow examples are separate from agent execution. They prepare
local prompt/checklist/vector-manifest files for user-selected model stacks, but
they do not enable agent tool execution, do not call external AI/model APIs, and
do not change discovery-only MCP behavior.

Phase 13A, Phase 13B, Phase 13C, and Phase 13D golden evals complement the Phase 7 agent
eval command. The top-level `procore-sdk evals` commands check local
deterministic artifacts such as agent manifests, export rows, workflow packages,
async export manifests, async batch plans, plugin metadata/configs, safety
boundaries, baselines, regression reports, and saved model-response fixtures.
They do not replace `procore-sdk agent evals`, and they do not enable tool
execution or call model providers.

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
- MCP-style tool, resource, prompt, and manifest exports.
- An experimental local stdio adapter for MCP discovery.
- Local deterministic eval suites for agent metadata and safety checks.
- Unreleased Phase 8A, Phase 8C, Phase 8D, Phase 8E, Phase 8F, and Phase 8G metadata for Observations, Punch
  Items, Generic Tool correspondence, Meetings, Inspections, Incidents,
  Directory users, Vendors, Departments, Distribution Groups, Locations,
  financial/change-management resources, contracts, invoices, payments, and
  billing resources, schedules, tasks, calendar items, coordination issues,
  forms, and action plans.

## What It Is Not

- Not an execution-enabled MCP server.
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
procore-sdk agent mcp tools --pretty
procore-sdk agent mcp manifest --pretty
procore-sdk agent mcp stdio
procore-sdk agent evals list
procore-sdk agent evals run
procore-sdk agent evals run registry_safety
procore-sdk agent evals run --output agent-eval-output/agent-eval-results.json
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

Tool execution is not enabled. Calls to the `/call` endpoint return
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

## MCP Adapter

The MCP adapter is discovery-only in Phase 7E. It lets local MCP-compatible
clients inspect PyProcore tool metadata, but `tools/call` always returns a
disabled execution response.

```bash
procore-sdk agent mcp tools --pretty
procore-sdk agent mcp resources --pretty
procore-sdk agent mcp prompts --pretty
procore-sdk agent mcp manifest --pretty
```

Export the same metadata to local files:

```bash
python3 scripts/export_agent_mcp.py --output-dir agent-mcp-output --pretty
```

The experimental stdio adapter supports metadata methods such as `initialize`,
`tools/list`, `resources/list`, `resources/read`, `prompts/list`, and `ping`:

```bash
procore-sdk agent mcp stdio
```

It does not load `.env`, read token stores, execute registered tools, or call
Procore. A future phase may add guarded execution with explicit approval gates
and replay/eval integration.

## Agent Evals

Agent evals are local checks for agent-facing metadata and safety guarantees.
They do not load `.env`, read token stores, call Procore, execute tools, or call
AI/model APIs.

```bash
procore-sdk agent evals list
procore-sdk agent evals show registry_safety
procore-sdk agent evals run
procore-sdk agent evals run registry_safety
procore-sdk agent evals run --output agent-eval-output/agent-eval-results.json
procore-sdk agent evals run --fail-on-warning
```

The helper script writes both JSON and Markdown summaries:

```bash
python3 scripts/run_agent_evals.py --output-dir agent-eval-output
```

Built-in suites include `registry_safety`, `schema_quality`,
`openapi_completeness`, `mcp_discovery`, `run_replay_safety`,
`redaction_safety`, and `execution_disabled`.

## Python

```python
from pyprocore.agent import (
    build_agent_manifest,
    export_agent_openapi_json,
    export_agent_tool_schemas_json,
    export_mcp_manifest_json,
    export_mcp_tools_json,
    get_agent_tool,
    list_agent_tools,
    run_all_agent_eval_suites,
)

tools = list_agent_tools()
find_rfi = get_agent_tool("procore.find_rfi")
manifest = build_agent_manifest()
eval_results = run_all_agent_eval_suites()

print(len(tools))
print(find_rfi.input_schema)
print(all(result.passed for result in eval_results))
print(manifest.model_dump_json(indent=2))
print(export_agent_openapi_json(pretty=True))
print(export_agent_tool_schemas_json(pretty=True))
print(export_mcp_tools_json(pretty=True))
print(export_mcp_manifest_json(pretty=True))
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
- enable MCP tool execution

Phase 11A plugin manifests may describe future `agent_metadata` or
`mcp_metadata` capabilities, but those manifests are also metadata-only. They
do not install plugins, import plugin modules, execute plugin code, or enable
agent/MCP execution.

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
add approval-gated execution, richer MCP integration, replay/eval tooling, or
server integrations. Those are intentionally not included yet.
