# Cron Scheduling

Cron can run PyProcore workflow plans on macOS or Linux. Use absolute paths in
cron entries because cron starts with a very small environment.

## Before You Start

1. Install PyProcore in the Python environment used by the scheduled job.
2. Configure `.env` in your project folder.
3. Validate your plan.
4. Run a dry-run first.

```bash
cd /absolute/path/to/pyprocore
PYTHONPATH=. procore-sdk workflow-plan validate examples/workflow_plans/nightly_project_context.json
PYTHONPATH=. procore-sdk workflow-plan run examples/workflow_plans/nightly_project_context.json --dry-run
```

## Local Runner Script

Use the helper script so cron stays readable:

```bash
/absolute/path/to/pyprocore/examples/scheduled/run_workflow_plan.sh \
  /absolute/path/to/pyprocore/examples/workflow_plans/nightly_project_context.json \
  /absolute/path/to/pyprocore/runs/nightly-project-context
```

## Cron Examples

Edit your cron table:

```bash
crontab -e
```

Hourly:

```cron
0 * * * * /absolute/path/to/pyprocore/examples/scheduled/run_workflow_plan.sh /absolute/path/to/pyprocore/examples/workflow_plans/rfi_submittal_sync.json /absolute/path/to/pyprocore/runs/rfi-submittal-sync >> /absolute/path/to/pyprocore/logs/cron-rfi-sync.log 2>&1
```

Nightly at 2:00 AM:

```cron
0 2 * * * /absolute/path/to/pyprocore/examples/scheduled/run_workflow_plan.sh /absolute/path/to/pyprocore/examples/workflow_plans/nightly_project_context.json /absolute/path/to/pyprocore/runs/nightly-project-context >> /absolute/path/to/pyprocore/logs/cron-nightly.log 2>&1
```

Weekly on Sunday at 3:30 AM:

```cron
30 3 * * 0 /absolute/path/to/pyprocore/examples/scheduled/run_workflow_plan.sh /absolute/path/to/pyprocore/examples/workflow_plans/weekly_ai_export.json /absolute/path/to/pyprocore/runs/weekly-ai-export >> /absolute/path/to/pyprocore/logs/cron-weekly-ai.log 2>&1
```

## Loading `.env`

PyProcore loads `.env` from the current working directory. The helper script
changes into the repository root before running the CLI. If you write your own
cron entry, include `cd /absolute/path/to/pyprocore && ...`.

## Troubleshooting

- Use absolute paths for the plan, output folder, and log files.
- Check the redirected log file first.
- Run the exact command manually before adding it to cron.
- If auth works locally but fails in cron, confirm cron is using the same
  working directory and Python environment.
- Start with `--dry-run`; then remove it when the plan and paths are correct.
