# Run Agent Evals

## What This Does

This recipe runs PyProcore's local deterministic agent eval suites. The evals
check agent registry safety, schema quality, OpenAPI coverage, MCP discovery
metadata, run-log replay, redaction, and disabled execution behavior.

## When To Use It

Use this before changing agent-facing metadata, publishing docs for assistant
integrations, or sharing MCP/OpenAPI discovery files with another system.

## Before You Start

You do not need a `.env` file, OAuth token, company ID, project ID, or AI API
key. These evals use local metadata only and do not call Procore.

## Code

```python
from pathlib import Path

from pyprocore.agent import run_all_agent_eval_suites, write_agent_eval_results

results = run_all_agent_eval_suites()
output_path = write_agent_eval_results(
    results,
    Path("agent-eval-output/agent-eval-results.json"),
    pretty=True,
)

print(f"Wrote {output_path}")
```

You can also use the CLI:

```bash
procore-sdk agent evals list
procore-sdk agent evals run
procore-sdk agent evals run registry_safety
procore-sdk agent evals run --output agent-eval-output/agent-eval-results.json
```

Or use the helper script:

```bash
python3 scripts/run_agent_evals.py --output-dir agent-eval-output
```

## Expected Output

You should see a summary showing each suite, whether it passed, the number of
cases checked, and any warnings. A successful run exits with code `0`.

## Common Issues

- If `procore-sdk` is not found, install the package or run with `PYTHONPATH=.`
  from a local checkout.
- If a suite fails after changing registry metadata, inspect the JSON output to
  see the exact case and finding.
- These evals do not prove live Procore access. They only validate local
  agent-facing metadata and safety guarantees.
