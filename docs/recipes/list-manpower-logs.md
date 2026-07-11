# List Manpower Logs

## What this does

Lists manpower Daily Log entries for one Procore project.

## When to use it

Use this for staffing reports, daily summaries, or AI workflows that need labor
activity by date.

## Before you start

Configure `.env`, complete OAuth once, and confirm the user can view Daily Logs.

Useful environment variables:

- `PROCORE_PROJECT_ID`
- `PROCORE_COMPANY_ID`
- `PROCORE_LOG_DATE`

## Code

```python
import os

from pyprocore.services import list_manpower_logs

project_id = int(os.environ["PROCORE_PROJECT_ID"])
company_id = int(os.environ["PROCORE_COMPANY_ID"])
log_date = os.getenv("PROCORE_LOG_DATE")

logs = list_manpower_logs(project_id, company_id=company_id, log_date=log_date)

for log in logs:
    print(log.id, log.description or log.notes or log.comments)
```

## Expected output

You should see manpower log IDs and available descriptive text.

## Common issues

- Manpower fields vary by account configuration, so inspect the typed model JSON
  if a field is blank.
- If no entries appear, try a different `PROCORE_LOG_DATE`.
- A 403 usually means the user can authenticate but cannot view this project or tool.
