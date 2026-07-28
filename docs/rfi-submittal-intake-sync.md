# RFI/Submittal Intake Sync

Phase 19B adds a read-only intake workflow for normalizing RFI and Submittal
records into local audit and polling outputs. The included CLI, examples, and
tests use mocked/local JSON only. They do not call Procore.

PyProcore does not grant access. A GC/Owner must install and authorize the
private app or DMSA, select permitted projects, and grant appropriate Read Only
tool permissions before user-written live integration code can retrieve data.
The [GC/Owner installation packet](gc-owner-installation-packet.md) provides
placeholder-based request and review documents for that human-owned process.

## Local Outputs

A mocked sync can produce normalized CSV and JSONL logs, raw per-project JSON,
JSON and Markdown summaries, polling state, an attachment metadata manifest,
and an output manifest.

Attachment availability is not guaranteed. It depends on DMSA permissions,
record visibility, and whether Procore includes usable metadata or URLs.
Phase 19B never follows or downloads those URLs.

## Plan And Validate

```bash
procore-sdk intake sample-config --output ./local/intake.json
procore-sdk intake validate-config ./local/intake.json
procore-sdk intake plan ./local/intake.json
```

The config identifies a DMSA profile reference, company, permitted projects,
selected resources, timestamp filter, output folder, state path, and optional
per-project limit. It contains no client secret or token.

## Mocked Local Sync

```bash
procore-sdk intake run-mock \
  examples/intake/intake_config.json \
  --rfis examples/intake/fake_rfis.json \
  --submittals examples/intake/fake_submittals.json
```

Preview output paths without writing:

```bash
procore-sdk intake write-mock \
  examples/intake/intake_config.json \
  --rfis examples/intake/fake_rfis.json \
  --submittals examples/intake/fake_submittals.json \
  --output-dir ./exports/intake \
  --dry-run
```

For intentional local writes, set `"dry_run": false` in the config and omit
`--dry-run`. Existing files are protected unless `--overwrite` is explicitly
supplied.

## Polling Fallback

State tracks last attempted and successful runs, per-project RFI and Submittal
timestamps, counts, and findings. This supports repeated user-scheduled polling:

```bash
procore-sdk intake state init \
  --config examples/intake/intake_config.json \
  --output ./exports/intake/state/intake_state.json
procore-sdk intake state show ./exports/intake/state/intake_state.json
```

Webhook integration may be planned later, but Phase 19B does not host a webhook
receiver or require webhooks.

## Attachment Manifest

```bash
procore-sdk intake attachment-manifest \
  examples/intake/fake_attachment_records.json
```

The manifest records candidate filenames, parent records, and URL presence. It
does not download remote attachments.

## Safety Boundaries

- Intake sync is read-only and local-output-oriented.
- The GC/Owner controls DMSA installation, project access, and permissions.
- PyProcore does not grant access or bypass Procore authorization.
- No Procore write actions are enabled.
- No approval, submission, close, delete, update, upload, or payment automation
  exists.
- Examples and tests are mocked/local and make no live Procore calls.
- No external AI/model API, MCP execution, or Procore tool execution is used.
