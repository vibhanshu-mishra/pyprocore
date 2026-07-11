# Project Context For AI Review

## What this does

Creates a local folder that AI tools can inspect without needing direct Procore
access. The package favors structured JSON plus compact Markdown summaries.

## When to use it

Use this before asking an AI assistant to summarize project activity, review
open items, compare RFIs and submittals, or prepare a project status brief.

## Before you start

Configure `.env`, complete OAuth once, and decide which sections are useful.
Keep downloads off unless the review needs the actual files.

Useful environment variables:

- `PROCORE_PROJECT_ID`
- `PROCORE_COMPANY_ID`
- `PROCORE_OUTPUT_DIR`

## Code

```python
import os

from pyprocore.workflows import build_project_context_package

result = build_project_context_package(
    int(os.environ["PROCORE_PROJECT_ID"]),
    company_id=int(os.environ["PROCORE_COMPANY_ID"]),
    output_dir=os.getenv("PROCORE_OUTPUT_DIR", "project-context-ai"),
    include=["project", "rfis", "submittals", "documents", "daily_logs"],
    max_items=100,
)

print(f"Give this folder to your AI workflow: {result.output_dir}")
```

## Expected output

You should see `summary.md` for a quick overview and `manifest.json` describing
what succeeded, failed, and where each local file was written.

## Common issues

- AI tools should read `summary.md` first, then follow local JSON references.
- Permissions can vary by Procore tool. Failed sections are normal during setup.
- Large projects should use `include`, `exclude`, and `max_items` to stay manageable.
