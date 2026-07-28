# GC/Owner Private App Installation Packet

Phase 19C provides a local template/documentation aid for requesting and
reviewing a private app and DMSA connection with a GC/Owner administrator.

PyProcore does not install the app or create the DMSA.
PyProcore does not grant access.
The GC/Owner controls private app installation, Permitted Projects, tool
permissions, attachment visibility, webhook setup, and revocation.

## Recommended First-Version Request

The packet recommends minimum access:

- RFIs: **Read Only**
- Submittals: **Read Only**
- visibility for projects explicitly permitted by the GC/Owner
- minimum Read Only project metadata needed to identify those projects

Attachment visibility is conditional and depends on permissions and API payload
availability. RFI/Submittal webhooks are optional; polling fallback can still
use repeated read-only intake runs and local state.

No create, edit, approve, reject, submit, close, reopen, delete, upload, import,
payment, or financial write permission is requested.

## Build The Packet

All commands are local and require no credentials:

```bash
procore-sdk dmsa gc-owner-packet
procore-sdk dmsa permission-request
procore-sdk dmsa security-statement
procore-sdk dmsa email-templates
procore-sdk dmsa troubleshooting-guide
```

Preview the artifact set without writing:

```bash
procore-sdk dmsa gc-owner-packet-write \
  --output-dir ./exports/gc-owner-packet \
  --dry-run
```

Omit `--dry-run` only for intentional local writes. Existing files are
protected unless `--overwrite` is explicitly supplied.

## Packet Artifacts

- `gc_owner_installation_packet.md`
- `permission_request.md`
- `security_statement.md`
- `admin_install_checklist.md`
- `email_templates.md`
- `troubleshooting_guide.md`
- `packet_metadata.json`

The packet includes an executive summary, integration purpose, explicit
non-goals, installation overview, Permitted Projects explanation, permission
request, attachment and webhook guidance, security statement, revocation
statement, admin and sender checklists, email templates, troubleshooting, and
support placeholders.

## Troubleshooting Language

Troubleshooting entries describe a **likely cause** and **recommended review**.
They do not perform live checks or guarantee that access will be available.
Coverage includes 401, 403, 404, empty projects, empty RFIs/Submittals, missing
attachments, webhook delivery, polling with no updates, revoked access, and
missing Permitted Projects.

## Safety Boundaries

- This packet is a template/documentation aid, not a certification.
- PyProcore does not create the DMSA or install the private app.
- PyProcore does not grant or bypass access.
- GC/Owner controls all access and revocation decisions.
- Attachment and webhook availability are not guaranteed.
- No Procore calls are made by the packet CLI, examples, or tests.
- No Procore write actions or automated approvals/submissions are enabled.
- No external AI/model calls, MCP execution, or Procore tool execution occurs.
- The implementer/customer remains responsible for secrets and deployment.
