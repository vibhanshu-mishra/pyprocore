# List Projects

## What this does

Lists the Procore projects available for a company. The result is a list of
typed `Project` models.

## When to use it

Use this when you know a company ID and want to see which projects your Procore
account can access.

## Before you start

You need a configured `.env` file, a completed OAuth token setup, and:

```bash
export PROCORE_COMPANY_ID=your_company_id
```

## Code

Function style:

```python
import os

from pyprocore.services import list_projects

company_id = int(os.environ["PROCORE_COMPANY_ID"])
projects = list_projects(company_id)

for project in projects:
    print(project.id, project.name)
```

Client style:

```python
import os

from pyprocore import Procore

company_id = int(os.environ["PROCORE_COMPANY_ID"])
projects = Procore().projects.list(company_id=company_id)

for project in projects:
    print(project.id, project.name)
```

## Expected output

You should see one line per project, with the project ID and project name.

## Common issues

- If `PROCORE_COMPANY_ID` is missing, set it in your shell or `.env`.
- If you see an authentication error, complete OAuth again.
- If the list is empty, confirm your Procore user has access to that company.
