# Find a Photo

## What this does

Finds one Procore photo by ID, filename, description, or query text.

## When to use it

Use this when you know a human-friendly filename or description but not the
Procore photo ID.

## Before you start

Configure `.env`, complete OAuth once, and confirm the user can view Photos.

Useful environment variables:

- `PROCORE_PROJECT_ID`
- `PROCORE_COMPANY_ID`
- `PROCORE_PHOTO_ID`

## Code

```python
import os

from pyprocore.services import find_photo

project_id = int(os.environ["PROCORE_PROJECT_ID"])
company_id = int(os.environ["PROCORE_COMPANY_ID"])

photo = find_photo(project_id, filename="site.jpg", company_id=company_id)

print(photo.id, photo.filename, photo.description)
```

## Expected output

You should see one matching photo. Ambiguous searches raise a clear SDK error.

## Common issues

- If multiple photos match, search by photo ID or a more specific filename.
- If nothing matches, list photos first and inspect returned filenames.
- A 403 means OAuth succeeded but Procore denied the project/company context.
