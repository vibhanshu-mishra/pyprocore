# Download a Document

## What this does

Downloads one Procore file/document to a local folder using the SDK's existing safe, streaming file downloader.

## When to use it

Use this when you already know the document ID and want a local copy for review, processing, or an automation workflow.

## Before you start

Configure your `.env` file, complete OAuth once, and make sure the document payload includes a URL or download URL. Some Procore environments may require a separate secure file access step before a direct download URL is available.

Useful environment variables:

- `PROCORE_PROJECT_ID`
- `PROCORE_DOCUMENT_ID`
- `PROCORE_OUTPUT_DIR`

## Code

```python
import os
from pathlib import Path

from pyprocore.services import download_document

project_id = int(os.environ["PROCORE_PROJECT_ID"])
document_id = int(os.environ["PROCORE_DOCUMENT_ID"])
output_dir = Path(os.getenv("PROCORE_OUTPUT_DIR", "downloads/documents"))

saved_path = download_document(project_id, document_id, output_dir=output_dir)

print(f"Saved to: {saved_path}")
```

CLI:

```bash
procore-sdk download-document \
  --project "$PROCORE_PROJECT_ID" \
  --id "$PROCORE_DOCUMENT_ID" \
  --output ./documents
```

## Expected output

The SDK prints the local path where the document was saved.

## Common issues

- If the SDK says the document has no download URL, inspect the document payload with `procore-sdk document`.
- Run `PYTHONPATH=. python3 scripts/smoke_documents.py --project "$PROCORE_PROJECT_ID" --folder "$PROCORE_DOCUMENT_FOLDER_ID"` to inspect whether Procore is returning `url` or `download_url`.
- `PROCORE_PROJECT_ID=352338 make smoke-documents` works too. The Makefile sets `PYTHONPATH=.` internally and can also use `PROCORE_DOCUMENT_FOLDER_ID`.
- If the file already exists, it is skipped unless you pass `--overwrite`.
- If authentication fails, run `procore-sdk auth refresh`.
