# Sync RFIs to a Folder

## What this does

Creates a local folder tree for project RFIs. Each RFI gets its own folder with
`item.json`, an optional Markdown summary, optional attachments, and a project
tracker CSV.

## When to use it

Use this when you want a local review package for coordination, offline
inspection, or AI workflows.

## Before you start

You need a configured `.env` file, completed OAuth setup, and:

```bash
export PROCORE_PROJECT_ID=your_project_id
```

Optional:

```bash
export PROCORE_RFI_STATUS=open
```

## Code

```python
import os
from pathlib import Path

from pyprocore.workflows import sync_rfis_to_folder

project_id = int(os.environ["PROCORE_PROJECT_ID"])
status = os.getenv("PROCORE_RFI_STATUS")

result = sync_rfis_to_folder(
    project_id,
    Path("exports/rfi-sync"),
    status=status,
    download_attachments=True,
    dry_run=False,
)

print(f"Synced {result.item_count} RFIs")
print(f"Manifest: {result.manifest_path}")
```

## Expected output

You should see folders under `exports/rfi-sync/rfis/`, plus
`exports/rfi-sync/rfi_tracker.csv` and `exports/rfi-sync/sync_manifest.json`.
Each item folder contains `item.json`, an optional `summary.md`, and downloaded
attachments when enabled.

## Common issues

- If downloads take a while, the project may have large attachment files.
- Use `download_attachments=False` when you only need metadata.
- Existing attachment files are skipped unless you pass `overwrite=True`.
- Tracker CSV, manifest, item JSON, and Markdown summaries are regenerated on each sync.
- Use `dry_run=True` to preview folders and files without writing anything locally.
