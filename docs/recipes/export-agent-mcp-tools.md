# Export Agent MCP Tools

## What This Does

This recipe exports PyProcore's agent tool registry as MCP-style JSON metadata.
The export is discovery-only: it describes tools, inputs, and safety metadata,
but it does not execute tools or call Procore.

## When To Use It

Use this when you want an MCP-compatible client, local assistant, or workflow
planner to inspect what PyProcore can do before any execution support exists.

## Before You Start

You do not need a `.env` file, OAuth token, company ID, or project ID for this
metadata export. The command reads PyProcore's static local registry only.

## Code

```python
from pathlib import Path

from pyprocore.agent import export_mcp_tools_json

output_path = Path("agent-mcp-output/mcp-tools.json")
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(export_mcp_tools_json(pretty=True), encoding="utf-8")

print(f"Wrote {output_path}")
```

You can also use the CLI:

```bash
procore-sdk agent mcp tools --pretty --output agent-mcp-output/mcp-tools.json
```

Or export all MCP metadata files:

```bash
python3 scripts/export_agent_mcp.py --output-dir agent-mcp-output --pretty
```

## Expected Output

You should see JSON tool definitions with names such as `procore.find_rfi`.
Each tool includes a description, `inputSchema`, and safety metadata including
`requires_auth`, `calls_live_api`, `produces_files`, and `execution_enabled`.

`execution_enabled` is always `false` in Phase 7E.

## Common Issues

- If the command is not found, install the package or run with `PYTHONPATH=.` in
  a local checkout.
- If an MCP client expects live execution, remind it that Phase 7E is
  discovery-only.
- If you do not see a specific endpoint, check `procore-sdk agent tools` to see
  the current registry.
