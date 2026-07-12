"""Run PyProcore agent evals locally without Procore or AI API access."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pyprocore.agent import (
    AgentEvalResult,
    export_agent_eval_results_json,
    format_agent_eval_summary,
    run_agent_eval_suite,
    run_all_agent_eval_suites,
    write_agent_eval_results,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the local agent eval runner parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Run deterministic PyProcore agent evals locally. "
            "No Procore credentials, live API calls, or AI model calls are used."
        )
    )
    parser.add_argument(
        "--suite",
        default=None,
        help="Optional suite name. When omitted, all built-in suites run.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("agent-eval-output"),
        help="Directory where eval JSON and Markdown summaries should be written.",
    )
    parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Print JSON results to stdout.",
    )
    parser.add_argument(
        "--fail-on-warning",
        action="store_true",
        help="Exit nonzero when warnings are present.",
    )
    return parser


def main() -> int:
    """Run local agent evals, write reports, and return an exit code."""
    args = build_parser().parse_args()
    results: AgentEvalResult | list[AgentEvalResult]
    results = run_agent_eval_suite(args.suite) if args.suite else run_all_agent_eval_suites()

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    results_path = write_agent_eval_results(
        results,
        output_dir / "agent-eval-results.json",
        pretty=True,
    )
    summary_path = output_dir / "agent-eval-summary.md"
    summary_path.write_text(format_agent_eval_summary(results), encoding="utf-8")

    if args.json_output:
        print(export_agent_eval_results_json(results, pretty=True))
    else:
        print("PyProcore agent evals complete.")
        print(f"Results: {results_path}")
        print(f"Summary: {summary_path}")
        print("Mode: local deterministic checks only; no Procore or AI calls.")

    active_results = [results] if isinstance(results, AgentEvalResult) else results
    has_failure = any(not result.passed for result in active_results)
    has_warning = any(result.warnings > 0 for result in active_results)
    return 1 if has_failure or (args.fail_on_warning and has_warning) else 0


if __name__ == "__main__":
    raise SystemExit(main())
