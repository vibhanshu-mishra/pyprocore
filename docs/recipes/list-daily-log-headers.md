# List Daily Log Headers

## What this does

Lists Daily Log headers for a Procore project.

## When to use it

Use headers when you need date-level Daily Log information before reading
individual log sections.

## Before you start

Configure `.env`, complete OAuth once, and set the project ID. Add a log date
when you want a single day.

Useful environment variables:

- `PROCORE_PROJECT_ID`
- `PROCORE_COMPANY_ID`
- `PROCORE_LOG_DATE`

## Code

```python
import os

from pyprocore.services import list_daily_log_headers

project_id = int(os.environ["PROCORE_PROJECT_ID"])
company_id = int(os.environ["PROCORE_COMPANY_ID"])
log_date = os.getenv("PROCORE_LOG_DATE")

headers = list_daily_log_headers(project_id, company_id=company_id, log_date=log_date)

for header in headers:
    print(header.id, header.log_date or header.date)
```

## Expected output

You should see Daily Log header IDs and dates.

## Common issues

- If no headers appear, confirm the Daily Log tool is enabled for the project.
- If a specific date is empty, try removing `PROCORE_LOG_DATE`.
- A 403 usually means the OAuth user or app cannot access this project/company context.
