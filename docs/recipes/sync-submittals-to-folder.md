# Sync Submittals to a Folder

## What this does

Creates a local folder tree for project submittals. Each submittal gets its own
folder with `item.json`, an optional Markdown summary, optional attachments, and
a project tracker CSV.

## When to use it

Use this when you need a local submittal review package for team coordination,
document checks, or AI workflows.

## Before you start

You need a configured `.env` file, completed OAuth setup, and:

```bash
export PROCORE_PROJECT_ID=your_project_id
```

Optional:

```bash
export PROCORE_SUBMITTAL_STATUS=pending
```

## Code

```python
import os
from pathlib import Path

from pyprocore.workflows import sync_submittals_to_folder

project_id = int(os.environ["PROCORE_PROJECT_ID"])
status = os.getenv("PROCORE_SUBMITTAL_STATUS")

result = sync_submittals_to_folder(
    project_id,
    Path("exports/submittal-sync"),
    status=status,
    download_attachments=True,
    dry_run=False,
)

print(f"Synced {result.item_count} submittals")
print(f"Manifest: {result.manifest_path}")
```

## Expected output

You should see folders under `exports/submittal-sync/submittals/`, plus
`exports/submittal-sync/submittal_tracker.csv` and
`exports/submittal-sync/sync_manifest.json`.
Each item folder contains `item.json`, an optional `summary.md`, and downloaded
attachments when enabled.

## Common issues

- Use `download_attachments=False` when you only need metadata.
- Existing attachment files are skipped unless you pass `overwrite=True`.
- Tracker CSV, manifest, item JSON, and Markdown summaries are regenerated on each sync.
- Use `dry_run=True` to preview folders and files without writing anything locally.
- Confirm your Procore user has access to the project submittal tool.
