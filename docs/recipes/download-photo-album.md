# Download a Photo Album

## What this does

Downloads photos from one Procore photo album and returns a summary with
downloaded files, skipped files, and per-photo errors.

## When to use it

Use this when you need a local folder of project photos for review or downstream
automation.

## Before you start

Configure `.env`, complete OAuth once, and set an album ID. Use a limit while
testing.

Useful environment variables:

- `PROCORE_PROJECT_ID`
- `PROCORE_COMPANY_ID`
- `PROCORE_PHOTO_ALBUM_ID`
- `PROCORE_PHOTO_LIMIT`
- `PROCORE_OUTPUT_DIR`

## Code

```python
import os
from pathlib import Path

from pyprocore.services import download_photo_album

project_id = int(os.environ["PROCORE_PROJECT_ID"])
company_id = int(os.environ["PROCORE_COMPANY_ID"])
album_id = int(os.environ["PROCORE_PHOTO_ALBUM_ID"])
limit = os.getenv("PROCORE_PHOTO_LIMIT")
output_dir = Path(os.getenv("PROCORE_OUTPUT_DIR", "downloads/photos"))

result = download_photo_album(
    project_id,
    album_id,
    output_dir=output_dir,
    company_id=company_id,
    limit=int(limit) if limit else None,
)

print(result.model_dump())
```

## Expected output

You should see counts for requested, downloaded, skipped, and errored photos.

## Common issues

- One missing URL does not stop the whole album download; it is recorded as an error.
- A 403 usually means the app is not connected to the company or the user lacks Photos permissions.
- Use `make smoke-photos` to inspect live payloads before a large album download.
