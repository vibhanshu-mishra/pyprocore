# Download a Specification Revision

## What this does

Downloads one specification section revision to a local folder. PyProcore first
requests Procore's revision download metadata, then streams the returned URL to
disk.

## When to use it

Use this when you already know a specification revision ID and need a local PDF
for review, archival, or AI-assisted processing.

## Before you start

Configure your `.env` file, complete OAuth once, and confirm your user can view
and download Specifications for the project.

Useful environment variables:

- `PROCORE_PROJECT_ID`
- `PROCORE_COMPANY_ID`
- `PROCORE_SPECIFICATION_REVISION_ID`
- `PROCORE_OUTPUT_DIR`

## Code

```python
import os
from pathlib import Path

from pyprocore.services import download_specification_section_revision

project_id = int(os.environ["PROCORE_PROJECT_ID"])
revision_id = int(os.environ["PROCORE_SPECIFICATION_REVISION_ID"])
company_id_value = os.getenv("PROCORE_COMPANY_ID")
output_dir = Path(os.getenv("PROCORE_OUTPUT_DIR", "downloads/specifications"))

saved_path = download_specification_section_revision(
    project_id,
    revision_id,
    output_dir=output_dir,
    company_id=int(company_id_value) if company_id_value else None,
)

print(f"Saved to: {saved_path}")
```

CLI:

```bash
procore-sdk download-specification-revision \
  --project "$PROCORE_PROJECT_ID" \
  --revision "$PROCORE_SPECIFICATION_REVISION_ID" \
  --output-dir ./specifications
```

## Expected output

The SDK prints the local path where the revision PDF was saved.

## Common issues

- If the SDK says no download URL was returned, inspect the revision with `procore-sdk specification-revision`.
- If the file already exists, it is skipped unless you pass `--overwrite`.
- A 403 means OAuth worked, but Procore rejected the project/company context. Confirm the project belongs to the company, the app is connected to that company, production vs sandbox is correct, and the user can download Specifications.
- A 404 can mean the wrong project, wrong revision ID, wrong API environment, or missing Specifications tool access.
- Use `PYTHONPATH=. python3 scripts/smoke_specifications.py --project "$PROCORE_PROJECT_ID" --revision "$PROCORE_SPECIFICATION_REVISION_ID"` to inspect payloads without downloading.
