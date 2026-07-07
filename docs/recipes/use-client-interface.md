# Use the Client Interface

## What this does

Uses the object-oriented `Procore` client to access grouped services with dot
notation, such as `client.projects.list(...)` and `client.rfis.get(...)`.

## When to use it

Use this style when you want a single SDK object in your script, app, notebook,
or automation workflow. It is especially helpful when you are new to PyProcore
and want methods grouped by resource type.

## Before you start

You need a configured `.env` file and a completed OAuth token setup. To list
projects, set:

```bash
export PROCORE_COMPANY_ID=your_company_id
```

To fetch RFIs or submittals, you will also need IDs such as
`PROCORE_PROJECT_ID`, `PROCORE_RFI_ID`, or `PROCORE_SUBMITTAL_ID`.

## Code

```python
import os

from pyprocore import Procore

client = Procore()
company_id = int(os.environ["PROCORE_COMPANY_ID"])

projects = client.projects.list(company_id=company_id)

for project in projects:
    print(project.id, project.name)
```

You can use the same client for other resources:

```python
rfi = client.rfis.get(project_id=352338, rfi_id=102784)
submittals = client.submittals.list(project_id=352338)
open_rfis = client.rfis.list(project_id=352338, status="open")
pending_submittals = client.submittals.list(
    project_id=352338,
    status="pending",
)
```

## Expected output

You should see one line per project, with the project ID and project name.

## Common issues

- If `PROCORE_COMPANY_ID` is missing, set it in your shell or `.env`.
- If you see an authentication error, run `procore-sdk auth status`.
- If you see a permissions error, confirm your Procore user has access to the
  company or project.
- If a filtered list is empty, try the same list call without `status` or date
  filters first.
- The client interface is additive. The existing function style still works.
