# CLI Usage

The `procore-sdk` command exposes PyProcore services and local workflow helpers.
Commands use your `.env` configuration and local token store.

## Auth And Diagnostics

```bash
procore-sdk doctor
procore-sdk doctor --json
procore-sdk doctor --live
procore-sdk auth login-url
procore-sdk auth exchange-code YOUR_AUTHORIZATION_CODE
procore-sdk auth status
procore-sdk auth refresh
```

## Companies And Projects

```bash
procore-sdk companies
procore-sdk projects
procore-sdk find-company Tracker
procore-sdk find-project Hospital
```

## RFIs And Submittals

```bash
procore-sdk rfis --project 352338
procore-sdk rfi --project 352338 --id 102784
procore-sdk find-rfi --project 352338 --number 15
procore-sdk submittals --project 352338
procore-sdk submittal --project 352338 --id 309641
procore-sdk find-submittal --project 352338 --number 27
```

## Documents, Drawings, Specifications, Photos, And Daily Logs

```bash
procore-sdk documents --project 352338
procore-sdk download-document --project 352338 --id 456 --output-dir ./downloads
procore-sdk drawing-areas 352338
procore-sdk drawings 352338
procore-sdk drawings 352338 --area 123
procore-sdk specifications sections --project 352338
procore-sdk photos --project 352338
procore-sdk daily-logs counts --project 352338
```

## Workflow And Package Builders

```bash
procore-sdk sync-rfis --project 352338 --output ./exports/rfis
procore-sdk sync-submittals --project 352338 --output ./exports/submittals
procore-sdk sync-documents --project 352338 --output ./exports/documents
procore-sdk sync-project --project 352338 --output ./exports/project
procore-sdk project-context --project 352338 --output ./project-context
procore-sdk enhanced-rfi-package --project 352338 --rfi-number 15
procore-sdk enhanced-submittal-package --project 352338 --submittal-number 27
```

## AI Exports

PyProcore creates local files for AI review. It does not call AI APIs.

```bash
procore-sdk ai-review-export --package-dir ./rfi-package
procore-sdk ai-prompt-pack --package-dir ./submittal-package --review-type submittal
```

## Workflow Plans

```bash
procore-sdk workflow-plan list
procore-sdk workflow-plan validate examples/workflow_plans/nightly_project_context.json
procore-sdk workflow-plan run examples/workflow_plans/nightly_project_context.json --dry-run
```

## Webhooks

Webhook helpers are local utilities for validating, redacting, saving, listing,
and dry-run dispatching sample payloads.

```bash
procore-sdk webhook validate examples/webhooks/rfi_created.json
procore-sdk webhook save examples/webhooks/rfi_created.json --output-dir ./webhook-events
procore-sdk webhook list --input-dir ./webhook-events
procore-sdk webhook dispatch examples/webhooks/rfi_created.json --dry-run
```

## Common Flags

- `--project`: Procore project ID.
- `--company-id` or `--company`: Procore company ID.
- `--output-dir`: Local output folder for downloads, packages, or exports.
- `--dry-run`: Preview a workflow without writing files or downloading attachments.
- `--overwrite`: Replace existing downloaded files when a command supports it.

## Troubleshooting

If a project-level command returns a 403, first run:

```bash
procore-sdk companies
procore-sdk auth status
procore-sdk doctor
```

Confirm the company ID, project ID, sandbox vs production environment, app
connection, and user permissions.
