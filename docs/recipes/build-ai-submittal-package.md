# Build an AI Submittal Package

## What this does

Builds a `WorkflowPackage` for one submittal. The package includes resolved
project and submittal identifiers, JSON-friendly metadata, and downloaded
attachment paths.

## When to use it

Use this when preparing submittal data for an internal review workflow, document
processor, or AI assistant outside the SDK.

## Before you start

You need a configured `.env` file, completed OAuth setup, and either
project/submittal IDs or human-friendly values:

```bash
export PROCORE_PROJECT_ID=your_project_id
export PROCORE_SUBMITTAL_ID=your_submittal_id
```

or:

```bash
export PROCORE_PROJECT_NAME="Project name"
export PROCORE_SUBMITTAL_NUMBER=your_submittal_number
```

## Code

```python
import os

from pyprocore.automation import AutomationInput, build_workflow_package

project_id_text = os.getenv("PROCORE_PROJECT_ID")
submittal_id_text = os.getenv("PROCORE_SUBMITTAL_ID")

package = build_workflow_package(
    AutomationInput(
        project_id=int(project_id_text) if project_id_text else None,
        project_name=os.getenv("PROCORE_PROJECT_NAME"),
        item_type="submittal",
        item_id=int(submittal_id_text) if submittal_id_text else None,
        item_number=os.getenv("PROCORE_SUBMITTAL_NUMBER"),
    )
)

print(package.title)
print(package.metadata)
print(package.attachments)
```

## Expected output

You should see the submittal title, metadata dictionary, and a list of downloaded
files if attachments were found.

## Common issues

- If project resolution is ambiguous, use `PROCORE_PROJECT_ID`.
- If the submittal number is ambiguous, use `PROCORE_SUBMITTAL_ID`.
- If you do not want downloads, pass `download_attachments=False`.
