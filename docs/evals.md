# Golden Evals

Phase 13A adds the local deterministic golden dataset foundation. Phase 13B
adds workflow-specific golden eval suites for RFI, submittal, async export,
async batch, AI workflow, plugin metadata/config, and safety-boundary artifacts.
Phase 13C adds local baseline files, regression comparison, threshold policies,
and history snapshots for those deterministic eval suites. Phase 13D adds
offline model-response fixture evals for saved/sample AI-style responses.

Current stable release: `2.2.0`. Phase 13A, Phase 13B, Phase 13C, and Phase
13D are unreleased branch work unless included in a later published release.

## What This Does

Golden evals check local JSON-like artifacts such as export rows, agent
manifest metadata, AI workflow package metadata, async batch plans, plugin
metadata, safety-boundary snippets, and saved offline model-response fixtures.

They are useful when you want a repeatable check that an export, manifest,
workflow package, or prompt package still has the expected structure before it
is used in automation or AI review.

## Safety Boundaries

Golden evals are local deterministic checks only.

- They do not call Procore.
- They do not call external AI/model APIs.
- They do not use model-as-judge scoring.
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
PYTHONPATH=. procore-sdk evals run --suite model_fixture_rfi_review_golden
PYTHONPATH=. procore-sdk evals run --suite model_fixture_safety_boundaries_golden
```

Work with one offline model-response fixture:

```bash
PYTHONPATH=. procore-sdk evals model-fixture sample
PYTHONPATH=. procore-sdk evals model-fixture validate examples/model_response_fixtures/rfi_review/passing_response.json
PYTHONPATH=. procore-sdk evals model-fixture score examples/model_response_fixtures/rfi_review/passing_response.json
PYTHONPATH=. procore-sdk evals model-fixture policy
```

Validate a local JSON dataset:

```bash
PYTHONPATH=. procore-sdk evals validate-dataset examples/golden_datasets/rfi_workflows/rfi_workflow_golden.json
```

Write a local report:

```bash
PYTHONPATH=. procore-sdk evals report --suite async_batch_golden --format markdown --output local-eval-report.md
```

Print a sample baseline:

```bash
PYTHONPATH=. procore-sdk evals baseline sample
```

Create a local baseline:

```bash
PYTHONPATH=. procore-sdk evals baseline create --output local-eval-baseline.json
```

Validate a baseline:

```bash
PYTHONPATH=. procore-sdk evals baseline validate local-eval-baseline.json
```

Compare current evals to a baseline:

```bash
PYTHONPATH=. procore-sdk evals compare --baseline local-eval-baseline.json
PYTHONPATH=. procore-sdk evals compare --baseline local-eval-baseline.json --suite rfi_workflow_golden
```

Build regression reports:

```bash
PYTHONPATH=. procore-sdk evals regression-report --baseline local-eval-baseline.json --format json
PYTHONPATH=. procore-sdk evals regression-report --baseline local-eval-baseline.json --format markdown
```

Create local history snapshots:

```bash
PYTHONPATH=. procore-sdk evals history sample
PYTHONPATH=. procore-sdk evals history append --output local-eval-history.json
PYTHONPATH=. procore-sdk evals history summary local-eval-history.json
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
- `model_response_fixture`

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

## Offline Model-Response Fixture Evals

Phase 13D evaluates static local text/JSON fixtures that represent saved or
sample AI-style responses. It does not generate responses, call OpenAI,
Anthropic, Gemini, local model servers, Procore, plugins, MCP, or tools.

Fixture checks are deterministic and include:

- required sections and required phrases
- forbidden phrases and forbidden claims
- allowed citation/source-label checks
- fake citation and hallucinated source-label detection
- grounding statement checks
- prohibited approval/write-action language checks
- fake confidence checks
- limitation/refusal disclosure checks
- secret-like value checks
- external model/API call claim checks
- live Procore verification claim checks

PyProcore does not use model-as-judge scoring. Unsafe demonstration fixtures can
still pass a suite when the expected result is that unsafe text was correctly
detected.

Built-in Phase 13D suites:

