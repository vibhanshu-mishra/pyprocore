# List Photo Albums

## What this does

Lists Procore photo albums for a project. Procore calls these albums
`image_categories` in the REST API.

## When to use it

Use this when you want to find the album ID before listing or downloading
photos.

## Before you start

Configure `.env`, complete OAuth once, and confirm your user can view the
project's Photos tool.

Useful environment variables:

- `PROCORE_PROJECT_ID`
- `PROCORE_COMPANY_ID`

## Code

```python
import os

from pyprocore.services import list_photo_albums

project_id = int(os.environ["PROCORE_PROJECT_ID"])
company_id = int(os.environ["PROCORE_COMPANY_ID"])

albums = list_photo_albums(project_id, company_id=company_id)

for album in albums:
    print(album.id, album.name)
```

## Expected output

You should see album IDs and names.

## Common issues

- A 403 means OAuth worked, but Procore rejected the project/company context.
- Confirm the app is connected to the company.
- Confirm the Photos tool is enabled and the user has permission to view it.
