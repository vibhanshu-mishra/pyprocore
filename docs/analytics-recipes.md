# Local Project Health Analytics

Phase 17D adds local project health analytics recipes for exported Procore
records. These helpers are deterministic, review-oriented, and designed for
teams that want a quick local signal before deeper project review.

## What This Does

The analytics recipes read local JSON, JSONL, or CSV files and produce JSON,
Markdown, or CSV summaries for:

- RFI aging and overdue risk
- Submittal delay and due-soon risk
- Change exposure by status and amount
- Daily Log completeness over a date range
- Combined project health scoring across available inputs

The scoring is heuristic. It is meant to highlight records worth reviewing, not
to guarantee project outcomes or replace professional judgment.

## Safety Boundaries

- No Procore API calls.
- No external AI/model calls.
- No MCP execution.
- No Procore tool execution.
- No create, update, delete, upload, approve, submit, payment, or write
  actions.
- No pandas, NumPy, scikit-learn, charting, database, dashboard, or web-server
  dependencies.
- No hosted dashboard is included.
- Input records are loaded only from local files or local Python objects.
- Obvious secret-like values are redacted from loaded records and reports.

## CLI Commands

```bash
procore-sdk analytics rfi-aging examples/analytics/fake_rfis.json --format markdown
procore-sdk analytics submittal-delay examples/analytics/fake_submittals.json --format json
procore-sdk analytics change-exposure examples/analytics/fake_changes.json --format markdown
procore-sdk analytics daily-log-completeness examples/analytics/fake_daily_logs.json --start-date 2026-06-01 --end-date 2026-06-05
procore-sdk analytics project-health \
  --rfis examples/analytics/fake_rfis.json \
  --submittals examples/analytics/fake_submittals.json \
  --changes examples/analytics/fake_changes.json \
  --daily-logs examples/analytics/fake_daily_logs.json \
  --start-date 2026-06-01 \
  --end-date 2026-06-05 \
  --format markdown
procore-sdk analytics sample-data --output-dir ./tmp/analytics-sample
```

## Python Example

```python
from pathlib import Path

from pyprocore.analytics import (
    analytics_result_to_markdown,
    run_project_health_recipe,
)

result = run_project_health_recipe(
    rfis_path=Path("examples/analytics/fake_rfis.json"),
    submittals_path=Path("examples/analytics/fake_submittals.json"),
    changes_path=Path("examples/analytics/fake_changes.json"),
    daily_logs_path=Path("examples/analytics/fake_daily_logs.json"),
    start_date="2026-06-01",
    end_date="2026-06-05",
)

print(analytics_result_to_markdown(result))
```

## Expected Output

Reports include:

- A project health score from `0` to `100`
- A label such as `healthy`, `watch`, `at_risk`, or `critical`
- Component summaries for the inputs provided
- Findings with severity, evidence, and suggested review actions
- Safety flags confirming no Procore calls, no external AI calls, and no write
  actions

## Input Notes

The recipes accept flexible record shapes because exported Procore payloads can
vary. Common fields such as `status`, `created_at`, `due_date`, `amount`,
`estimated_value`, `log_date`, and `date` are recognized where applicable.

If a field is missing, the recipe skips that part of the calculation instead of
failing aggressively. Missing inputs are reported in the combined project health
result so reviewers know which signals were not available.

## Examples

See examples `296` through `300` in the
[examples README](https://github.com/vibhanshu-mishra/pyprocore/blob/main/examples/README.md)
for standalone local scripts that use the fake analytics fixtures.
