"""Run local PyProcore agent evals without Procore credentials.

This example checks the agent registry, schemas, OpenAPI export, MCP discovery
metadata, replay safety, redaction, and disabled execution behavior. It does
not call Procore and does not call any AI/model APIs.
"""

from __future__ import annotations

from pathlib import Path

from pyprocore.agent import (
    format_agent_eval_summary,
    run_all_agent_eval_suites,
    write_agent_eval_results,
)


def main() -> None:
    """Run all built-in agent eval suites and write a JSON report."""
    output_dir = Path("example-output/agent-evals")
    output_dir.mkdir(parents=True, exist_ok=True)

    results = run_all_agent_eval_suites()
    results_path = write_agent_eval_results(
        results,
        output_dir / "agent-eval-results.json",
        pretty=True,
    )
    summary_path = output_dir / "agent-eval-summary.md"
    summary_path.write_text(format_agent_eval_summary(results), encoding="utf-8")

    print("Agent evals completed locally.")
    print(f"Results: {results_path}")
    print(f"Summary: {summary_path}")
    print("No Procore credentials, live API calls, or AI API calls were used.")


if __name__ == "__main__":
    main()
