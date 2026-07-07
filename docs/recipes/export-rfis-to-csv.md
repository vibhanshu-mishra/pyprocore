# Export RFIs to CSV

## What this does

Exports the RFIs you can access in one Procore project into a local CSV file.

## When to use it

Use this when you want a spreadsheet-friendly tracker for review meetings,
reporting, QA checks, or handoff to another tool.

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

from pyprocore.workflows import export_rfis_to_csv

project_id = int(os.environ["PROCORE_PROJECT_ID"])
status = os.getenv("PROCORE_RFI_STATUS")

saved_path = export_rfis_to_csv(
    project_id,
    Path("exports/rfis.csv"),
    status=status,
)

print(f"Saved RFI CSV to {saved_path}")
```

## Expected output

You should see a CSV file at `exports/rfis.csv` with one row per RFI.
Use `export_rfis_to_jsonl()` instead when another tool should process one full
typed RFI JSON object per line.

## Common issues

- If the file is empty, confirm the project has RFIs matching your filters.
- If authentication fails, run `procore-sdk auth status`.
- If the project is not found, confirm `PROCORE_PROJECT_ID` is a project ID, not a company ID.
