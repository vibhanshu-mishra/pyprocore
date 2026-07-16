# CLI Usage

The `procore-sdk` command exposes PyProcore services and local workflow helpers.
Commands use your `.env` configuration and local token store.

## Auth And Diagnostics

These commands show auth mode, configured URLs, token-store path/readability,
expiry, and refresh-token availability without printing secrets or token values.
In `client_credentials` mode, renewal requests a new token and a refresh token
is not required. A 401 usually means token, credential, expiry, or environment
trouble; a 403 usually means user/service-account permissions, project/tool
access, or an app-company connection issue.

```bash
procore-sdk doctor
procore-sdk doctor --json
procore-sdk doctor --live
procore-sdk auth login-url
procore-sdk auth exchange-code YOUR_AUTHORIZATION_CODE
procore-sdk auth client-credentials-token
procore-sdk auth status
procore-sdk auth refresh
```

`auth client-credentials-token` is for `PROCORE_AUTH_MODE=client_credentials`
setups such as Procore Data Connection Apps. It requests and stores a
server-to-server access token without using a redirect URI.

## Scheduled Export Planning

Phase 9B adds local-only scheduled export planning commands for enterprise
Data Connection App deployment patterns. These commands validate and explain
plan files; they do not call Procore, do not fetch data, and do not run exports.

```bash
procore-sdk scheduled-export sample-config
procore-sdk scheduled-export sample-config --output examples/configs/my_scheduled_export.json
procore-sdk scheduled-export validate examples/configs/scheduled_export_client_credentials.json
procore-sdk scheduled-export dry-run examples/configs/scheduled_export_client_credentials.json
procore-sdk scheduled-export dry-run examples/configs/scheduled_export_client_credentials.json --json
```

Use `client_credentials` for unattended server-to-server jobs. Use
`authorization_code` only for user-owned local workflows with a private token
store.

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

## Meetings, Inspections, And Incidents

Phase 8C adds read-only commands for meetings, checklist-backed inspections,
incidents, and project incident configuration in the current unreleased branch:

```bash
procore-sdk meetings --project 352338 --company-id 123456
procore-sdk meeting --project 352338 --company-id 123456 --id 42
procore-sdk find-meeting --project 352338 --company-id 123456 --query "weekly"
procore-sdk inspections --project 352338 --company-id 123456
procore-sdk inspection --project 352338 --company-id 123456 --id 99
procore-sdk find-inspection --project 352338 --company-id 123456 --query "safety"
procore-sdk incidents --project 352338 --company-id 123456
procore-sdk incident --project 352338 --company-id 123456 --id 88
procore-sdk incident-configuration --project 352338 --company-id 123456
procore-sdk find-incident --project 352338 --company-id 123456 --query "near miss"
```

Local CSV exports are also available:

```bash
procore-sdk export-meetings --project 352338 --company-id 123456 --output exports/meetings.csv
procore-sdk export-inspections --project 352338 --company-id 123456 --output exports/inspections.csv
procore-sdk export-incidents --project 352338 --company-id 123456 --output exports/incidents.csv
```

## Directory, Vendors, Departments, Distribution Groups, And Locations

Phase 8D adds read-only commands for company/project users, vendors,
departments, project distribution groups, and project locations in the current
unreleased branch:

```bash
procore-sdk company-users --company-id 123456
procore-sdk company-user --company-id 123456 --id 42
procore-sdk find-company-user --company-id 123456 --email person@example.com
procore-sdk project-users --project 352338 --company-id 123456
procore-sdk project-user --project 352338 --company-id 123456 --id 42
procore-sdk find-project-user --project 352338 --company-id 123456 --name "Alex"
procore-sdk vendors --company-id 123456
procore-sdk vendor --company-id 123456 --id 77
procore-sdk find-vendor --company-id 123456 --name "Concrete"
procore-sdk departments --company-id 123456
procore-sdk department --company-id 123456 --id 12
procore-sdk find-department --company-id 123456 --name "Operations"
procore-sdk distribution-groups --project 352338 --company-id 123456
procore-sdk distribution-group --project 352338 --company-id 123456 --id 33
procore-sdk find-distribution-group --project 352338 --company-id 123456 --name "Team"
procore-sdk locations --project 352338 --company-id 123456
procore-sdk location --project 352338 --company-id 123456 --id 44
procore-sdk find-location --project 352338 --company-id 123456 --name "Level 1"
```

Local CSV exports are also available:

```bash
procore-sdk export-company-users --company-id 123456 --output exports/company-users.csv
procore-sdk export-project-users --project 352338 --company-id 123456 --output exports/project-users.csv
procore-sdk export-vendors --company-id 123456 --output exports/vendors.csv
procore-sdk export-departments --company-id 123456 --output exports/departments.csv
procore-sdk export-distribution-groups --project 352338 --company-id 123456 --output exports/distribution-groups.csv
procore-sdk export-locations --project 352338 --company-id 123456 --output exports/locations.csv
```

