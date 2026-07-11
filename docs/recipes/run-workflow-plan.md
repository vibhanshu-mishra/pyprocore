# Run a Workflow Plan

## What this does

Runs a local JSON workflow plan through PyProcore's safe automation runner. The
runner resolves placeholders, executes existing SDK workflow helpers in order,
and writes run manifest files.

## When to use it

Use this for repeatable project exports, scheduled syncs, local review package
generation, and future automation jobs.

## Before you start

Configure `.env` and complete OAuth if your plan includes workflows that call
Procore. Use dry-run first to inspect the resolved steps without executing them.

Useful environment variables:

- `WORKFLOW_PLAN_PATH`
- `WORKFLOW_RUN_OUTPUT_DIR`
- `WORKFLOW_DRY_RUN`

## Code

```python
import os
from pathlib import Path

from pyprocore.workflows import run_workflow_plan

plan_path = Path(os.getenv("WORKFLOW_PLAN_PATH", "workflow.json"))
output_dir = os.getenv("WORKFLOW_RUN_OUTPUT_DIR")

result = run_workflow_plan(
    plan_path,
    output_dir=Path(output_dir) if output_dir else None,
    dry_run=True,
)

print(result.status)
print(result.summary_path)
```

CLI examples:

```bash
procore-sdk workflow-plan run workflow.json --dry-run
procore-sdk workflow-plan run workflow.json --output-dir ./runs
procore-sdk workflow-plan run workflow.json --fail-fast
```

## Expected output

The run output folder contains:

- `run_manifest.json`
- `run_summary.md`
- `plan_resolved.json`
- `errors.json` only when errors exist
- `warnings.json` only when warnings exist

## Common issues

- Dry-run does not execute workflows, so it is safe before scheduled automation.
- Some steps may fail because the OAuth user lacks Procore project permissions.
- Dependent steps are skipped when their dependency fails.
- Workflow plans do not execute shell commands and do not mutate Procore data.
