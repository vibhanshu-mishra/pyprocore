# Sync Documents to a Folder

## What this does

Syncs project documents into a local folder, writes document metadata, creates a tracker CSV, and records a JSON manifest. Internally this uses Procore's Project Folders and Files endpoint structure.

## When to use it

Use this when you want a local working set of Procore Documents for search, review, reporting, or AI workflows.

## Before you start

Configure your `.env` file, complete OAuth once, and make sure your Procore user has Documents access for the project.

Useful environment variables:

- `PROCORE_PROJECT_ID`
- `PROCORE_DOCUMENT_FOLDER_ID`
- `PROCORE_OUTPUT_DIR`

## Code

```python
import os
from pathlib import Path

from pyprocore.workflows import sync_documents_to_folder

project_id = int(os.environ["PROCORE_PROJECT_ID"])
folder_id_value = os.getenv("PROCORE_DOCUMENT_FOLDER_ID")
folder_id = int(folder_id_value) if folder_id_value else None
output_dir = Path(os.getenv("PROCORE_OUTPUT_DIR", "downloads/project-documents"))

result = sync_documents_to_folder(
    project_id,
    output_dir,
    folder_id=folder_id,
    incremental=True,
    recursive=True,
)

print(f"Synced: {result.synced_count}")
print(f"Skipped: {result.skipped_count}")
print(f"Manifest: {result.manifest_path}")
```

CLI:

```bash
procore-sdk sync-documents --project "$PROCORE_PROJECT_ID" --output ./documents
procore-sdk sync-documents --project "$PROCORE_PROJECT_ID" --output ./documents --incremental
procore-sdk sync-documents --project "$PROCORE_PROJECT_ID" --output ./documents --dry-run
procore-sdk sync-documents --project "$PROCORE_PROJECT_ID" --output ./documents --recursive
```

## Expected output

You should see a sync summary. The output folder contains document folders, `document_tracker.csv`, `document_sync_manifest.json`, and `document_sync_summary.md`.

## Common issues

- Use `--dry-run` first if you want to preview the sync.
- Use `--incremental` after the first sync to skip unchanged documents.
- Use `--recursive` when you want PyProcore to traverse child folders returned by Procore.
- Use `--overwrite` only when you intentionally want to replace local files.
- If downloads fail because no URL is present, inspect the raw payload with `scripts/smoke_documents.py`.
