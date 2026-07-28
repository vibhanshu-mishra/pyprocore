# DMSA Connection Profiles

PyProcore DMSA connection profiles are secret-free local JSON documents for
describing a GC/Owner-authorized Procore Data Connection App connection. They
reference credential environment-variable names and document the intended
company, permitted projects, URLs, and token-store settings.

PyProcore does not create a DMSA in Procore and does not grant project access.
The GC/Owner controls private-app installation, DMSA authorization, permitted
projects, tool permissions, and revocation.

## What You Need From The GC/Owner

Before building a profile, confirm:

- the GC/Owner Company Admin installed the private app with its App Version Key;
- the GC/Owner authorized the DMSA;
- the intended company ID and permitted project IDs;
- Read Only permission for RFIs and Submittals;
- related attachment visibility if attachment sync is needed;
- production or sandbox API and login URLs; and
- whether webhooks will be configured or read-only polling is required.

Attachment availability depends on permissions and the API payload. A profile
does not guarantee attachment access. Webhooks can be planned, but polling may
still be needed.

## Create A Safe Profile

```bash
procore-sdk dmsa sample-profile --output ./local/dmsa-profile.json
```

The generated JSON contains `client_id_env_var` and
`client_secret_env_var`. It does not contain credential values. Store actual
credentials in environment variables or a suitable deployment secret store:

```bash
export PROCORE_CLIENT_ID="your-client-id"
export PROCORE_CLIENT_SECRET="your-client-secret"
```

Keep profile metadata, `.env` files, token stores, exports, and logs outside
source control when they identify private companies or projects.

## Validate And Summarize

These commands are local and make no Procore calls:

```bash
procore-sdk dmsa validate-profile ./local/dmsa-profile.json
procore-sdk dmsa summarize-profile ./local/dmsa-profile.json --format json
procore-sdk dmsa permission-checklist --format markdown
procore-sdk dmsa installation-packet --format markdown
procore-sdk dmsa smoke-plan ./local/dmsa-profile.json --format markdown
procore-sdk dmsa diagnose --status-code 403 --context rfis
```

Diagnostics describe a **likely cause** and **recommended review**. They do not
prove the effective permissions of a live Procore account.

## Build A Client

```python
from pyprocore import Procore

client = Procore.from_dmsa_profile_file("./local/dmsa-profile.json")
```

This factory reuses PyProcore's existing client-credentials OAuth and token
management. Loading the profile and creating the client do not request a token.
The first intentional API operation resolves a token through the existing
client-credentials flow.

## Least-Privilege Boundary

The first integration version should request only Read Only access to RFIs,
Submittals, essential project metadata, and required attachment visibility.
No Procore write actions are enabled. PyProcore does not automatically create,
edit, submit, approve, close, delete, upload, or modify Procore data.

Examples and tests use fake local data. They make no live Procore calls, do not
call external AI/model APIs, and do not enable MCP or Procore tool execution.
