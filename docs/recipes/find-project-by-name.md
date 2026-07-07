# Find Project by Name

## What this does

Finds one project using a human-friendly name or project number instead of a
project ID.

## When to use it

Use this when you know a project name, but do not want to manually look up the
project ID in Procore.

## Before you start

You need a configured `.env` file, completed OAuth setup, and either:

```bash
export PROCORE_PROJECT_NAME="Project name"
```

or:

```bash
export PROCORE_PROJECT_NUMBER="Project number"
```

Set `PROCORE_COMPANY_ID` if your `.env` does not already contain the right
company ID.

## Code

```python
import os

from pyprocore.services import find_project

project_name = os.getenv("PROCORE_PROJECT_NAME")
project_number = os.getenv("PROCORE_PROJECT_NUMBER")
company_id_text = os.getenv("PROCORE_COMPANY_ID")
company_id = int(company_id_text) if company_id_text else None

project = find_project(project_name, number=project_number, company_id=company_id)
print(project.id, project.name)
```

## Expected output

You should see the matching project ID and name.

## Common issues

- If more than one project matches, use a more specific name or project number.
- If no project matches, check spelling and company access.
- If the company ID is wrong, the resolver may search the wrong project list.
