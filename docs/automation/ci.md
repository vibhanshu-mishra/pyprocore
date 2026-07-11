# CI Automation

PyProcore includes CI-friendly examples for validating the package, checking
examples, and dry-running workflow plans without live Procore access.

## Recommended pattern

Start with local-only or dry-run checks:

```bash
procore-sdk --help
procore-sdk workflow-plan validate examples/workflow_plans/lightweight_sync.json
procore-sdk workflow-plan run examples/workflow_plans/lightweight_sync.json --dry-run
```

For Docker-based CI, see:

```text
examples/github-actions/pyprocore-docker-workflow.yml
```

That template:

- builds the Docker image
- runs `procore-sdk --help`
- validates a sample workflow plan
- dry-runs a sample workflow plan
- uploads dry-run output as an artifact

## Secrets

Use CI secrets for Procore values:

- `PROCORE_CLIENT_ID`
- `PROCORE_CLIENT_SECRET`
- `PROCORE_REDIRECT_URI`
- `PROCORE_LOGIN_URL`
- `PROCORE_API_BASE`
- `PROCORE_COMPANY_ID`

Never print secrets, tokens, authorization headers, token stores, or `.env`
contents in CI logs.

## Live scheduled runs

GitHub Actions scheduled live runs need a valid OAuth token refresh and
token-store strategy. Treat that as a deliberate production decision. The
included examples are templates and default to safer validation or dry-run
behavior where possible.

## Artifacts

Upload generated outputs as CI artifacts instead of committing them:

- workflow manifests
- run summaries
- dry-run outputs
- local export folders

Do not commit generated downloads, logs, token stores, or webhook event stores.

## Troubleshooting

If a CI dry-run fails validation, run the same workflow plan locally first.

If Docker builds locally but fails in CI, confirm `.dockerignore` is not
excluding required source, docs, or example files.

If live CI runs fail with authentication errors, confirm the OAuth app,
environment, company, project, user access, and token-store strategy.
