# Schedule a Workflow Plan

## What this does

Shows how to run an existing PyProcore workflow plan automatically using local
or CI schedulers.

## When to use it

Use this after you have validated a workflow plan and want it to run hourly,
nightly, weekly, or on demand.

## Before you start

Make sure your plan validates and dry-runs locally:

```bash
PYTHONPATH=. procore-sdk workflow-plan validate examples/workflow_plans/nightly_project_context.json
PYTHONPATH=. procore-sdk workflow-plan run examples/workflow_plans/nightly_project_context.json --dry-run
```

If the plan calls Procore, configure `.env`, complete OAuth once, and confirm
the scheduled user has access to the company/project.

## Code

Local script example:

```bash
examples/scheduled/run_workflow_plan.sh \
  examples/workflow_plans/nightly_project_context.json \
  runs/nightly-project-context
```

PowerShell example:

```powershell
powershell -ExecutionPolicy Bypass -File examples\scheduled\run_workflow_plan.ps1 `
  -PlanPath examples\workflow_plans\nightly_project_context.json `
  -OutputDir runs\nightly-project-context
```

## Expected output

The scheduled run writes normal workflow-plan output:

- `run_manifest.json`
- `run_summary.md`
- `plan_resolved.json`
- `errors.json` only when errors exist
- `warnings.json` only when warnings exist

## Common issues

- Use absolute paths when configuring cron, launchd, or Windows Task Scheduler.
- Dry-run before scheduling real runs.
- Scheduled jobs may use a different user account than your terminal.
- If auth fails only in the scheduler, check the working directory, `.env`, and
  token store for that scheduled user.
- GitHub Actions scheduled live runs need a token-store strategy before OAuth
  refresh can work reliably in CI.

## More scheduling guides

- [Cron](../automation/cron.md)
- [macOS launchd](../automation/launchd.md)
- [Windows Task Scheduler](../automation/windows-task-scheduler.md)
- [GitHub Actions](../automation/github-actions.md)
