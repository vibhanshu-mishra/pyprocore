# Integration Blueprints

Phase 17C adds a local integration blueprint layer for teams designing
PyProcore-powered sync workers, webhook receivers, read-only internal APIs, and
dashboard data bridges.

Blueprints are templates and readiness guidance only. PyProcore does not host
infrastructure, schedule jobs automatically, store secrets in a database, call
Procore from blueprint commands, call external AI/model APIs, enable MCP
execution, enable Procore tool execution, or enable Procore write actions.

## What Blueprints Provide

- Local metadata for common integration service shapes.
- Required environment-variable checklists.
- Suggested local output files.
- Safety boundaries and no-secrets guidance.
- Test strategy notes.
- Pseudocode and example CLI commands.
- Local JSON/Markdown reports.

## Built-In Blueprints

- `procore_to_csv_sync_worker`
- `procore_to_jsonl_sync_worker`
- `procore_webhook_receiver`
- `procore_fastapi_read_api`
- `procore_dashboard_data_bridge`
- `procore_scheduled_export_worker`
- `procore_project_health_feed`

The FastAPI and dashboard blueprints are static design guidance only. PyProcore
does not add FastAPI, Docker, Redis, Sidekiq, Postgres, cloud, or database
dependencies.

## CLI Examples

```bash
procore-sdk integrations blueprints
procore-sdk integrations blueprint procore_to_csv_sync_worker
procore-sdk integrations blueprint procore_dashboard_data_bridge --format json
procore-sdk integrations readiness procore_webhook_receiver --output-dir ./exports
```

Create and inspect local sync-run records:

```bash
procore-sdk integrations sync-run sample --output-dir ./exports/sync-runs
procore-sdk integrations sync-run summarize ./exports/sync-runs
```

Create and verify a local webhook fixture:

```bash
procore-sdk integrations webhook sample-event --output ./tmp/webhook-event.json
procore-sdk integrations webhook verify \
  --event ./tmp/webhook-event.json \
  --secret PROCORE_WEBHOOK_SECRET
```

For local tests only, you can pass a direct test secret:

```bash
procore-sdk integrations webhook verify \
  --event ./tmp/webhook-event.json \
  --secret local-test-secret \
  --secret-is-value
```

The CLI never prints the secret value.

## Local Sync Run Records

The sync-run helpers write local JSON and JSONL files only. They are useful for
cron jobs, CI jobs, or user-owned workers that need simple run records without a
database.

Suggested pattern:

1. Create a sync run record.
2. Append redacted JSONL log entries.
3. Complete or fail the run.
4. Summarize local run files.

Secret-like keys such as `token`, `secret`, `authorization`, and `password` are
redacted before structured log data is written.

## Webhook Fixture Helpers

Webhook helpers are generic local HMAC SHA-256 fixture tools. They can normalize
headers/body metadata, compute test signatures, verify test signatures, and
write sanitized local event records.

They are not a hosted webhook receiver. Match the signature header, payload
canonicalization, and verification rules to the provider configuration used by
your own service.

## Readiness Checks

Readiness checks inspect local setup signals:

- Required environment variables.
- Output directory presence.
- Token store path placement.
- Sync log directory presence.
- Webhook secret availability for webhook blueprints.
- Placeholder secret warnings.
- Declared safety boundaries.

Readiness checks do not validate live Procore access and do not call Procore.

## Safety Boundaries

- No hosted app is created.
- No scheduled job is installed.
- No database storage is included.
- No Procore live sync is started.
- No Procore writes or mutations are enabled.
- No external AI/model calls are made.
- MCP remains discovery-only.
- Procore tool execution remains disabled.

