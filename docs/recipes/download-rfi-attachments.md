# Download RFI Attachments

## What this does

Downloads files attached to the questions on one RFI.

## When to use it

Use this when you need local copies of drawings, photos, PDFs, or other files
attached to an RFI.

## Before you start

You need a configured `.env` file, completed OAuth setup, and:

```bash
export PROCORE_PROJECT_ID=your_project_id
export PROCORE_RFI_ID=your_rfi_id
export PROCORE_OUTPUT_DIR=downloads/rfi
```

`PROCORE_OUTPUT_DIR` is optional.

## Code

```python
import os
from pathlib import Path

from pyprocore.services import download_rfi_attachments

project_id = int(os.environ["PROCORE_PROJECT_ID"])
rfi_id = int(os.environ["PROCORE_RFI_ID"])
output_dir = os.getenv("PROCORE_OUTPUT_DIR")

paths = download_rfi_attachments(
    project_id,
    rfi_id,
    Path(output_dir) if output_dir else None,
)

for path in paths:
    print(path)
```

## Expected output

You should see one local path per downloaded attachment. Existing files are
skipped by default.

## Common issues

- If no files download, the RFI may not have question attachments.
- If a download fails, check `logs/errors.log`.
- If access is denied, confirm your Procore user can view the RFI and files.
