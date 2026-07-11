# Build Enhanced RFI Package

## What this does

Builds a read-only RFI review package with the primary RFI, optional RFI
attachments, related project context, and AI-friendly review files.

## When to use it

Use this when a reviewer or AI workflow needs more than the RFI alone. The
package can include related submittals, documents, drawings, specifications,
photos, and Daily Logs using simple keyword matching.

## Before you start

Configure `.env`, complete OAuth once, and make sure your Procore user can view
the project and related tools you want to collect.

Useful environment variables:

- `PROCORE_PROJECT_ID`
- `PROCORE_COMPANY_ID`
- `PROCORE_RFI_ID`
- `PROCORE_RFI_NUMBER`
- `PROCORE_OUTPUT_DIR`
- `PROCORE_LOG_DATE`

Downloads are optional. Related matching is keyword-based, not semantic or AI
search. Some sections may fail because of permissions; the package continues by
default and records failures in `manifest.json` and `errors.json`.

## Code

```python
import os

from pyprocore.workflows import build_enhanced_rfi_package

project_id = int(os.environ["PROCORE_PROJECT_ID"])
company_id = int(os.environ["PROCORE_COMPANY_ID"])

result = build_enhanced_rfi_package(
    project_id,
    company_id=company_id,
    rfi_number=os.getenv("PROCORE_RFI_NUMBER"),
    rfi_id=int(os.environ["PROCORE_RFI_ID"]) if os.getenv("PROCORE_RFI_ID") else None,
    output_dir=os.getenv("PROCORE_OUTPUT_DIR", "rfi-package"),
    include_related=True,
    log_date=os.getenv("PROCORE_LOG_DATE"),
    max_related_items=25,
    download_files=False,
)

print(result.output_dir)
print(result.review_context_path)
```

You can also run the CLI:

```bash
procore-sdk enhanced-rfi-package \
  --project "$PROCORE_PROJECT_ID" \
  --company "$PROCORE_COMPANY_ID" \
  --rfi-number "$PROCORE_RFI_NUMBER"
```

## Expected output

You should see a folder like:

```text
rfi-package/
  manifest.json
  summary.md
  rfi.json
  rfi.md
  related/
  ai/
```

Start with `summary.md` for a human overview and `ai/review_context.md` for an
AI-ready context file.

## Common issues

- If the RFI cannot be found, confirm `PROCORE_RFI_ID` or `PROCORE_RFI_NUMBER`.
- If related sections fail, check whether your user can view those Procore tools.
- If no related items are found, add `search_terms=["keyword"]` or use
  `--search-term keyword`.
- If downloads are needed, set `download_files=True` or pass `--download-files`.
- Treat `ai/risk_flags.md` as possible review flags, not construction, legal, or
  final decision guidance.
