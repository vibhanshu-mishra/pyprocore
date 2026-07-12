# Export Agent OpenAPI

## What This Does

Exports machine-readable OpenAPI and JSON Schema documents for the local
PyProcore Agent API.

The export describes the discovery endpoints and registered tool metadata. It
does not execute tools, read credentials, load tokens, or call Procore.

## When To Use It

Use this when you want to connect PyProcore metadata to an agent framework,
gateway, workflow engine, documentation tool, or future MCP/Open Agent API
adapter.

## Before You Start

No Procore credentials are required for this recipe.

You only need PyProcore installed in your local environment:

```bash
pip3 install pyprocore
```

If you are testing unreleased local changes from a checkout, use:

```bash
PYTHONPATH=. procore-sdk agent openapi --pretty
```

## Code

```python
from pathlib import Path

from pyprocore.agent import export_agent_openapi_json, export_agent_tool_schemas_json

output_dir = Path("agent-spec-output")
output_dir.mkdir(parents=True, exist_ok=True)

(output_dir / "agent-openapi.json").write_text(
    export_agent_openapi_json(pretty=True),
    encoding="utf-8",
)
(output_dir / "agent-schemas.json").write_text(
    export_agent_tool_schemas_json(pretty=True),
    encoding="utf-8",
)

print(f"Exported specs to {output_dir}")
```

You can do the same from the CLI:

```bash
procore-sdk agent openapi --pretty --output agent-spec-output/agent-openapi.json
procore-sdk agent schemas --pretty --output agent-spec-output/agent-schemas.json
```

Or use the helper script:

```bash
python3 scripts/export_agent_openapi.py --output-dir agent-spec-output --pretty
```

## Expected Output

You should see JSON files similar to:

```text
agent-spec-output/
  agent-openapi.json
  agent-schemas.json
```

The OpenAPI document includes `GET /agent/manifest`, `GET /agent/tools`, and the
disabled `POST /agent/tools/{tool_name}/call` endpoint.

## Common Issues

- If `procore-sdk` is not found, install PyProcore or activate your virtual
  environment.
- If local checkout changes do not appear, run with `PYTHONPATH=.`.
- These exports do not prove Procore authentication works. Use
  `procore-sdk doctor` for local auth diagnostics.
- Tool execution remains disabled. The `/call` endpoint is documented for
  future adapters and returns `tool_execution_disabled`.
