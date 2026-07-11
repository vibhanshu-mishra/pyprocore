# RFI AI Review Context

## What this does

Creates focused AI review files for one RFI, including the RFI summary, related
context summaries, suggested reviewer questions, and simple possible risk flags.

## When to use it

Use this when you want to paste or attach local context to an AI assistant for
review help without downloading every project file.

## Before you start

Configure `.env`, complete OAuth once, and set a project ID plus either an RFI
ID or RFI number.

Useful environment variables:

- `PROCORE_PROJECT_ID`
- `PROCORE_COMPANY_ID`
- `PROCORE_RFI_ID`
- `PROCORE_RFI_NUMBER`
- `PROCORE_SEARCH_TERM`
- `PROCORE_OUTPUT_DIR`

The generated files are for review assistance only. The matching is explainable
keyword matching and may miss items that use different wording.

## Code

```python
import os

from pyprocore.workflows import build_enhanced_rfi_package

project_id = int(os.environ["PROCORE_PROJECT_ID"])
company_id = int(os.environ["PROCORE_COMPANY_ID"])
search_term = os.getenv("PROCORE_SEARCH_TERM")

result = build_enhanced_rfi_package(
    project_id,
    company_id=company_id,
    rfi_number=os.getenv("PROCORE_RFI_NUMBER"),
    rfi_id=int(os.environ["PROCORE_RFI_ID"]) if os.getenv("PROCORE_RFI_ID") else None,
    output_dir=os.getenv("PROCORE_OUTPUT_DIR", "rfi-ai-review"),
    related_sections=["drawings", "specifications", "submittals"],
    search_terms=[search_term] if search_term else None,
    max_related_items=10,
    download_files=False,
)

print(result.review_context_path)
```

CLI example:

```bash
procore-sdk enhanced-rfi-package \
  --project "$PROCORE_PROJECT_ID" \
  --company "$PROCORE_COMPANY_ID" \
  --rfi-number "$PROCORE_RFI_NUMBER" \
  --related-sections drawings,specifications,submittals \
  --max-related-items 10
```

## Expected output

Look in the `ai/` folder:

- `review_context.md`
- `review_context.json`
- `questions_to_answer.md`
- `risk_flags.md`

## Common issues

- If the AI context is too broad, reduce `max_related_items` or limit
  `related_sections`.
- If related items are missing, add a specific `search_terms` value.
- If a related section fails, review `errors.json` and confirm tool permissions.
- If the RFI has no answer or attachments, that may appear in `risk_flags.md` as
  a possible review flag.
- Do not treat generated risk flags as final construction or legal conclusions.
