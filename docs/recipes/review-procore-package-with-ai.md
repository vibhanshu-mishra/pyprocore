# Review a Procore Package with AI

## What this does

Shows a safe local workflow for reviewing a PyProcore package with an AI tool.
PyProcore prepares the files, but it does not call an AI service or send your
data anywhere.

## When to use it

Use this when a human reviewer wants AI assistance summarizing an RFI,
submittal, or project context package while keeping the source material local
and traceable.

## Before you start

Build a local PyProcore package first, then create an AI review export.
Credentials and OAuth are only needed for the earlier Procore data collection
step, not for the local export step.

Useful environment variables:

- `PACKAGE_DIR`
- `AI_EXPORT_OUTPUT_DIR`

## Code

```python
import os
from pathlib import Path

from pyprocore.workflows import build_ai_review_export

result = build_ai_review_export(Path(os.environ["PACKAGE_DIR"]))

print("Attach these files to your AI review tool:")
print(result.system_context_path)
print(result.prompt_path)
print(result.ai_review_path)
print(result.source_index_md_path)
for chunk_path in result.chunk_paths:
    print(chunk_path)
```

## Expected output

You should see paths to the system context, prompt, review guide, source index,
and chunk files. Start an AI review session with `system_context.md`, then use
`prompt.md` and the chunk files as the review material.

## Common issues

- If an AI answer does not cite local files, ask it to revise the answer using
  only filenames and sections from the export.
- If the AI makes assumptions, ask it to separate confirmed facts from
  assumptions.
- If information is missing, use the generated checklist files to decide what to
  retrieve next.
- Do not use AI output as final approval, legal advice, or construction
  direction.
