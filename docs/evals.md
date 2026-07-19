# Golden Evals

Phase 13A adds the local deterministic golden dataset foundation. Phase 13B
adds workflow-specific golden eval suites for RFI, submittal, async export,
async batch, AI workflow, plugin metadata/config, and safety-boundary artifacts.

Current stable release: `2.2.0`. Phase 13A and Phase 13B are unreleased branch
work unless included in a later published release.

## What This Does

Golden evals check local JSON-like artifacts such as export rows, agent
manifest metadata, AI workflow package metadata, async batch plans, plugin
metadata, and safety-boundary snippets.

They are useful when you want a repeatable check that an export, manifest,
workflow package, or prompt package still has the expected structure before it
is used in automation or AI review.

## Safety Boundaries

Golden evals are local deterministic checks only.

- They do not call Procore.
- They do not call external AI/model APIs.
- They do not execute Procore tools.
- They do not execute MCP.
- They do not execute plugins.
- They do not fetch remote datasets.
- They do not upload datasets or reports.
- They do not require credentials.

Reports are local artifacts only when you explicitly write them.

## CLI

List built-in suites:

```bash
PYTHONPATH=. procore-sdk evals list
```

Run all built-in suites:

```bash
PYTHONPATH=. procore-sdk evals run
```

Run one suite:

```bash
PYTHONPATH=. procore-sdk evals run --suite rfi_workflow_golden
PYTHONPATH=. procore-sdk evals run --suite safety_boundaries_golden
```

Validate a local JSON dataset:

```bash
PYTHONPATH=. procore-sdk evals validate-dataset examples/golden_datasets/rfi_workflows/rfi_workflow_golden.json
```

Write a local report:

```bash
PYTHONPATH=. procore-sdk evals report --suite async_batch_golden --format markdown --output local-eval-report.md
```

## Python

```python
from pyprocore.evals import run_builtin_eval_suites

report = run_builtin_eval_suites(suite="rfi_workflow_golden")
print(report.passed)
print(f"{report.passed_cases}/{report.total_cases} cases passed")
```

## Built-In Dataset Types

- `export_rows`
- `agent_manifest`
- `agent_tool_schema`
- `ai_workflow_package`
- `rfi_workflow_package`
- `submittal_workflow_package`
- `async_export_manifest`
- `async_batch_plan`
- `async_batch_manifest`
- `plugin_manifest`
- `plugin_config`
- `extension_pack`
- `safety_boundary`
- `docs_truth_snippet`

## Workflow-Specific Suites

Phase 13B adds these built-in suites:

| Suite | Checks |
| --- | --- |
| `rfi_workflow_golden` | RFI export row fields, RFI package context, grounded prompt package language |
| `submittal_workflow_golden` | Submittal export row fields, review package context, human-review prompt boundaries |
| `async_export_golden` | CSV/JSONL row shape, export manifests, output path boundaries, redacted errors |
| `async_batch_golden` | Batch plan fields, dry-run manifests, partial failure summaries, output path boundaries |
| `ai_workflow_package_golden` | Prompt-package sections, grounding language, vector export manifest shape |
| `plugin_metadata_golden` | Metadata-only plugin manifests, allowed capabilities, hook metadata types |
| `plugin_config_golden` | JSON-only plugin preferences and extension-pack metadata |
| `safety_boundaries_golden` | Disabled tool/MCP/plugin/model/remote dataset execution boundaries |

## RFI Workflow Evals

RFI workflow evals validate placeholder export rows and local package artifacts.
They check fields such as number, title, status, responsible contractor,
assignee, due date, references, and grounding instructions. They do not create
answers or call a model.

## Submittal Workflow Evals

Submittal workflow evals validate export rows and review package artifacts.
They check fields such as title, number, status, due date, submitter, reviewer,
spec section, and ball-in-court. Prompt fixtures keep decisions human-reviewed.

## Async Export Evals

Async export evals validate CSV/JSONL-style rows and export manifests. They
check record counts, output paths, dry-run flags, warnings/errors, and secret
redaction boundaries.

## Async Batch Evals

Async batch evals validate local batch plans and manifests. They check
placeholder company/project IDs, resources, output folders, concurrency limits,
dry-run flags, partial failures, fail-safe structure, and resume-friendly
result shapes.

## AI Workflow Package Evals

AI workflow package evals validate local prompt packages, source/context
manifests, safety checklists, output expectations, vector-export metadata, and
grounding language such as “do not invent facts.” They do not call external
model APIs.

## Plugin Metadata and Config Evals

Plugin evals validate metadata-only manifests, allowed capabilities, hook
metadata, JSON config preferences, extension-pack metadata, and scaffold
fixtures. They do not install, fetch, load, or execute plugin code.

## Safety-Boundary Evals

Safety-boundary evals check fixture-level guarantees that agent tool execution,
MCP execution, plugin config execution, remote dataset fetching, external model
calls, and Procore write actions remain disabled.

## Reports

Reports include suite count, case count, pass/fail counts, warning count, score,
and per-case findings. JSON and Markdown rendering are supported.

Use Markdown for quick human review and JSON for CI artifacts:

```bash
PYTHONPATH=. procore-sdk evals report --suite plugin_metadata_golden --format json
```

## What Phase 13B Does Not Do

Phase 13B does not evaluate live Procore responses, live model responses, remote
datasets, plugin runtime behavior, or MCP tool execution. It evaluates local
deterministic artifacts only.
