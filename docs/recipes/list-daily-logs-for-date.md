# List Daily Logs For One Date

## What this does

Lists multiple Daily Log sections for one project date and groups the results by
log type.

## When to use it

Use this when building a daily project summary, preparing AI context, or
checking which Daily Log sections have entries for a date.

## Before you start

Configure `.env`, complete OAuth once, and set a project ID. You can limit the
types with a comma-separated list.

Useful environment variables:

- `PROCORE_PROJECT_ID`
- `PROCORE_COMPANY_ID`
- `PROCORE_LOG_DATE`
- `PROCORE_DAILY_LOG_TYPES`

## Code

```python
import os

from pyprocore.services import list_daily_logs_for_date

project_id = int(os.environ["PROCORE_PROJECT_ID"])
company_id = int(os.environ["PROCORE_COMPANY_ID"])
log_date = os.getenv("PROCORE_LOG_DATE")
raw_types = os.getenv("PROCORE_DAILY_LOG_TYPES", "manpower,notes,delay")
log_types = [value.strip() for value in raw_types.split(",") if value.strip()]

summary = list_daily_logs_for_date(
    project_id,
    company_id=company_id,
    log_date=log_date,
    log_types=log_types,
)

for log_type, logs in summary.logs.items():
    print(log_type, len(logs))
```

## Expected output

You should see each requested log type and the number of entries returned.

## Common issues

- Some log types can fail independently; check `summary.errors`.
- Empty groups usually mean there are no entries for that type/date.
- Confirm project/company IDs, Daily Log permissions, and production vs sandbox on 403 responses.
