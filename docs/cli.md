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

## Observations, Punch Items, And Correspondence

Phase 8A adds read-only commands for observations, punch items, and Generic
Tool correspondence items in the current unreleased branch:

```bash
procore-sdk observations --project 352338 --company-id 123456
procore-sdk observation --project 352338 --company-id 123456 --id 42
procore-sdk find-observation --project 352338 --company-id 123456 --number 15
procore-sdk punch-items --project 352338 --company-id 123456
procore-sdk punch-item --project 352338 --company-id 123456 --id 99
procore-sdk find-punch-item --project 352338 --company-id 123456 --query "door"
procore-sdk generic-tools --project 352338 --company-id 123456
procore-sdk correspondences --project 352338 --company-id 123456 --generic-tool-id 77
procore-sdk correspondence --project 352338 --company-id 123456 --id 88
procore-sdk find-correspondence --project 352338 --company-id 123456 --generic-tool-id 77 --query "submittal"
```

Local CSV exports are also available:

```bash
procore-sdk export-observations --project 352338 --company-id 123456 --output exports/observations.csv
procore-sdk export-punch-items --project 352338 --company-id 123456 --output exports/punch-items.csv
procore-sdk export-correspondences --project 352338 --company-id 123456 --generic-tool-id 77 --output exports/correspondences.csv
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

The main workflow and AI commands currently exposed by the CLI include
`project-context`, `enhanced-rfi-package`, `enhanced-submittal-package`,
`ai-review-export`, `ai-prompt-pack`, `workflow-plan`, and `webhook`.

## Agent Registry

Agent registry commands inspect local metadata for future assistant
integrations. They do not execute tools, read credentials, or call Procore.

```bash
procore-sdk agent manifest
procore-sdk agent manifest --json
procore-sdk agent tools
procore-sdk agent tool procore.find_rfi
procore-sdk agent openapi --pretty
procore-sdk agent schemas --pretty
procore-sdk agent serve --port 8765
procore-sdk agent serve --run-log-dir agent-runs
procore-sdk agent runs list --run-log-dir agent-runs
procore-sdk agent runs replay RUN_ID --run-log-dir agent-runs
procore-sdk agent mcp tools --pretty
procore-sdk agent mcp resources --pretty
procore-sdk agent mcp prompts --pretty
procore-sdk agent mcp manifest --pretty
procore-sdk agent mcp stdio
procore-sdk agent evals list
procore-sdk agent evals run
procore-sdk agent evals run registry_safety
```

`agent serve` starts a local HTTP discovery API on `127.0.0.1` by default. It
does not execute tools or call Procore. Binding outside localhost requires
`--allow-public-bind`.

`agent openapi` and `agent schemas` export machine-readable documents for agent
frameworks and gateways. They are specification-only commands and do not require
Procore credentials.

`agent runs` commands inspect, replay, and export opt-in local run logs. Replay
verifies recorded Agent API discovery activity but does not execute tools or
call Procore.

`agent mcp` commands export MCP-style discovery metadata for the same local
agent registry. The Phase 7E MCP adapter is discovery-only: `tools/call` returns
a disabled execution response, and no Procore API calls or credentials are used.

`agent evals` commands run local deterministic safety and quality checks for
agent metadata. They do not execute tools, load credentials, call Procore, or
call AI/model APIs.

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
