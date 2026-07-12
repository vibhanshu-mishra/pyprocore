"""Show how to replay a local Agent API run log.

This example does not call Procore and does not execute tools. It prints the
CLI command shape for replaying a run created by the local Agent API server.
"""

from __future__ import annotations

import os


def main() -> None:
    """Print a safe replay command for a local run."""
    run_log_dir = os.getenv("PYPROCORE_AGENT_RUN_LOG_DIR", "agent-runs")
    run_id = os.getenv("PYPROCORE_AGENT_RUN_ID", "your-run-id")

    print("Replay verifies local Agent API activity without executing tools.")
    print("")
    print("Replay a saved run:")
    print(f"PYTHONPATH=. procore-sdk agent runs replay {run_id} --run-log-dir {run_log_dir}")
    print("")
    print("Use `procore-sdk agent runs list --run-log-dir agent-runs` to find run IDs.")


if __name__ == "__main__":
    main()