| Suite | Checks |
| --- | --- |
| `model_fixture_rfi_review_golden` | Saved RFI review responses and unsafe write/approval wording |
| `model_fixture_submittal_review_golden` | Saved submittal review responses and approval boundaries |
| `model_fixture_project_context_qa_golden` | Project-context Q&A source labels and grounding |
| `model_fixture_drawing_spec_comparison_golden` | Drawing/spec comparison citations and limitations |
| `model_fixture_engineering_assistant_golden` | Advisory engineering assistant response boundaries |
| `model_fixture_field_issue_summary_golden` | Field issue summary grounding and limitations |
| `model_fixture_change_risk_review_golden` | Change-risk review caution and source use |
| `model_fixture_safety_boundaries_golden` | Fake citation, live-call, and external-model claim detection |

Sample fixtures live in `examples/model_response_fixtures/`. They use
placeholder labels only and contain no real Procore IDs, tokens, users,
companies, projects, emails, Authorization headers, or API keys.

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

## Baselines

Baselines are local JSON snapshots of deterministic eval reports. They store
suite names, case IDs, statuses, scores, warning counts, failure counts, and
sanitized finding messages. They do not store credentials, Authorization
headers, real Procore IDs, or live response payloads.

Use a baseline when you want to compare today’s local eval run against a
known-good result:

```python
from pyprocore.evals import build_eval_baseline, run_builtin_eval_suites

report = run_builtin_eval_suites()
baseline = build_eval_baseline(report, baseline_name="release-check")
```

## Regression Comparison

Regression comparison checks current deterministic eval results against a local
baseline. It can detect:

- missing suites
- missing cases
- pass-to-fail changes
- pass-to-warning changes
- suite and case score drops
- max score changes
- new suites or cases
- increased failures or warnings

Unknown new suites are informational or warning-level findings depending on the
threshold policy. They are not treated as live API verification.

## Threshold Policies

Threshold policies are local rules applied after comparison. The default policy
is conservative: missing baseline suites/cases, score drops, and new failures
fail the comparison. Strict policy is useful before release-candidate checks
because it can require a perfect score ratio and disallow new warnings.

```python
from pyprocore.evals import (
    build_eval_baseline,
    compare_eval_report_to_baseline,
    run_builtin_eval_suites,
    strict_eval_threshold_policy,
)

report = run_builtin_eval_suites()
baseline = build_eval_baseline(report)
result = compare_eval_report_to_baseline(
    report,
    baseline,
    policy=strict_eval_threshold_policy(),
)
```

## Local History Snapshots

History snapshots are optional local JSON records of eval summary scores over
time. They are useful for release notes, local quality reports, and comparing
recent branch runs. PyProcore only writes history when you pass an explicit
local output path.

```bash
PYTHONPATH=. procore-sdk evals history append --output local-eval-history.json --label pre-release
PYTHONPATH=. procore-sdk evals history summary local-eval-history.json
```

## Sample Artifacts

Static sample files live in:

- `examples/eval_baselines/sample_eval_baseline.json`
- `examples/eval_reports/sample_regression_report.json`
- `examples/eval_reports/sample_regression_report.md`
- `examples/eval_reports/sample_eval_history.json`

These samples use placeholder local metadata only.

## Before a Release

For a local release-readiness pattern:

1. Run `PYTHONPATH=. procore-sdk evals run`.
2. Create or update a local baseline with `procore-sdk evals baseline create`.
3. Compare current results with `procore-sdk evals compare --baseline ...`.
4. Save JSON or Markdown regression reports for local review.
5. Keep generated reports/history files out of commits unless they are curated
   examples.

Phase 13C does not modify GitHub Actions. Teams can wire the commands into CI
later if they choose.

Phase 13D also leaves GitHub Actions unchanged. It adds local fixture suites and
CLI helpers only.

## What Phase 13C Does Not Do

Phase 13C does not evaluate live Procore responses, live model responses,
remote datasets, plugin runtime behavior, or MCP tool execution. It does not
fetch remote baselines, upload reports, execute plugins, call external models,
call Procore, or enable tool execution. It compares local deterministic eval
results only.

Phase 13D does not call model providers, use model-as-judge grading, fetch
remote fixture data, upload reports, execute plugins, execute MCP, execute
Procore tools, or verify anything against live Procore. It scores saved local
fixtures only.

Phase 15A, Phase 15B, and Phase 15C expose eval suite, per-suite,
sample-report, baseline-template, regression-template, history-template,
model-fixture, safety-boundary, contract, snapshot, and compatibility metadata
through discovery-only MCP resources. Reading these resources does not run
evals, call Procore, call models, fetch remote datasets, upload reports, or
enable MCP execution.
