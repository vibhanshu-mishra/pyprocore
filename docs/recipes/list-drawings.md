# List Drawings

## What this does

Lists drawings that the authenticated Procore user can access. Procore
organizes drawings by drawing area, so PyProcore can either list drawings from
one area or list project areas first and collect drawings from each area.

## When to use it

Use this when you need to inspect project sheets before downloading, reporting,
or preparing a downstream automation workflow.

## Before you start

Configure your `.env` file, complete OAuth once, and make sure your Procore user
has access to the project's Drawings tool.

Useful environment variables:

- `PROCORE_PROJECT_ID`
- `PROCORE_COMPANY_ID`
- `PROCORE_DRAWING_AREA_ID`
- `PROCORE_DRAWING_DISCIPLINE_ID`

## Code

```python
import os

from pyprocore.services import list_drawings

project_id = int(os.environ["PROCORE_PROJECT_ID"])
company_id_value = os.getenv("PROCORE_COMPANY_ID")
area_id_value = os.getenv("PROCORE_DRAWING_AREA_ID")

drawings = list_drawings(
    project_id,
    company_id=int(company_id_value) if company_id_value else None,
    drawing_area_id=int(area_id_value) if area_id_value else None,
    current=True,
)

for drawing in drawings:
    print(drawing.id, drawing.number, drawing.title)
```

CLI:

```bash
procore-sdk drawings --project "$PROCORE_PROJECT_ID"
procore-sdk drawings --project "$PROCORE_PROJECT_ID" --area "$PROCORE_DRAWING_AREA_ID"
procore-sdk drawing-areas --project "$PROCORE_PROJECT_ID"
procore-sdk drawing-disciplines --project "$PROCORE_PROJECT_ID"
```

## Expected output

You should see drawing IDs, numbers, and titles, or a formatted JSON list from
the CLI.

## Common issues

- If no drawings appear, list drawing areas first and confirm the project has published drawings.
- If authentication fails, run `procore-sdk auth status`.
- If a filter returns nothing, list drawings without filters first.
- A 403 means OAuth worked, but Procore rejected the project/company context. Confirm the project belongs to the company, production vs sandbox is correct, the OAuth user can access the company/project, the Drawings tool is enabled, and the user can view Drawings.
- A 404 can mean the wrong project, wrong sandbox/production API base, missing Drawings tool access, or an invalid drawing area ID.
- Use `PYTHONPATH=. python3 scripts/smoke_drawings.py --project "$PROCORE_PROJECT_ID"` to inspect the raw sandbox payload.
- `PROCORE_PROJECT_ID=352338 make smoke-drawings` also works. The Makefile sets `PYTHONPATH=.` internally for local checkout testing.
