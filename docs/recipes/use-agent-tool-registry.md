# Use The Agent Tool Registry

## What This Does

The agent tool registry lists PyProcore operations in a machine-readable format.
It helps you see which SDK functions are suitable for future assistants,
planners, or workflow orchestration tools.

The registry is local metadata only. It does not execute tools or call Procore.

## When To Use It

Use this recipe when you want to:

- inspect available agent-friendly PyProcore operations
- export a manifest for another local tool
- understand which operations are read-only or local-file-output only
- prototype an AI assistant without exposing credentials

## Before You Start

Install PyProcore in your environment:

```bash
python3 -m pip install pyprocore
```

No `.env`, OAuth token, company ID, or project ID is required for registry
inspection.

## Code

```python
from pathlib import Path

from pyprocore.agent import export_agent_manifest_json, get_agent_tool, list_agent_tools

tools = list_agent_tools()
print(f"Registered tools: {len(tools)}")

tool = get_agent_tool("procore.find_rfi")
print(tool.title)
print(tool.input_schema)

output_path = Path("exports/agent_manifest.json")
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(export_agent_manifest_json(pretty=True), encoding="utf-8")
print(f"Wrote {output_path}")
```

You can also use the CLI:

```bash
procore-sdk agent tools
procore-sdk agent tool procore.find_rfi
procore-sdk agent manifest --json
```

## Expected Output

You should see a list of registered tools or JSON metadata. The output should
mention tool names such as `procore.find_rfi`, whether a tool requires auth, and
whether it would call the live Procore API if executed by a separate runner.

## Common Issues

If a tool name is not found, check the exact name:

```bash
procore-sdk agent tools
```

If you expected this to call Procore, that is not what this layer does. The
registry is a description of available SDK operations. It does not execute them.

If you need live Procore data, use the regular SDK services or CLI commands with
valid OAuth configuration.
