# Export Submittals to CSV

## What this does

Exports submittals from one Procore project into a local CSV tracker.

## When to use it

Use this when you need a quick submittal register for reporting, coordination,
or review preparation.

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

from pyprocore.workflows import export_submittals_to_csv

project_id = int(os.environ["PROCORE_PROJECT_ID"])
status = os.getenv("PROCORE_SUBMITTAL_STATUS")

saved_path = export_submittals_to_csv(
    project_id,
    Path("exports/submittals.csv"),
    status=status,
)

print(f"Saved submittal CSV to {saved_path}")
```

## Expected output

You should see a CSV file at `exports/submittals.csv` with one row per
submittal.
Use `export_submittals_to_jsonl()` instead when another tool should process one
full typed submittal JSON object per line.

## Common issues

- If no rows are exported, remove the status filter and try again.
- If authentication fails, run `procore-sdk auth status`.
- Confirm your Procore user has access to the project submittal tool.
