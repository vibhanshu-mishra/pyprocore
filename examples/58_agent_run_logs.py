"""Show how to enable local Agent API run logs.

This example does not start a server and does not call Procore. It prints safe
commands for opting in to local run logging while using the discovery-only Agent
API server.
"""

from __future__ import annotations


def main() -> None:
    """Print safe local run-log commands."""
    print("Agent API run logging is opt-in and local-only.")
    print("")
    print("Start the discovery server with run logging enabled:")
    print("PYTHONPATH=. procore-sdk agent serve --run-log-dir agent-runs")
    print("")
    print("Then inspect local runs:")
    print("PYTHONPATH=. procore-sdk agent runs list --run-log-dir agent-runs")
    print("")
    print("Tool execution remains disabled. No Procore credentials are required.")


if __name__ == "__main__":
    main()
