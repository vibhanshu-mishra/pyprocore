# Enterprise Scheduled Exports

Phase 9B adds local planning patterns for enterprise scheduled exports and Data
Connection App deployments. Phase 9D adds private deployment and production
runbook guidance around those patterns. This is unreleased branch work unless a
later PyPI release includes it. The current published stable release remains
`2.2.0`.

These helpers validate and explain local plan files only. They do not call Procore,
do not run external AI/model APIs, do not enable Procore tool execution, and
keep MCP discovery-only. Tool execution remains disabled.

## What This Does

Scheduled export plans describe the shape of an export before a real job is
scheduled:

- auth mode
- company ID
- project IDs
- resources
- output folder
- output format, currently `csv` or `jsonl`
- dry-run and redaction intent
- project safety limits

Plan files must never contain `client_secret`, access tokens, refresh tokens,
Authorization headers, or token-store contents.

## Recommended Auth Mode

Use `client_credentials` for server-to-server scheduled exports with a Procore
Data Connection App. Access still depends on the Procore app connection,
service-account permissions, company access, project access, and enabled tools.

Use `authorization_code` for user-owned local workflows where a human completed
OAuth and owns the local token store.

## Validate A Plan

```bash
procore-sdk scheduled-export validate examples/configs/scheduled_export_client_credentials.json
```

Validation is local-only. It checks the plan structure, auth mode, output
format, company scope, project scope, requested resources, output directory, and
broad-export warnings.

## Dry-Run A Plan

```bash
procore-sdk scheduled-export dry-run examples/configs/scheduled_export_client_credentials.json
```

Dry-run planning builds a manifest that explains what would be exported,
including estimated output file paths. It does not fetch Procore data and does
not write exported records.

To write the dry-run manifest deliberately:

```bash
procore-sdk scheduled-export dry-run examples/configs/scheduled_export_client_credentials.json \
  --write-manifest exports/scheduled/dry-run-manifest.json
```

## Sample Config

```bash
procore-sdk scheduled-export sample-config
procore-sdk scheduled-export sample-config --output examples/configs/my_scheduled_export.json
```

Sample configs use placeholder IDs only. Replace them after reviewing Procore
permissions and deployment boundaries.

## Deployment Guidance

Keep private deployment material out of the repository:

- Put `.env` on the scheduled host, not in source control.
- Store token files in a private folder with restricted permissions.
- Write export outputs to private storage outside the checkout.
- Separate sandbox and production credentials, token stores, logs, and outputs.
- Rotate Data Connection App credentials on a documented schedule.
- Inspect token-store safety with `procore-sdk token-store status`.
- Use `procore-sdk auth rotation-checklist --auth-mode client_credentials`
  before rotating scheduled export credentials.
- Run `procore-sdk doctor` and a scheduled-export dry run before enabling a real
  schedule.
- Review company, project, app, service-account, and tool permissions before
  adding projects or resources.

Phase 9C adds file and memory token-store backend architecture plus local
diagnostics. File token stores remain the persistent default, memory token
stores are for tests/examples only, and cloud secret-manager backends remain
future work unless explicitly implemented later.

For production readiness, run:

```bash
procore-sdk enterprise readiness-check
procore-sdk enterprise runbook-summary
```

See [Private Deployment](private-deployment.md) and
[Production Runbook](production-runbook.md).

## Safe Scheduling Pattern

1. Create or copy a scheduled export plan.
2. Validate it locally.
3. Dry-run it and review the manifest.
4. Confirm Procore permissions and environment boundaries.
5. Run existing export commands or workflow plans from private infrastructure.
6. Monitor logs and storage usage.

Do not commit `.env`, token stores, logs, downloads, generated exports, private
project data, or dry-run output that reveals internal company/project names.
