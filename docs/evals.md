# Golden Evals

Phase 13A adds local deterministic golden datasets and eval reports for
PyProcore artifacts.

Current stable release: `2.2.0`. Phase 13A is unreleased branch work unless it
is included in a later published release.

## What This Does

Golden evals check local JSON-like artifacts such as export rows, agent
manifest metadata, AI workflow package metadata, async batch plans, plugin
metadata, and safety-boundary snippets.

They are useful when you want a repeatable check that an export, manifest, or
workflow package still has the expected structure.

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
PYTHONPATH=. procore-sdk evals run --suite golden_export_rows_basic
```

Validate a local JSON dataset:

```bash
PYTHONPATH=. procore-sdk evals validate-dataset examples/golden_datasets/golden_export_rows_basic.json
```

Write a local report:

```bash
PYTHONPATH=. procore-sdk evals report --format markdown --output local-eval-report.md
```

## Python

```python
from pyprocore.evals import run_builtin_eval_suites

report = run_builtin_eval_suites()
print(report.passed)
print(f"{report.passed_cases}/{report.total_cases} cases passed")
```

## Built-In Dataset Types

- `export_rows`
- `agent_manifest`
- `agent_tool_schema`
- `ai_workflow_package`
- `async_batch_plan`
- `async_batch_manifest`
- `plugin_manifest`
- `plugin_config`
- `extension_pack`
- `safety_boundary`
- `docs_truth_snippet`

## Reports

Reports include suite count, case count, pass/fail counts, warning count, score,
and per-case findings. JSON and Markdown rendering are supported.

Future Phase 13 slices may add patterns for evaluating saved model responses,
but Phase 13A does not call live models.
