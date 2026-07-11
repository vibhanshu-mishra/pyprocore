# Build Enhanced Submittal Package

## What this does

Builds a read-only submittal review package with the primary submittal, optional
attachments, related project context, and AI-friendly review files.

## When to use it

Use this when a reviewer or AI workflow needs more than the submittal alone.
The package can include related RFIs, documents, drawings, specifications,
photos, and Daily Logs using simple keyword matching.

## Before you start

Configure `.env`, complete OAuth once, and make sure your Procore user can view
the project and related tools you want to collect.

Useful environment variables:

- `PROCORE_PROJECT_ID`
- `PROCORE_COMPANY_ID`
- `PROCORE_SUBMITTAL_ID`
- `PROCORE_SUBMITTAL_NUMBER`
- `PROCORE_OUTPUT_DIR`
- `PROCORE_LOG_DATE`

Downloads are optional. Related matching is keyword-based, not semantic or AI
search. Some sections may fail because of permissions; the package continues by
default and records failures in `manifest.json` and `errors.json`.

## Code

```python
import os

from pyprocore.workflows import build_enhanced_submittal_package

project_id = int(os.environ["PROCORE_PROJECT_ID"])
company_id = int(os.environ["PROCORE_COMPANY_ID"])

result = build_enhanced_submittal_package(
    project_id,
    company_id=company_id,
    submittal_number=os.getenv("PROCORE_SUBMITTAL_NUMBER"),
    submittal_id=(
        int(os.environ["PROCORE_SUBMITTAL_ID"])
        if os.getenv("PROCORE_SUBMITTAL_ID")
        else None
    ),
    output_dir=os.getenv("PROCORE_OUTPUT_DIR", "enhanced-submittal-package"),
    include_related=True,
    log_date=os.getenv("PROCORE_LOG_DATE"),
    max_related_items=25,
    download_files=False,
)

print(result.output_dir)
print(result.review_context_path)
print(result.approval_review_path)
```

You can also run the CLI:

```bash
procore-sdk enhanced-submittal-package \
  --project "$PROCORE_PROJECT_ID" \
  --company "$PROCORE_COMPANY_ID" \
  --submittal-number "$PROCORE_SUBMITTAL_NUMBER"
```

## Expected output

You should see a folder like:

```text
enhanced-submittal-package/
  manifest.json
  summary.md
  submittal.json
  submittal.md
  related/
  ai/
```

Start with `summary.md` for a human overview, `ai/review_context.md` for AI
context, and `ai/approval_review.md` for structured human review assistance.

## Common issues

- If the submittal cannot be found, confirm `PROCORE_SUBMITTAL_ID` or
  `PROCORE_SUBMITTAL_NUMBER`.
- If related sections fail, check whether your user can view those Procore tools.
- If no related items are found, add `search_terms=["keyword"]` or use
  `--search-term keyword`.
- If downloads are needed, set `download_files=True` or pass `--download-files`.
- Treat `ai/risk_flags.md` as possible review flags, not construction, legal, or
  final decision guidance.
- The SDK does not approve, reject, or revise submittals.
