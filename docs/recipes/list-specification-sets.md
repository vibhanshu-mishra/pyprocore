# List Specification Sets

## What this does

Lists specification sets for a Procore project using the company/project-scoped
Specifications API.

## When to use it

Use this when you need to understand how a project's specifications are grouped
before listing sections, revisions, or downloads.

## Before you start

Configure your `.env` file, complete OAuth once, and make sure your Procore user
has access to the project's Specifications tool.

Useful environment variables:

- `PROCORE_PROJECT_ID`
- `PROCORE_COMPANY_ID`

## Code

```python
import os

from pyprocore.services import list_specification_sets

project_id = int(os.environ["PROCORE_PROJECT_ID"])
company_id_value = os.getenv("PROCORE_COMPANY_ID")

sets = list_specification_sets(
    project_id,
    company_id=int(company_id_value) if company_id_value else None,
)

for specification_set in sets:
    print(specification_set.id, specification_set.name)
```

CLI:

```bash
procore-sdk specification-sets --project "$PROCORE_PROJECT_ID"
procore-sdk specification-sets --project "$PROCORE_PROJECT_ID" --company "$PROCORE_COMPANY_ID"
```

## Expected output

You should see specification set IDs and names, or a formatted JSON list from
the CLI.

## Common issues

- If no sets appear, the project may not use specification sets or your user may not have access.
- If authentication fails, run `procore-sdk auth status`.
- A 403 means OAuth worked, but Procore rejected the project/company context. Confirm the project belongs to the company, the app is connected to that company, production vs sandbox is correct, and the user can view Specifications.
- Use `PROCORE_PROJECT_ID=352338 make smoke-specifications` to inspect live payloads. The Makefile sets `PYTHONPATH=.` internally.
