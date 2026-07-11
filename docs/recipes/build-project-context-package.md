# Build Project Context Package

## What this does

Builds a read-only local folder of project information from Procore, including
JSON files, JSONL files, Markdown summaries, and a manifest.

## When to use it

Use this when preparing project data for AI review, audits, handoff workflows,
or local analysis.

## Before you start

Configure `.env`, complete OAuth once, and confirm the OAuth user can view the
project tools you want to export.

Useful environment variables:

- `PROCORE_PROJECT_ID`
- `PROCORE_COMPANY_ID`
- `PROCORE_OUTPUT_DIR`

## Code

```python
import os

from pyprocore.workflows import build_project_context_package

project_id = int(os.environ["PROCORE_PROJECT_ID"])
company_id = int(os.environ["PROCORE_COMPANY_ID"])

result = build_project_context_package(
    project_id,
    company_id=company_id,
    output_dir="project-context",
    max_items=100,
)

print(result.summary_path)
print(result.manifest_path)
```

## Expected output

You should see a `project-context/` folder with `manifest.json`, `summary.md`,
and section folders for the tools PyProcore could access.

## Common issues

- Some sections may fail due to permissions; the package continues by default.
- File downloads are off by default. Pass `download_files=True` only when needed.
- A 403 usually means the app, company, project, environment, or user permissions need review.
