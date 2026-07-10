# List Documents

## What this does

Lists documents that the authenticated Procore user can access in a project. PyProcore keeps this as a document-friendly helper, but internally Procore exposes these resources through Project Folders and Files endpoints.

## When to use it

Use this when you need to inspect project files before downloading or syncing them for automation, reporting, or AI workflows.

## Before you start

Configure your `.env` file, complete OAuth once, and make sure your Procore user has access to the project Documents tool.

Useful environment variables:

- `PROCORE_PROJECT_ID`
- `PROCORE_DOCUMENT_FOLDER_ID`

## Code

```python
import os

from pyprocore.services import list_documents

project_id = int(os.environ["PROCORE_PROJECT_ID"])
folder_id_value = os.getenv("PROCORE_DOCUMENT_FOLDER_ID")
folder_id = int(folder_id_value) if folder_id_value else None

documents = list_documents(project_id, folder_id=folder_id)
all_documents = list_documents(project_id, recursive=True)

for document in documents:
    label = document.filename or document.file_name or document.name
    print(document.id, label)
```

CLI:

```bash
procore-sdk documents --project "$PROCORE_PROJECT_ID"
procore-sdk documents --project "$PROCORE_PROJECT_ID" --folder "$PROCORE_DOCUMENT_FOLDER_ID"
procore-sdk documents --project "$PROCORE_PROJECT_ID" --recursive
```

## Expected output

You should see document IDs and names or a formatted JSON list from the CLI.

## Common issues

- If no documents appear, confirm the project ID and your Procore permissions.
- If authentication fails, run `procore-sdk auth status`.
- If a folder filter returns nothing, try listing documents without `--folder` first.
- Use `python3 scripts/smoke_documents.py --project "$PROCORE_PROJECT_ID"` to inspect the raw folder/file payload in a sandbox.
