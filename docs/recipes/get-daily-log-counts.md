# Get Daily Log Counts

## What this does

Gets Procore Daily Log count information for one project.

## When to use it

Use this when you want to quickly see whether Daily Log activity exists before
listing specific log types such as manpower, notes, or delays.

## Before you start

Configure `.env`, complete OAuth once, and make sure the OAuth user can view the
project's Daily Log tool.

Useful environment variables:

- `PROCORE_PROJECT_ID`
- `PROCORE_COMPANY_ID`
- `PROCORE_LOG_DATE`

## Code

```python
import os

from pyprocore.services import get_daily_log_counts

project_id = int(os.environ["PROCORE_PROJECT_ID"])
company_id = int(os.environ["PROCORE_COMPANY_ID"])
log_date = os.getenv("PROCORE_LOG_DATE")

counts = get_daily_log_counts(project_id, company_id=company_id, log_date=log_date)

for count in counts:
    print(count.log_type, count.count)
```

## Expected output

You should see Daily Log type names and counts when Procore returns count data.

## Common issues

- A 403 usually means the app, company, project, or user permissions need review.
- Empty results can mean there are no Daily Logs for that date.
- Confirm production vs sandbox if the same IDs work in one environment but not another.
