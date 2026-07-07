# Export RFI JSON

## What this does

Fetches one RFI and prints its typed Pydantic model as JSON.

## When to use it

Use this when you want to inspect RFI data, save it for debugging, or pass it to
another internal tool.

## Before you start

You need a configured `.env` file, completed OAuth setup, and:

```bash
export PROCORE_PROJECT_ID=your_project_id
export PROCORE_RFI_ID=your_rfi_id
```

## Code

```python
import os

from pyprocore.services import get_rfi

project_id = int(os.environ["PROCORE_PROJECT_ID"])
rfi_id = int(os.environ["PROCORE_RFI_ID"])

rfi = get_rfi(project_id, rfi_id)
print(rfi.model_dump_json(indent=2))
```

## Expected output

You should see formatted JSON for the RFI, including nested questions and
attachments when Procore returns them.

## Common issues

- If the RFI is not found, confirm the RFI belongs to the project ID.
- If JSON is missing fields, Procore may not return those fields for that item.
- Do not paste exported JSON into public issues if it contains project data.
