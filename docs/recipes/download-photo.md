# Download a Photo

## What this does

Downloads one Procore photo when the image payload contains a full-size URL.

## When to use it

Use this when you know the Procore photo ID and want a local file for review,
reporting, or AI processing.

## Before you start

Configure `.env`, complete OAuth once, and confirm the user can view and download
Photos.

Useful environment variables:

- `PROCORE_PROJECT_ID`
- `PROCORE_COMPANY_ID`
- `PROCORE_PHOTO_ID`
- `PROCORE_OUTPUT_DIR`

## Code

```python
import os
from pathlib import Path

from pyprocore.services import download_photo

project_id = int(os.environ["PROCORE_PROJECT_ID"])
company_id = int(os.environ["PROCORE_COMPANY_ID"])
photo_id = int(os.environ["PROCORE_PHOTO_ID"])
output_dir = Path(os.getenv("PROCORE_OUTPUT_DIR", "downloads/photos"))

saved_path = download_photo(project_id, photo_id, output_dir=output_dir, company_id=company_id)

print(saved_path)
```

## Expected output

The SDK prints the saved local path.

## Common issues

- If no URL is found, Procore did not include a downloadable URL in the payload.
- The SDK does not use thumbnail URLs for full-size downloads unless no better URL exists.
- Existing files are skipped unless `overwrite=True`.
