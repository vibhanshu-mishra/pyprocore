# Build an AI Review Export

## What this does

Builds a local AI-friendly review folder from an existing PyProcore package.
It reads local Markdown, JSON, JSONL, and text files, creates a source index,
splits large files into deterministic chunks, and writes safe prompts and
review checklists.

## When to use it

Use this after creating an enhanced RFI package, enhanced submittal package, or
project context package and you want a clean folder to attach to an AI review
workflow.

## Before you start

Create a local package folder first. This recipe does not require Procore
credentials at runtime because it only reads local files.

Useful environment variables:

- `PACKAGE_DIR`
- `AI_EXPORT_OUTPUT_DIR`

## Code

```python
import os
from pathlib import Path

from pyprocore.workflows import build_ai_review_export

package_dir = Path(os.environ["PACKAGE_DIR"])
output_dir = os.getenv("AI_EXPORT_OUTPUT_DIR")

result = build_ai_review_export(
    package_dir,
    output_dir=Path(output_dir) if output_dir else None,
)

print(result.output_dir)
print(result.ai_review_path)
print(result.manifest_path)
```

CLI example:

```bash
procore-sdk ai-review-export --package-dir "$PACKAGE_DIR"
```

## Expected output

The output folder contains:

- `manifest.json`
- `ai_review.md`
- `ai_review.json`
- `prompt.md`
- `system_context.md`
- `source_index.json`
- `source_index.md`
- `chunks/`
- `checklists/`

## Common issues

- If the output folder already exists, use `--overwrite` only after confirming
  you do not need the old files.
- If no source files are included, confirm the package contains `.md`, `.json`,
  `.jsonl`, or `.txt` files.
- Attachments and binary downloads are intentionally excluded by default.
- The generated files are review assistance only, not final construction,
  approval, or legal decisions.
