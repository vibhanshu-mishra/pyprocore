# API Coverage

PyProcore focuses on read-oriented SDK and automation workflows. The table below
summarizes current coverage without overclaiming live verification in every
Procore environment.

| Area | Status | Read/List/Get/Download Support | Notes |
| --- | --- | --- | --- |
| Companies | Supported | List | Used to discover companies available to the token. |
| Projects | Supported | List, get | Project listing is company-scoped. |
| RFIs | Supported | List, get, download attachments | Attachments are read from RFI questions when Procore includes signed URLs. |
| Submittals | Supported | List, get, download attachments | Attachments are downloaded from Procore-provided URLs. |
| Documents | Supported | List folders, list files, get, download, sync | Uses Procore folder/file endpoints behind user-friendly service names. |
| Drawings | Supported | List areas, list drawings, get, find, download when URL is present | Drawings are organized by drawing areas. Download depends on Procore payload URLs. |
| Specifications | Supported | List sets, list sections, get revisions, download revisions | V2 endpoints are used where appropriate. |
| Photos | Supported | List albums, list photos, get, find, download | SDK names map to Procore image category/image API terms. |
| Daily Logs | Supported | Counts, headers, type-specific listing, date summaries | Read-only helpers for common log workflows. |
| Observations | Unreleased Phase 8A | List, get, find, CSV/JSONL export | Read-only helpers use project context and typed flexible models. |
| Punch Items | Unreleased Phase 8A | List, get, find, CSV/JSONL export | Read-only helpers use project context and typed flexible models. |
| Generic Tools / Correspondence | Unreleased Phase 8A | List Generic Tools, list/get/find correspondence items, CSV/JSONL export | Correspondence-like items are modeled through Procore Generic Tools. |
| Attachments/downloads | Supported | Streaming downloads, skip existing files, overwrite option | Downloads are local file operations only. |
| Workflows | Supported | CSV, JSONL, folder sync, project context, AI-ready packages | Workflows create local files and do not mutate Procore data. |
| Webhooks | Local helpers | Validate, redact, save, list, dry-run dispatch | No hosted webhook server is included. |
| Agent registry | Metadata only | Manifest, tool list, tool lookup | No tool execution, server, credentials, or live Procore calls. |

## Agent Tool Registry

The agent registry describes existing read-only and local-file-output PyProcore
operations for future assistant integrations. It is intentionally metadata-only:
it does not execute SDK functions, mutate Procore data, read credentials, or
start a server.

See [Agent API](agent-api.md) for the CLI and Python usage.

## Phase 8A Endpoint Notes

Phase 8A adds read-only SDK coverage for Observations, Punch Items, and Generic
Tools / correspondence-like items. The implementation follows conservative
endpoint helpers and mocked unit tests only:

- Observations: `/rest/v1.0/observations/items` with `project_id` as query context.
- Punch Items: `/rest/v1.0/punch_items` with `project_id` as query context.
- Generic Tools: `/rest/v1.0/generic_tools` with `project_id` as query context.
- Generic Tool Items: `/rest/v1.0/generic_tools/{generic_tool_id}/generic_tool_items`.

These helpers do not create, update, delete, or mutate Procore data. If a live
Procore environment returns a different payload shape or permission response,
open an issue with sanitized endpoint details and no tokens or secrets.

## Live Verification Notes

Procore access varies by environment, company, project, app connection, and user
permissions. A command can be implemented correctly and still receive a 403 or
404 if the OAuth app is not connected to the company, the project belongs to a
different environment, a tool is disabled, or the user lacks permission.

Use the smoke helper scripts only when you intentionally want to inspect live
payload behavior in your own sandbox or production environment.

Manual smoke helpers are not part of the normal test suite. They require valid
Procore credentials, a project the OAuth user can access, and the correct
sandbox or production API base:

```bash
PROCORE_PROJECT_ID=352338 make smoke-documents
PROCORE_PROJECT_ID=352338 make smoke-drawings
PROCORE_PROJECT_ID=352338 make smoke-specifications
PROCORE_PROJECT_ID=352338 make smoke-photos
PROCORE_PROJECT_ID=352338 make smoke-daily-logs
```

If one of these returns a 403, authentication may still be valid. Confirm the
company/project pairing, app connection, user permissions, enabled Procore tool,
and sandbox vs production environment.
