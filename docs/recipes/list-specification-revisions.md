# List Specification Revisions

## What this does

Lists specification section revisions for a project, optionally narrowed to one
specification section.

## When to use it

Use this when you need the revision IDs required for a download, audit trail, or
automation package.

## Before you start

Configure your `.env` file, complete OAuth once, and confirm your user can view
the project's Specifications tool.

Useful environment variables:

- `PROCORE_PROJECT_ID`
- `PROCORE_COMPANY_ID`
- `PROCORE_SPECIFICATION_SECTION_ID`

## Code

```python
import os

from pyprocore.services import list_specification_section_revisions

project_id = int(os.environ["PROCORE_PROJECT_ID"])
company_id_value = os.getenv("PROCORE_COMPANY_ID")
section_id_value = os.getenv("PROCORE_SPECIFICATION_SECTION_ID")

revisions = list_specification_section_revisions(
    project_id,
    company_id=int(company_id_value) if company_id_value else None,
    specification_section_id=int(section_id_value) if section_id_value else None,
    per_page=1000,
)

for revision in revisions:
    print(revision.id, revision.specification_section_id, revision.revision_number)
```

CLI:

```bash
procore-sdk specification-revisions --project "$PROCORE_PROJECT_ID"
procore-sdk specification-revisions \
  --project "$PROCORE_PROJECT_ID" \
  --section "$PROCORE_SPECIFICATION_SECTION_ID" \
  --per-page 1000
```

## Expected output

You should see revision IDs and revision numbers, or a formatted JSON list from
the CLI.

## Common issues

- If no revisions appear, list sections first and confirm the section has published revisions.
- If authentication fails, run `procore-sdk auth refresh`.
- A 403 means OAuth worked, but Procore rejected the project/company context. Confirm the project belongs to the company, the app is connected to that company, production vs sandbox is correct, and the user can view Specifications.
- Use `PROCORE_PROJECT_ID=352338 make smoke-specifications` to inspect live payloads.
