# List Daily Logs By Type

## What this does

Lists one Daily Log section, such as manpower, notes, delays, deliveries, or
visitors.

## When to use it

Use this when your automation only needs one Daily Log type instead of a full
daily summary.

## Before you start

Configure `.env`, complete OAuth once, and set a project ID. Set a log type with
`PROCORE_DAILY_LOG_TYPE`; the default in examples is `manpower`.

Useful environment variables:

- `PROCORE_PROJECT_ID`
- `PROCORE_COMPANY_ID`
- `PROCORE_LOG_DATE`
- `PROCORE_DAILY_LOG_TYPE`

## Code

```python
import os

from pyprocore.services import list_daily_logs

project_id = int(os.environ["PROCORE_PROJECT_ID"])
company_id = int(os.environ["PROCORE_COMPANY_ID"])
log_type = os.getenv("PROCORE_DAILY_LOG_TYPE", "manpower")
log_date = os.getenv("PROCORE_LOG_DATE")

logs = list_daily_logs(project_id, log_type, company_id=company_id, log_date=log_date)

for log in logs:
    print(log.id, log.log_date or log.date)
```

## Expected output

You should see Daily Log entry IDs and dates for the requested log type.

## Common issues

- Supported type names include `manpower`, `notes`, `delay`, `delivery`, `call`,
  `accident`, `dumpster`, `visitor`, `productivity`, and `plan_revision`.
- A typo in the log type raises a validation error with the supported values.
- Empty results often mean no entries exist for that type/date.
