# Download Submittal Attachments

## What this does

Downloads files attached to one submittal.

## When to use it

Use this when you need local copies of submittal PDFs, product data, shop
drawings, or related files.

## Before you start

You need a configured `.env` file, completed OAuth setup, and:

```bash
export PROCORE_PROJECT_ID=your_project_id
export PROCORE_SUBMITTAL_ID=your_submittal_id
export PROCORE_OUTPUT_DIR=downloads/submittal
```

`PROCORE_OUTPUT_DIR` is optional.

## Code

```python
import os
from pathlib import Path

from pyprocore.services import download_submittal_attachments

project_id = int(os.environ["PROCORE_PROJECT_ID"])
submittal_id = int(os.environ["PROCORE_SUBMITTAL_ID"])
output_dir = os.getenv("PROCORE_OUTPUT_DIR")

paths = download_submittal_attachments(
    project_id,
    submittal_id,
    Path(output_dir) if output_dir else None,
)

for path in paths:
    print(path)
```

## Expected output

You should see one local path per downloaded attachment. Existing files are
skipped by default.

## Common issues

- If no files download, the submittal may not have attachments.
- If a file already exists, PyProcore will not overwrite it by default.
- If access is denied, confirm your Procore user can view the submittal files.
