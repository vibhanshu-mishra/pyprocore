# GitHub Actions Scheduled Workflows

The example GitHub Actions workflow shows how to validate and run a PyProcore
workflow plan on a schedule or manually through `workflow_dispatch`.

## Template

Use:

```text
examples/github-actions/pyprocore-scheduled-workflow.yml
```

Copy it into:

```text
.github/workflows/pyprocore-scheduled-workflow.yml
```

## What It Does

- Checks out the repository.
- Sets up Python 3.12.
- Installs PyProcore.
- Validates a workflow plan.
- Runs the workflow plan.
- Uploads the output folder as a GitHub Actions artifact.

For Docker-based CI dry-runs, see:

```text
examples/github-actions/pyprocore-docker-workflow.yml
```

That template builds the Docker image, runs `procore-sdk --help`, validates a
sample workflow plan, and dry-runs the plan without requiring live Procore
credentials.

## Required Secrets

Configure repository or organization secrets:

- `PROCORE_CLIENT_ID`
- `PROCORE_CLIENT_SECRET`
- `PROCORE_REDIRECT_URI`
- `PROCORE_LOGIN_URL`
- `PROCORE_API_BASE`
- `PROCORE_COMPANY_ID`

Never print these values in workflow logs.

## OAuth Token Store Limitation

Scheduled GitHub Actions runs need a valid token-store strategy before live
Procore calls can refresh OAuth tokens. The template is ready for plan
validation and artifact upload, but live scheduled API runs should be treated as
pending until your team decides how encrypted token storage and refresh should
work in CI.

## Schedule Syntax

The template uses:

```yaml
schedule:
  - cron: "0 2 * * *"
```

That runs daily at 2:00 AM UTC. Adjust the cron expression for your team.

## Manual Runs

The template includes:

```yaml
workflow_dispatch:
```

This lets you run it manually from the GitHub Actions tab.

## Artifact Safety

The workflow uploads the configured output folder only. Review generated files
before sharing artifacts outside your organization.
