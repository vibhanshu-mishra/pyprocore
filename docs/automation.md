# Automation

PyProcore automation examples show how to run local workflow plans on a schedule
without adding cloud infrastructure or mutating Procore data.

Start with a dry run:

```bash
procore-sdk workflow-plan validate examples/workflow_plans/nightly_project_context.json
procore-sdk workflow-plan run examples/workflow_plans/nightly_project_context.json --dry-run
```

## Scheduling Guides

- [Cron](automation/cron.md) for macOS and Linux schedules.
- [macOS launchd](automation/launchd.md) for native macOS background jobs.
- [Windows Task Scheduler](automation/windows-task-scheduler.md) for Windows.
- [GitHub Actions](automation/github-actions.md) for scheduled CI templates.
- [Docker](automation/docker.md) for containerized local runs.
- [CI](automation/ci.md) for dry-run validation in automation pipelines.
- [Webhooks](automation/webhooks.md) for local webhook payload validation and dry-run dispatch.

## Safety Notes

- Do not commit `.env` files or token stores.
- Use absolute paths in schedulers.
- Redirect logs to a folder that is not committed.
- Run `--dry-run` before enabling a schedule.
- GitHub Actions scheduled runs need a deliberate token-store strategy before
  they can call live Procore APIs.
