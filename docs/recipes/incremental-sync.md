# Incremental Sync

## What this does

Incremental sync stores a small local state file and skips RFIs or submittals
whose `updated_at` value has not changed since the last successful sync.

## When to use it

Use this for repeated local exports where you only want to rewrite changed
items.

## Before you start

You need a configured `.env` file, completed OAuth setup, and:

```bash
export PROCORE_PROJECT_ID=your_project_id
```

## Code

```python
import os
from pathlib import Path

from pyprocore.workflows import sync_rfis_to_folder

project_id = int(os.environ["PROCORE_PROJECT_ID"])

result = sync_rfis_to_folder(
    project_id,
    Path("exports/incremental-rfis"),
    incremental=True,
)

print(f"Synced: {result.synced_count}")
print(f"Skipped: {result.skipped_count}")
print(f"State: {result.state_path}")
```

## CLI Example

```bash
procore-sdk sync-rfis --project "$PROCORE_PROJECT_ID" --output exports/incremental-rfis --incremental
```

## Expected output

The first run syncs all matching items. Later runs skip unchanged items and
update the local state file after a successful non-dry-run sync.

## Common issues

- Dry runs do not write state files.
- If the state file is unreadable, PyProcore warns and performs a full sync.
- Deleting the state file makes the next run behave like the first run.
