# Inspect Agent Eval Results

## What This Does

This recipe shows how to read a saved agent eval JSON report and summarize the
suite results in Python.

## When To Use It

Use this when you want to review eval output from a local run, CI artifact, or
shared report without rerunning the evals.

## Before You Start

You need a local eval results JSON file. You can create one with:

```bash
procore-sdk agent evals run --output agent-eval-output/agent-eval-results.json
```

No `.env`, OAuth token, Procore access, or AI API key is required.

## Code

```python
import json
from pathlib import Path

from pyprocore.agent import AgentEvalResult, format_agent_eval_summary

results_path = Path("agent-eval-output/agent-eval-results.json")
payload = json.loads(results_path.read_text(encoding="utf-8"))
results = [AgentEvalResult.model_validate(item) for item in payload]

print(format_agent_eval_summary(results))
```

## Expected Output

You should see a Markdown-style table with suite pass/fail status, case counts,
and warning counts.

## Common Issues

- If the file does not exist yet, run `procore-sdk agent evals run --output ...`
  first.
- If JSON parsing fails, make sure the file came from
  `write_agent_eval_results()` or `procore-sdk agent evals run --output`.
- If a suite failed, inspect each result's `findings` list for the exact case
  and beginner-friendly message.
