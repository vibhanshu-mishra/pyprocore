# Build an AI Prompt Pack

## What this does

Builds a prompt-focused local folder from an existing PyProcore package. It
creates prompt and system-context files, a source index, chunks, and checklists
without writing the optional JSON review export.

## When to use it

Use this when you already have a local package and want a compact set of files
to guide an AI review session.

## Before you start

Create a local package folder first. This recipe does not call Procore and does
not require credentials while it runs.

Useful environment variables:

- `PACKAGE_DIR`
- `AI_PROMPT_PACK_OUTPUT_DIR`
- `AI_REVIEW_TYPE`

## Code

```python
import os
from pathlib import Path

from pyprocore.workflows import build_ai_prompt_pack

package_dir = Path(os.environ["PACKAGE_DIR"])
output_dir = os.getenv("AI_PROMPT_PACK_OUTPUT_DIR")

result = build_ai_prompt_pack(
    package_dir,
    output_dir=Path(output_dir) if output_dir else None,
    review_type=os.getenv("AI_REVIEW_TYPE", "general"),
)

print(result.output_dir)
print(result.prompt_path)
print(result.system_context_path)
```

CLI example:

```bash
procore-sdk ai-prompt-pack --package-dir "$PACKAGE_DIR" --review-type general
```

## Expected output

The output folder contains prompt-focused files:

- `manifest.json`
- `ai_review.md`
- `prompt.md`
- `system_context.md`
- `source_index.json`
- `source_index.md`
- `chunks/`
- `checklists/`

## Common issues

- If the output folder already exists, pass `--overwrite` only when replacing it
  is intentional.
- If a source file is missing from the prompt pack, check `source_index.md` for
  the exclusion reason.
- Keep the prompt and system-context instructions with the source files so AI
  tools know to cite local files and avoid invented facts.
