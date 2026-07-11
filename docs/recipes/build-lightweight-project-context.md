# Build Lightweight Project Context

## What this does

Builds a smaller context package with only selected sections.

## When to use it

Use this when you want a quick AI-ready package for RFIs, submittals, and Daily
Logs without collecting heavier project tools.

## Before you start

Configure `.env`, complete OAuth once, and set a project ID. Add `PROCORE_LOG_DATE`
when you want Daily Log entries for one day.

Useful environment variables:

- `PROCORE_PROJECT_ID`
- `PROCORE_COMPANY_ID`
- `PROCORE_LOG_DATE`

## Code

```python
import os

from pyprocore.workflows import build_project_context_package

project_id = int(os.environ["PROCORE_PROJECT_ID"])
company_id = int(os.environ["PROCORE_COMPANY_ID"])

result = build_project_context_package(
    project_id,
    company_id=company_id,
    output_dir="project-context-light",
    include=["rfis", "submittals", "daily_logs"],
    log_date=os.getenv("PROCORE_LOG_DATE"),
    max_items=25,
)

print(result.output_dir)
```

## Expected output

You should see a smaller package with only the requested sections.

## Common issues

- Use `exclude=["photos", "documents"]` when starting from the default section set.
- If Daily Logs are empty, set `PROCORE_LOG_DATE` to a date with entries.
- If a section fails, check `errors.json` and `manifest.json`.
