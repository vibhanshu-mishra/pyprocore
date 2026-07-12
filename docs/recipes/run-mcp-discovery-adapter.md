# Run MCP Discovery Adapter

## What This Does

This recipe runs PyProcore's lightweight MCP-style stdio adapter. It lets local
MCP-compatible clients discover PyProcore agent tools, resources, and prompts.

The adapter is discovery-only in Phase 7E. It does not execute tools and does
not call Procore.

## When To Use It

Use this when testing how an MCP client reads PyProcore metadata before a future
execution phase adds approval gates and guarded tool calls.

## Before You Start

No Procore credentials are required. You do not need `.env`, OAuth tokens,
company IDs, or project IDs. The adapter only serves local metadata.

## Code

Start the stdio adapter:

```bash
procore-sdk agent mcp stdio
```

For local checkout testing:

```bash
PYTHONPATH=. python3 -m pyprocore.app agent mcp stdio
```

You can inspect the same metadata without stdio:

```bash
procore-sdk agent mcp manifest --pretty
procore-sdk agent mcp tools --pretty
procore-sdk agent mcp resources --pretty
procore-sdk agent mcp prompts --pretty
```

## Expected Output

An MCP client can call methods such as `initialize`, `tools/list`,
`resources/list`, `resources/read`, and `prompts/list`.

If a client calls `tools/call`, PyProcore returns a structured disabled
execution response explaining that Phase 7E is discovery-only and no Procore API
call was made.

## Common Issues

- Stdio tools usually wait for JSON-RPC input from a client. Use the metadata
  export commands above if you only want to inspect output in a terminal.
- If your MCP client tries to execute a tool, that is expected to fail safely in
  Phase 7E.
- If the local checkout imports an older installed package, run with
  `PYTHONPATH=.` while developing unreleased changes.
