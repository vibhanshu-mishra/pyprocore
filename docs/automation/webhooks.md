# Local Webhook Helpers

PyProcore includes local webhook helpers for testing payload handling before you
build a hosted webhook receiver.

These helpers do not start a web server, create public URLs, register webhooks
with Procore, or mutate Procore data. They process webhook JSON that you already
have in a file or stdin.

## What You Can Do

- Validate a webhook payload shape.
- Normalize flexible Procore event payloads into one typed model.
- Redact sensitive fields before saving.
- Save local event files under `webhook-events/`.
- List saved events with simple filters.
- Dry-run an existing workflow plan from an event.

## Validate an Event

```bash
procore-sdk webhook validate examples/webhooks/rfi_created_event.json
```

For JSON output:

```bash
procore-sdk webhook validate examples/webhooks/rfi_created_event.json --json
```

## Save an Event

```bash
procore-sdk webhook save examples/webhooks/rfi_created_event.json
```

Use a custom event store:

```bash
procore-sdk webhook save examples/webhooks/rfi_created_event.json --event-dir ./webhook-events-dev
```

PyProcore saves a redacted original payload and a normalized event file:

```text
webhook-events/
  2026-07-10/
    event-20260710T143000Z-evt-example-rfi-created.json
    event-20260710T143000Z-evt-example-rfi-created.normalized.json
```

## List Events

```bash
procore-sdk webhook list
procore-sdk webhook list --project-id 123
procore-sdk webhook list --resource-type rfi --event-type rfi.created
```

## Dispatch to a Workflow Plan

Dispatch defaults to dry-run, which validates and resolves the workflow plan
without live workflow execution:

```bash
procore-sdk webhook dispatch examples/webhooks/rfi_created_event.json \
  --workflow-plan examples/workflow_plans/lightweight_sync.json \
  --dry-run
```

Only use `--no-dry-run` when your `.env`, OAuth token store, IDs, and workflow
plan are ready for live Procore reads.

## Event Placeholders

When dispatching a workflow plan, event values are available as placeholders:

```text
{event.id}
{event.type}
{event.action}
{event.company_id}
{event.project_id}
{event.resource_type}
{event.resource_id}
```

## Security Notes

PyProcore recursively redacts common sensitive keys, including tokens, secrets,
passwords, API keys, authorization values, signatures, and webhook secrets.

Do not expose webhook secrets in examples, logs, screenshots, issue reports, or
committed payloads. For production receiving, use a real web framework or hosted
webhook service with proper signature verification and secret storage.

## Troubleshooting

If validation warns that fields are missing, the payload may still be useful.
Webhook shapes vary, so PyProcore records warnings instead of rejecting flexible
payloads.

If listing returns no events, confirm you are using the same `--event-dir` used
when saving.

If dispatch creates a workflow output folder during dry-run, that is expected.
Dry-run writes local run manifests and summaries, but it does not execute live
workflow steps.
