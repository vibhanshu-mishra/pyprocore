# List Specification Sections

## What this does

Lists specification sections for a Procore project. You can optionally filter by
specification set, specification area, division, and sort order.

## When to use it

Use this before building reports, searching for a section by number, or finding
the section whose revisions you want to inspect.

## Before you start

Configure your `.env` file, complete OAuth once, and confirm the authenticated
user can access the project's Specifications tool.

Useful environment variables:

- `PROCORE_PROJECT_ID`
- `PROCORE_COMPANY_ID`
- `PROCORE_SPECIFICATION_SET_ID`
- `PROCORE_SPECIFICATION_AREA_ID`
- `PROCORE_SPECIFICATION_DIVISION_ID`

## Code

```python
import os

from pyprocore.services import list_specification_sections

project_id = int(os.environ["PROCORE_PROJECT_ID"])
company_id_value = os.getenv("PROCORE_COMPANY_ID")
set_id_value = os.getenv("PROCORE_SPECIFICATION_SET_ID")

sections = list_specification_sections(
    project_id,
    company_id=int(company_id_value) if company_id_value else None,
    specification_set_id=int(set_id_value) if set_id_value else None,
    sort="number",
)

for section in sections:
    print(section.id, section.number, section.title)
```

CLI:

```bash
procore-sdk specification-sections --project "$PROCORE_PROJECT_ID" --sort number
procore-sdk specification-sections \
  --project "$PROCORE_PROJECT_ID" \
  --specification-set-id "$PROCORE_SPECIFICATION_SET_ID"
```

## Expected output

You should see section IDs, numbers, and titles, or a formatted JSON list from
the CLI.

## Common issues

- If no sections appear, confirm the Specifications tool is enabled and populated.
- If a filter returns nothing, list sections without filters first.
- A 403 means OAuth worked, but Procore rejected the project/company context. Confirm the project belongs to the company, the app is connected to that company, production vs sandbox is correct, and the user can view Specifications.
- A 404 can mean the wrong project, wrong API environment, missing tool access, or an endpoint/version mismatch.
- Use `PROCORE_PROJECT_ID=352338 make smoke-specifications` to inspect the raw response shape.
