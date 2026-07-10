# Find a Specification Section

## What this does

Finds one specification section by number, title, or search text and returns a
typed `SpecificationSection` model.

## When to use it

Use this when a workflow knows a human-friendly section number such as
`03 3000` but does not know the Procore section ID yet.

## Before you start

Configure your `.env` file, complete OAuth once, and confirm the authenticated
user can access specification sections for the project.

Useful environment variables:

- `PROCORE_PROJECT_ID`
- `PROCORE_COMPANY_ID`
- `PROCORE_SPECIFICATION_SECTION_NUMBER`

## Code

```python
import os

from pyprocore.services import find_specification_section

project_id = int(os.environ["PROCORE_PROJECT_ID"])
company_id_value = os.getenv("PROCORE_COMPANY_ID")
section_number = os.getenv("PROCORE_SPECIFICATION_SECTION_NUMBER", "03 3000")

section = find_specification_section(
    project_id,
    number=section_number,
    company_id=int(company_id_value) if company_id_value else None,
)

print(section.id, section.number, section.title)
```

CLI:

```bash
procore-sdk find-specification-section \
  --project "$PROCORE_PROJECT_ID" \
  --number "$PROCORE_SPECIFICATION_SECTION_NUMBER"
```

## Expected output

You should see one section's ID, number, and title. If multiple sections match,
PyProcore asks you to narrow the search.

## Common issues

- If multiple sections match, search by exact number or include a more specific title.
- If nothing matches, list sections first and confirm the number formatting used by Procore.
- The SDK resolves section details through the verified list endpoint because a direct section show endpoint is still pending live verification.
- A 403 means OAuth worked, but Procore rejected the project/company context. Confirm the app is connected to the company and the user can view Specifications.