## Financial And Change Management Read Commands

Phase 8E adds read-oriented commands for financial and change-management
resources in the current unreleased branch. These commands do not create,
update, delete, approve, change statuses, modify budgets, create commitments,
create invoices, or mutate payments.

```bash
procore-sdk change-events --project 352338 --company-id 123456
procore-sdk change-event --project 352338 --company-id 123456 --id 10
procore-sdk find-change-event --project 352338 --company-id 123456 --number CE-001
procore-sdk change-event-statuses --project 352338 --company-id 123456
procore-sdk change-event-types --project 352338 --company-id 123456
procore-sdk change-event-settings --project 352338 --company-id 123456
procore-sdk prime-change-orders --project 352338 --company-id 123456
procore-sdk direct-costs --project 352338 --company-id 123456
procore-sdk budget-views --project 352338 --company-id 123456
procore-sdk budget-details --project 352338 --company-id 123456 --budget-view 1
procore-sdk cost-codes --company-id 123456
procore-sdk wbs-codes --project 352338 --company-id 123456
procore-sdk commitments --project 352338 --company-id 123456
```

Local CSV exports are also available:

```bash
procore-sdk export-change-events --project 352338 --company-id 123456 --output exports/change-events.csv
procore-sdk export-prime-change-orders --project 352338 --company-id 123456 --output exports/prime-change-orders.csv
procore-sdk export-direct-costs --project 352338 --company-id 123456 --output exports/direct-costs.csv
procore-sdk export-budget-views --project 352338 --company-id 123456 --output exports/budget-views.csv
procore-sdk export-budget-details --project 352338 --company-id 123456 --budget-view 1 --output exports/budget-details.csv
procore-sdk export-cost-codes --company-id 123456 --output exports/cost-codes.csv
procore-sdk export-commitments --project 352338 --company-id 123456 --output exports/commitments.csv
```

## Contracts, Invoices, Payments, And Billing Read Commands

Phase 8F adds read-oriented commands for contracts, invoices, payments, and
billing resources in the current unreleased branch. These commands do not
create, update, delete, submit, approve, reject, change statuses, generate PDFs,
update SOV values, mutate line items, or submit payments.

```bash
procore-sdk prime-contracts --project 352338 --company-id 123456
procore-sdk prime-contract-line-items --project 352338 --company-id 123456 --prime-contract 10
procore-sdk owner-invoices --project 352338 --company-id 123456 --prime-contract 10
procore-sdk subcontractor-invoices --project 352338 --company-id 123456
procore-sdk contract-payments --project 352338 --company-id 123456
procore-sdk billing-periods --project 352338 --company-id 123456
procore-sdk cost-types --company-id 123456
procore-sdk tax-codes --company-id 123456
```

```bash
procore-sdk export-prime-contracts --project 352338 --company-id 123456 --output exports/prime-contracts.csv
procore-sdk export-owner-invoices --project 352338 --company-id 123456 --prime-contract 10 --output exports/owner-invoices.csv
procore-sdk export-contract-payments --project 352338 --company-id 123456 --output exports/contract-payments.csv
```

## Project Management Extras Read Commands

Phase 8G adds read-oriented commands for schedules, tasks, calendar items,
coordination issues, forms, and action plans in the current unreleased branch.
These commands do not upload schedules, create schedule imports, mutate tasks,
submit forms, complete action plans, approve, change statuses, or perform other
project-management writes.

```bash
procore-sdk project-schedule --project 352338 --company-id 123456
procore-sdk schedule-settings --project 352338 --company-id 123456
procore-sdk schedule-resource-assignments --project 352338 --company-id 123456
procore-sdk tasks --project 352338 --company-id 123456
procore-sdk task --project 352338 --company-id 123456 --id 10
procore-sdk find-task --project 352338 --company-id 123456 --number 15
procore-sdk task-requested-changes --project 352338 --company-id 123456 --task 10
procore-sdk calendar-items --project 352338 --company-id 123456
procore-sdk coordination-issues --project 352338 --company-id 123456
procore-sdk coordination-issue-change-history --project 352338 --company-id 123456 --coordination-issue 20
procore-sdk forms --project 352338 --company-id 123456
procore-sdk form-templates --project 352338 --company-id 123456
procore-sdk action-plans --project 352338 --company-id 123456
procore-sdk action-plan-change-history --project 352338 --company-id 123456 --action-plan 30
```

Local CSV exports are also available:

```bash
procore-sdk export-tasks --project 352338 --company-id 123456 --output exports/tasks.csv
procore-sdk export-calendar-items --project 352338 --company-id 123456 --output exports/calendar-items.csv
procore-sdk export-coordination-issues --project 352338 --company-id 123456 --output exports/coordination-issues.csv
procore-sdk export-forms --project 352338 --company-id 123456 --output exports/forms.csv
procore-sdk export-action-plans --project 352338 --company-id 123456 --output exports/action-plans.csv
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
