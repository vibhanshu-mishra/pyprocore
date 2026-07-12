"""Inspect local PyProcore agent eval results.

Set AGENT_EVAL_RESULTS_PATH to inspect a previous JSON report. If the report
does not exist yet, this example runs the local evals first so beginners have a
safe file to inspect.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from pyprocore.agent import (
    AgentEvalResult,
    format_agent_eval_summary,
    run_all_agent_eval_suites,
    write_agent_eval_results,
)


def main() -> None:
    """Load or create an agent eval report and print a concise summary."""
    results_path = Path(
        os.getenv(
            "AGENT_EVAL_RESULTS_PATH",
            "example-output/agent-evals/agent-eval-results.json",
        )
    )

    if not results_path.exists():
        print("No eval results file found yet. Running local evals first.")
        results = run_all_agent_eval_suites()
        write_agent_eval_results(results, results_path, pretty=True)
    else:
        payload = json.loads(results_path.read_text(encoding="utf-8"))
        results = [AgentEvalResult.model_validate(item) for item in payload]

    print(format_agent_eval_summary(results))
    print(f"Inspected: {results_path}")
    print("No Procore credentials, live API calls, or AI API calls were used.")


if __name__ == "__main__":
    main()
