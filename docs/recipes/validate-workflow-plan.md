# Validate a Workflow Plan

## What this does

Checks a local workflow plan file before running it. Validation confirms the
plan shape, step IDs, supported workflow names, dependencies, and option
structure.

## When to use it

Use this before a scheduled run, cron job, GitHub Actions job, or any repeatable
export workflow.

## Before you start

Create a JSON workflow plan file. Validation is local-only and does not require
Procore credentials.

Useful environment variables:

- `WORKFLOW_PLAN_PATH`

## Code

```python
import os
from pathlib import Path

from pyprocore.workflows import load_workflow_plan, validate_workflow_plan

plan_path = Path(os.getenv("WORKFLOW_PLAN_PATH", "workflow.json"))
plan = validate_workflow_plan(load_workflow_plan(plan_path))

print(plan.name)
print(len(plan.steps))
```

CLI example:

```bash
procore-sdk workflow-plan validate workflow.json
```

## Expected output

You should see a short message saying the workflow plan is valid, plus the plan
name and step count.

## Common issues

- If YAML is not enabled, use JSON plans.
- If a dependency fails validation, make sure `depends_on` references an earlier
  step ID.
- If a workflow name is unknown, run `procore-sdk workflow-plan list`.
- Validation does not call Procore, so permission errors only appear during a
  real run.
