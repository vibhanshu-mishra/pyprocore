# Sync a Project to a Folder

## What this does

Syncs RFIs and submittals for one project into a single local folder with
trackers, manifests, summaries, item JSON, Markdown summaries, and optional
attachments.

## When to use it

Use this when you want one project-level review package for reporting, handoff,
or AI workflows.

## Before you start

You need a configured `.env` file, completed OAuth setup, and:

```bash
export PROCORE_PROJECT_ID=your_project_id
```

## Code

```python
import os
from pathlib import Path

from pyprocore.workflows import sync_project_to_folder

project_id = int(os.environ["PROCORE_PROJECT_ID"])

result = sync_project_to_folder(
    project_id,
    Path("exports/project-sync"),
    incremental=True,
)

print(f"Synced: {result.synced_count}")
print(f"Skipped: {result.skipped_count}")
print(f"Summary: {result.summary_path}")
```

## CLI Example

```bash
procore-sdk sync-project --project "$PROCORE_PROJECT_ID" --output exports/project-sync --incremental
```

## Expected output

You should see `rfis/`, `submittals/`, tracker CSVs, child manifests, a
`project_sync_manifest.json`, and a `project_sync_summary.md`.

## Common issues

- Use `--dry-run` to preview the sync without writing files.
- Use `--rfis-only` or `--submittals-only` when you only need one item type.
- Do not pass `--rfis-only` and `--submittals-only` together.
