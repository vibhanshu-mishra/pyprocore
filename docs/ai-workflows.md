# AI Workflows

PyProcore is model-agnostic. It prepares structured local data for construction
AI workflows, but it does not call external AI/model APIs by default. Users
choose their own model stack, review the data they want to share, and keep human
review in the loop.

The current published stable release remains `2.2.0`. Phase 8A through 8G,
Phase 9A through 9D, Phase 12, Phase 13A, Phase 13B, Phase 13C, and Phase 13D are
unreleased branch work unless a later release publishes them.

## What This Does

Phase 12 adds local examples, templates, and helper functions that show how
PyProcore outputs can support AI workflows. The helpers operate on local text,
local dictionaries, or placeholder/sample data. They can produce prompt text,
Markdown, JSON, JSONL-style chunks, and vector export manifests.

PyProcore does not:

- Call external AI/model APIs
- Require OpenAI, Anthropic, LangChain, LlamaIndex, Chroma, FAISS, or other AI dependencies
- Install or call a vector database
- Execute Procore tools through the agent layer
- Execute MCP tools
- Perform Procore write actions
- Approve, reject, submit, upload, update, delete, or change statuses

Tool execution remains disabled. MCP remains discovery-only.

## Safe Workflow Pattern

1. Export or read Procore data with existing read-only SDK workflows.
2. Build a local package such as an RFI package, submittal package, project context package, AI review export, or prompt pack.
3. Review and redact private project data if needed.
4. Send only selected files to the user's chosen AI/model system.
5. Keep human review in the loop before any project decision or Procore action.

## Supported Patterns

### RFI Review Assistant

Use a local RFI package and related context to summarize the question, identify
missing information, and draft follow-up questions for human review.

### Submittal Review Assistant

Use local submittal data and specification notes to prepare a review checklist,
scope summary, missing-item list, and human follow-up questions.

### Drawing/Spec Comparison Assistant

Use reviewed drawing notes and specification notes to flag possible conflicts,
revision mismatches, and missing references. These findings are review leads,
not confirmed design conclusions.

### Project Context Q&A Package

Use a local project context package for question answering. Ask the selected
model system to cite local filenames or section names and say when information
is missing.

### Vector DB/Chunk Export Pattern

Use local chunking helpers to prepare a JSON manifest that can be indexed in a
user-owned vector system. PyProcore does not install, host, or call a vector
database.

### Engineering Assistant Context Bundle

Prepare assumptions, known facts, missing inputs, relevant references, and
questions for a qualified reviewer. PyProcore does not perform engineering
calculations or certify design decisions.

### Field Issue Summarizer

Prepare notes from local observations, photos, daily logs, RFIs, or submittals
so a chosen model system can summarize timeline, affected areas, and open
questions.

### Change-Risk Review Package

Prepare local context around possible scope, schedule, cost, documentation, and
approval-chain risks. AI output is not contractual entitlement or approval.

## Local Helper Example

```python
from pyprocore.workflows import build_rfi_review_prompt_pack

prompt = build_rfi_review_prompt_pack(
    {"number": "RFI-PLACEHOLDER", "title": "Placeholder detail question"},
    context="Reviewed local context from a PyProcore export.",
)

print(prompt.user_prompt)
```

## Vector Manifest Example

```python
from pyprocore.workflows import build_vector_index_manifest

manifest = build_vector_index_manifest(
    "Reviewed local project context.",
    source_name="project-context.md",
)

print(manifest.model_dump(mode="json"))
```

## Safety Boundaries

- No external AI/model calls are made by PyProcore.
- No autonomous Procore actions are performed.
- No Procore write actions are added by Phase 12.
- No create/update/delete endpoints are introduced.
- No approvals, status changes, uploads, submissions, or mutations are performed.
- Tool execution remains disabled.
- MCP remains discovery-only.
- Private data should not be committed to source control.

The examples are intentionally local-only patterns. They show where users may
plug in their own model or vector stack after reviewing data, but PyProcore does
not select or call that stack.

Phase 13A through Phase 13D golden evals can validate local AI workflow package
structure, safety metadata, baselines, regression reports, and saved
model-response fixtures with deterministic checks. They do not call a model,
use model-as-judge grading, or grade live model responses.
