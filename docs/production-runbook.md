# Production Runbook

PyProcore `v2.3.0` is the current published stable release and includes Phase
8A through 8G plus Phase 9A through 9D. This runbook is for private/internal
deployments only.

PyProcore does not host scheduled jobs, does not automatically run background
jobs, does not call external AI/model APIs by default, and does not enable tool
execution. MCP remains discovery-only.

## 1. Pre-Deployment Checklist

- Confirm the deployment is private and controlled by your team.
- Confirm `.env`, token stores, exports, logs, downloads, and project data are
  outside source control.
- Confirm sandbox and production paths are separate.
- Confirm operator access is limited to the people who need it.

## 2. Environment Setup

- Use absolute paths for config, token stores, exports, and logs.
- Store `.env` files outside the repository.
- Set `PROCORE_TOKEN_STORE_PATH` to a private runtime path.
- Redirect logs to a private log folder.

## 3. Auth Mode Selection

Use Client Credentials / Data Connection App auth for server-to-server scheduled
exports. Use Authorization Code auth for user-driven local workflows.

## 4. Data Connection App Setup Notes

Confirm the app is connected to the target company. Confirm the DMSA/app has
permissions for every company, project, and tool included in the export plan.

## 5. Token-Store Safety Check

```bash
procore-sdk token-store status
python3 scripts/check_token_store_safety.py
```

No command should print access tokens, refresh tokens, client secrets, or
authorization headers.

## 6. Scheduled Export Plan Validation

```bash
procore-sdk scheduled-export validate /opt/pyprocore/plans/nightly_project_context.json
```

Fix all validation errors before any production run.

## 7. Dry-Run Procedure

```bash
procore-sdk scheduled-export dry-run /opt/pyprocore/plans/nightly_project_context.json
```

Review the dry-run manifest, planned files, warnings, and target output paths.

## 8. First Production Run Checklist

- Run once manually before scheduling.
- Confirm company and project context.
- Confirm logs are written to the private log folder.
- Confirm outputs are written to the expected private export folder.
- Confirm no secrets appear in logs.

## 9. Monitoring And Log Review

Review structured logs, export manifests, failed resource counts, skipped items,
and disk usage. PyProcore does not provide hosted monitoring.

## 10. 401 Troubleshooting

Check token expiry, token-store path, auth mode, login URL, API base, client ID,
client secret, and sandbox/production alignment.

## 11. 403 Troubleshooting

Confirm the app is connected to the company. Confirm user or DMSA permissions,
company ID, project IDs, tool access, and production vs sandbox environment.

## 12. Sandbox Vs Production Mismatch

Never mix sandbox credentials with production API URLs or token stores. Use
separate folders, `.env` files, token stores, logs, and exports.

## 13. Credential Rotation Procedure

Rotate credentials in Procore, update private secrets, clear or replace token
stores, request a fresh token through the normal SDK flow, validate plans,
dry-run exports, and only then resume external schedules.

## 14. Leaked `.env` Or Token Store

Disable the external schedule, revoke or rotate Procore credentials, delete or
quarantine leaked token stores, audit logs, create a fresh token store, and
document the incident internally. Do not paste secrets into public issues.

## 15. Rollback Procedure

Disable the external schedule, restore the last known good private config, run
readiness checks, validate and dry-run the plan, then resume only after review.

## 16. Release Upgrade Checklist

Read the changelog, test in sandbox first, run examples and readiness checks,
validate scheduled export plans, dry-run, and then update production.

## 17. Decommissioning Checklist

Disable schedules, archive required outputs, clear token stores, revoke app
access if needed, remove private `.env` files, and document the shutdown.
