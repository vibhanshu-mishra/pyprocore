# List Photos

## What this does

Lists Procore photos for a project or one photo album. Procore calls photos
`images` in the REST API.

## When to use it

Use this before downloading photos or finding a specific image by filename,
description, or query text.

## Before you start

Configure `.env`, complete OAuth once, and set the project ID. Set an album ID
when you want one album only.

Useful environment variables:

- `PROCORE_PROJECT_ID`
- `PROCORE_COMPANY_ID`
- `PROCORE_PHOTO_ALBUM_ID`

## Code

```python
import os

from pyprocore.services import list_photos

project_id = int(os.environ["PROCORE_PROJECT_ID"])
company_id = int(os.environ["PROCORE_COMPANY_ID"])
album_id = os.getenv("PROCORE_PHOTO_ALBUM_ID")

photos = list_photos(
    project_id,
    company_id=company_id,
    album_id=int(album_id) if album_id else None,
    sort="-created_at",
)

for photo in photos:
    print(photo.id, photo.filename or photo.name)
```

## Expected output

You should see photo IDs and filenames or names.

## Common issues

- If no photos appear, list albums first and confirm the album contains photos.
- If reverse sort does not parse in a shell, use `--sort=-created_at`.
- A 403 usually means the app, company, project, or user permissions need review.
