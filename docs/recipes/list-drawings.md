# List Drawings

## What this does

Lists drawings that the authenticated Procore user can access in a project. You
can optionally filter by drawing area, discipline, or current revision status.

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

- If no drawings appear, confirm the project ID and your Drawings permissions.
- If authentication fails, run `procore-sdk auth status`.
- If a filter returns nothing, list drawings without filters first.
- Use `PYTHONPATH=. python3 scripts/smoke_drawings.py --project "$PROCORE_PROJECT_ID"` to inspect the raw sandbox payload.
