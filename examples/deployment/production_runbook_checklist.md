# Production Runbook Checklist Template

- [ ] Confirm this is a private environment controlled by your team.
- [ ] Keep `.env`, token stores, logs, exports, downloads, and project data out of git.
- [ ] Use Client Credentials / Data Connection App auth for unattended jobs.
- [ ] Keep sandbox and production credentials fully separate.
- [ ] Run `procore-sdk enterprise readiness-check`.
- [ ] Run `procore-sdk token-store status`.
- [ ] Validate the scheduled export plan.
- [ ] Dry-run the scheduled export plan.
- [ ] Review logs after the first production run.
- [ ] Rotate credentials with a dry-run before resuming schedules.
- [ ] If secrets leak, revoke, rotate, clear token stores, and audit logs.

Tool execution remains disabled. MCP remains discovery-only.
