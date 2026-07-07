# List Filtered RFIs and Submittals

## What this does

Lists RFIs or submittals for a project while passing simple filters, such as
status or updated date, to Procore as query parameters.

## When to use it

Use this when you only want a smaller set of items, such as open RFIs, pending
submittals, or items updated after a certain date.

## Before you start

You need a configured `.env` file, a completed OAuth token setup, and:

```bash
export PROCORE_PROJECT_ID=your_project_id
export PROCORE_RFI_STATUS=open
export PROCORE_SUBMITTAL_STATUS=pending
```

The status values shown here are examples. PyProcore passes them through to
Procore and lets Procore decide which values are valid for your account.

## Code

Function style:

```python
import os

from pyprocore.services import list_rfis, list_submittals

project_id = int(os.environ["PROCORE_PROJECT_ID"])

open_rfis = list_rfis(
    project_id=project_id,
    status=os.getenv("PROCORE_RFI_STATUS"),
    updated_after="2026-07-01",
)

pending_submittals = list_submittals(
    project_id=project_id,
    status=os.getenv("PROCORE_SUBMITTAL_STATUS"),
)

print(f"RFIs: {len(open_rfis)}")
print(f"Submittals: {len(pending_submittals)}")
```

Client style:

```python
import os

from pyprocore import Procore

client = Procore()
project_id = int(os.environ["PROCORE_PROJECT_ID"])

open_rfis = client.rfis.list(project_id=project_id, status="open")
pending_submittals = client.submittals.list(project_id=project_id, status="pending")

print(f"RFIs: {len(open_rfis)}")
print(f"Submittals: {len(pending_submittals)}")
```

## Expected output

You should see counts or item details for resources matching the filters that
Procore accepts.

## Common issues

- If no items are returned, try the same call without filters first.
- If Procore rejects a filter value, check the status names used by your
  Procore account.
- If you see an authentication error, run `procore-sdk auth status`.
- Date strings are passed through as query parameters. Use the format expected
  by the Procore endpoint you are calling.
