# Inspect Agent Run Logs

## What This Does

Shows how to opt in to local Agent API run logging and inspect recorded
discovery activity.

Run logs record sanitized summaries of local Agent API requests such as
`/health`, `/agent/tools`, `/agent/openapi.json`, and disabled `/call`
attempts. They do not record raw headers, tokens, client secrets, `.env` values,
or full signed URLs.

## When To Use It

Use local run logs when you want an audit trail for agent discovery traffic,
future evals, safety reviews, regression checks, or replay experiments.

## Before You Start

No Procore credentials are required. Run logging is off by default and only
writes files when you pass `--run-log-dir`.

## Code

Start the local discovery server with logging enabled:

```bash
PYTHONPATH=. procore-sdk agent serve --run-log-dir agent-runs
```

In another terminal, call local discovery endpoints:

```bash
curl http://127.0.0.1:8765/health
curl http://127.0.0.1:8765/agent/tools
```

List saved runs:

```bash
PYTHONPATH=. procore-sdk agent runs list --run-log-dir agent-runs
```

Show one run:

```bash
PYTHONPATH=. procore-sdk agent runs show RUN_ID --run-log-dir agent-runs
```

## Expected Output

PyProcore creates local files like:

```text
agent-runs/
  RUN_ID/
    run.json
    events.jsonl
```

## Common Issues

- If no runs appear, confirm you started `agent serve` with `--run-log-dir`.
- If local checkout changes are not visible, use `PYTHONPATH=.`.
- Run logs are summaries, not full request archives.
- Tool execution is still disabled.
