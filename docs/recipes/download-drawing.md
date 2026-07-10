# Download a Drawing

## What this does

Downloads one Procore drawing to a local folder when the drawing payload includes
a direct `url` or `download_url`.

## When to use it

Use this when you already know the drawing ID and want a local PDF or file for
review, automation, or AI-assisted processing.

## Before you start

Configure your `.env` file, complete OAuth once, and confirm that your Procore
environment returns a direct drawing URL. Some Procore Drawings setups may
require a separate export or file access step before a direct download URL is
available.

Useful environment variables:

- `PROCORE_PROJECT_ID`
- `PROCORE_DRAWING_ID`
- `PROCORE_COMPANY_ID`
- `PROCORE_OUTPUT_DIR`

## Code

```python
import os
from pathlib import Path

from pyprocore.services import download_drawing

project_id = int(os.environ["PROCORE_PROJECT_ID"])
drawing_id = int(os.environ["PROCORE_DRAWING_ID"])
company_id_value = os.getenv("PROCORE_COMPANY_ID")
output_dir = Path(os.getenv("PROCORE_OUTPUT_DIR", "downloads/drawings"))

saved_path = download_drawing(
    project_id,
    drawing_id,
    output_dir=output_dir,
    company_id=int(company_id_value) if company_id_value else None,
)

print(f"Saved to: {saved_path}")
```

CLI:

```bash
procore-sdk download-drawing \
  --project "$PROCORE_PROJECT_ID" \
  --id "$PROCORE_DRAWING_ID" \
  --output ./drawings
```

## Expected output

The SDK prints the local path where the drawing was saved.

## Common issues

- If the SDK says the drawing has no download URL, inspect the payload with `procore-sdk drawing`.
- Run `PYTHONPATH=. python3 scripts/smoke_drawings.py --project "$PROCORE_PROJECT_ID" --drawing "$PROCORE_DRAWING_ID"` to inspect whether Procore is returning `url` or `download_url`.
- If the file already exists, it is skipped unless you pass `--overwrite`.
- If authentication fails, run `procore-sdk auth refresh`.
