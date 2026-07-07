# Build an AI RFI Package

## What this does

Builds a `WorkflowPackage` for one RFI. The package includes resolved project
and RFI identifiers, JSON-friendly metadata, and downloaded attachment paths.

## When to use it

Use this when preparing RFI data for an internal review workflow, document
processor, or AI assistant outside the SDK.

## Before you start

You need a configured `.env` file, completed OAuth setup, and either project/RFI
IDs or human-friendly values:

```bash
export PROCORE_PROJECT_ID=your_project_id
export PROCORE_RFI_ID=your_rfi_id
```

or:

```bash
export PROCORE_PROJECT_NAME="Project name"
export PROCORE_RFI_NUMBER=your_rfi_number
```

## Code

```python
import os

from pyprocore.automation import AutomationInput, build_workflow_package

project_id_text = os.getenv("PROCORE_PROJECT_ID")
rfi_id_text = os.getenv("PROCORE_RFI_ID")

package = build_workflow_package(
    AutomationInput(
        project_id=int(project_id_text) if project_id_text else None,
        project_name=os.getenv("PROCORE_PROJECT_NAME"),
        item_type="rfi",
        item_id=int(rfi_id_text) if rfi_id_text else None,
        item_number=os.getenv("PROCORE_RFI_NUMBER"),
    )
)

print(package.title)
print(package.metadata)
print(package.attachments)
```

## Expected output

You should see the RFI title, metadata dictionary, and a list of downloaded
files if attachments were found.

## Common issues

- If project resolution is ambiguous, use `PROCORE_PROJECT_ID`.
- If the RFI number is ambiguous, use `PROCORE_RFI_ID`.
- If you do not want downloads, pass `download_attachments=False`.
