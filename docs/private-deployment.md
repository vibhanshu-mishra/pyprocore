# Private Deployment

PyProcore `v2.3.0` is the current published stable release and includes Phase
8A through 8G plus Phase 9A through 9D.

Private deployment guidance is included in `v2.3.0`.

Phase 9D completes the enterprise authentication and data-access hardening work
on main by documenting private deployment patterns and adding local readiness
checks. PyProcore does not host infrastructure, does not automatically schedule
jobs, does not call external AI/model APIs by default, and does not enable tool
execution. Tool execution remains disabled. MCP remains discovery-only.

## What This Is For

Use this guide when running PyProcore inside a private environment controlled by
your team:

- An operator workstation for local exports.
- A private server for scheduled exports.
- A cron-based runner.
- A Docker-based private export runner.

PyProcore provides SDK commands, workflow helpers, templates, and checks. Your
team provides the runtime, scheduler, credentials, monitoring, and access
controls.

## Recommended Pattern

Use Client Credentials / Data Connection App authentication for server-to-server
scheduled exports. Use Authorization Code authentication for user-driven local
workflows where a human is intentionally operating with their own Procore
permissions.

Before production use:

```bash
procore-sdk enterprise readiness-check \
  --auth-mode client_credentials \
  --environment-name production \
  --token-store-path /opt/pyprocore/token-stores/production/token_store.json \
  --output-dir /opt/pyprocore/exports/production \
  --log-dir /opt/pyprocore/logs/production \
  --plan /opt/pyprocore/plans/nightly_project_context.json

procore-sdk token-store status
procore-sdk scheduled-export validate /opt/pyprocore/plans/nightly_project_context.json
procore-sdk scheduled-export dry-run /opt/pyprocore/plans/nightly_project_context.json
```

These checks are local. They do not call Procore unless you later run an
authenticated export workflow.

## Private Folder Layout

Keep runtime files outside your source checkout:

```text
/opt/pyprocore/
  config/
    sandbox.env
    production.env
  token-stores/
    sandbox/token_store.json
    production/token_store.json
  plans/
    nightly_project_context.json
  exports/
    sandbox/
    production/
  logs/
    sandbox/
    production/
```

Recommended `.gitignore` patterns for private deployments:

```gitignore
.env
*.env
token_store.json
token-stores/
exports/
downloads/
logs/
*.jsonl
*.csv
```

## Local-Only Deployment

Local workflows are best for development, one-off exports, and operator-led
review packages. Authorization Code auth is acceptable when a human is present
and understands the company/project context.

Keep `.env` and token stores private. Use separate `.env` and token-store paths
for sandbox and production.

## Private Server Deployment

Private server deployments should use Client Credentials / Data Connection App
auth. Store `.env`, token stores, exports, downloads, and logs in private
runtime folders. Run readiness checks before installing any external schedule.

PyProcore does not install background jobs. Use your operating system scheduler
or orchestration platform after validating and dry-running the plan.

## Cron Pattern

Cron can run a PyProcore command or wrapper script. Dry-run first and redirect
logs to a private folder. Use absolute paths and load a private environment file
from outside the repository.

See `examples/deployment/cron_example.txt` for a placeholder-only template.

## Docker Pattern

Docker can be useful for repeatable private runners. Mount `.env`, token stores,
plans, exports, and logs as private volumes. Do not bake secrets into an image.

The Docker Compose template in `examples/deployment/docker_compose_example.yml`
is illustrative only. It does not create hosted infrastructure or schedule jobs.

## 401 And 403 Guidance

401 usually means a missing, expired, malformed, or wrong-environment token.
Check auth mode, token-store path, login URL, API base, and credential rotation.

403 usually means the OAuth user or Data Connection App lacks company, project,
or tool access, or the app is not connected to the company. Confirm the company
ID, project IDs, app-company connection, user/DMSA permissions, and sandbox vs
production environment.

## Credential Rotation

Rotate credentials with a controlled dry-run:

1. Rotate the Procore app or Data Connection App secret.
2. Update the private deployment secret store.
3. Clear or replace the old token store in the private runtime path.
4. Request a fresh token through the normal SDK flow.
5. Validate and dry-run scheduled export plans.
6. Resume the external schedule only after logs and outputs look correct.

## What Not To Do

- Do not commit `.env`, token stores, exports, downloads, logs, or project data.
- Do not mix sandbox and production credentials or token stores.
- Do not use Authorization Code for unattended server jobs.
- Do not store client secrets in examples, docs, issue comments, or logs.
- Do not assume PyProcore hosts, schedules, or monitors jobs for you.
- Do not enable agent tool execution; Phase 9D keeps execution disabled.
