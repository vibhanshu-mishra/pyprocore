# Run The Local Agent API Server

## What This Does

The local agent API server exposes PyProcore's agent tool registry over HTTP.
It lets local agents, workflow engines, and future adapters discover PyProcore
capabilities without importing Python code directly.

It is discovery only. It does not execute tools, call Procore, read `.env`, or
require OAuth credentials.

## When To Use It

Use this recipe when you want a local process to inspect PyProcore tools through
HTTP instead of Python imports.

## Before You Start

Install PyProcore:

```bash
python3 -m pip install pyprocore
```

No Procore credentials are required for the discovery server.

## Code

Start the local server:

```bash
procore-sdk agent serve --port 8765
```

Check health:

```bash
curl http://127.0.0.1:8765/health
```

Read the manifest:

```bash
curl http://127.0.0.1:8765/agent/manifest
```

Read one tool:

```bash
curl http://127.0.0.1:8765/agent/tools/procore.find_rfi
```

## Expected Output

The health endpoint returns JSON similar to:

```json
{
  "service": "pyprocore-agent-api",
  "status": "ok",
  "version": "2.1.0"
}
```

The `/agent/tools` endpoint returns a JSON list of tool metadata. The `/call`
endpoint intentionally returns `tool_execution_disabled` because Phase 7B does
not execute tools.

## Common Issues

If the port is already in use, choose another local port:

```bash
procore-sdk agent serve --port 8877
```

The server binds to `127.0.0.1` by default. Do not bind to `0.0.0.0` unless you
intentionally want other machines on your network to reach it:

```bash
procore-sdk agent serve --host 0.0.0.0 --allow-public-bind
```

This is not an MCP server and not a hosted public API. It is a local discovery
API for metadata only.
