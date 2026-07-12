# Replay Agent Run

## What This Does

Replays a local Agent API run log by validating recorded discovery activity.

Replay checks whether events are well-formed, routes are recognized, referenced
tools still exist in the registry, and disabled tool-call attempts still record
`tool_execution_disabled`.

## When To Use It

Use replay for local regression checks, agent safety reviews, and future eval
workflows. Replay verifies what happened; it does not execute Procore actions.

## Before You Start

You need a local run created with `procore-sdk agent serve --run-log-dir`.
No Procore credentials are required for replay.

## Code

List available runs:

```bash
PYTHONPATH=. procore-sdk agent runs list --run-log-dir agent-runs
```

Replay one run:

```bash
PYTHONPATH=. procore-sdk agent runs replay RUN_ID --run-log-dir agent-runs
```

Export a replay bundle:

```bash
PYTHONPATH=. procore-sdk agent runs export RUN_ID \
  --run-log-dir agent-runs \
  --output-dir agent-run-bundles
```

## Expected Output

Replay prints whether the run passed, how many events were checked, and any
warnings or errors.

Export creates:

```text
agent-run-bundles/
  RUN_ID/
    run.json
    run-with-events.json
    events.jsonl
    replay.json
```

## Common Issues

- `Agent run not found` means the run ID or `--run-log-dir` path is wrong.
- Unknown tool warnings can happen if registry names changed after the run was
  recorded.
- Replay does not authenticate with Procore and does not execute tools.
